from flask import Flask, render_template, request, redirect, flash, url_for
from models import db, User, Recipe, RecipeIngredient, PantryItem
from api_helper import search_recipes, get_recipe_by_id, get_random_recipe, get_ingredients, get_categories, get_areas, filter_by_category, filter_by_area
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LoginForm, RegisterForm,CustomRecipeForm, AddPantryItemForm, EditRecipeForm

# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================
# DB Debug
database_debug = True




# Create the Flask application instance.
# __name__ tells Flask where to look for templates/ and static/ folders.
app = Flask(__name__)

# Configures the SQLite database location
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pantry.db"

# Disable modification tracking for better performance
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = 'thisisasecretkey'

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

# Connects SQLAlchemy to the Flask application instance
db.init_app(app)

# Create database tables if they do not exist
with app.app_context():
    db.create_all()

    if database_debug:
        print("\n=== DATABASE TABLES ===")
        for table in db.metadata.tables.keys():
            print(f"✅ {table}")
        print("=======================\n")

# ============================================================================
# ROUTES
# ============================================================================

# create a Login Manager Object, stored to login_manager variable, and initialize it with the Flask app.
login_manager = LoginManager()
login_manager.init_app(app)
# Tell the login_manager the name of the view function that handles logins, so it can redirect users there when they need to log in.
login_manager.login_view = 'login'
    

# Tell the login_manager how to load a user from the database, given the user's id.
# It does this automatically for every request where a session cookie exists, and sets the result to current_user
# Makes it available as current_user in all our routes and templates.
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

    
# Each route below maps a URL to a function that returns a page.
# render_template() finds the named file in templates/ and renders it,
# passing in any variables we want available inside the Jinja2 template.

@app.route("/", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('kitchen'))
        flash('Invalid email or password.', 'error')
    
    return render_template("login.html", form=form)


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(first_name=form.first_name.data, last_name=form.last_name.data, email=form.email.data, password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully. Please log in.')
            return redirect(url_for('login'))
        except Exception:
            db.session.rollback()
            flash('Something went wrong creating your account. Please try again.', 'error')
    
    return render_template("register.html", form=form)


# @app.route("/register_success")
# def register_success():
#     return render_template("register_success.html")


@app.route("/kitchen")
@login_required
def kitchen():
    return render_template("kitchen.html", active_page="kitchen")


@app.route("/pantry")
@login_required
def pantry():
    pantry_items = PantryItem.query.filter_by(owner=current_user).all()
    return render_template("pantry.html", active_page="pantry", pantry_items=pantry_items)

@app.route("/add_pantry_item", methods=['GET', 'POST'])
@login_required
def add_pantry_item():
    form = AddPantryItemForm()
    if form.validate_on_submit():
        new_pantry_item = PantryItem(name=form.name.data, quantity=form.quantity.data, unit=form.unit.data, expiry_date = form.expiry_date.data ,owner=current_user)
        try:
            db.session.add(new_pantry_item)
            db.session.commit()
            # flash('Pantry item added successfully.')
            return redirect(url_for('pantry'))  # redirect after success
        except Exception:
            db.session.rollback()
            # flash('Something went wrong adding the pantry item. Please try again.', 'error')
    return render_template("add_pantry_item.html", form=form, active_page="pantry")

@app.route("/recipes")
@login_required
def recipes():
    active_tab = request.args.get("tab", "saved")

    api_results = []
    saved_recipes = []
    created_recipes = []
    search_query = ""
    selected_category = ""
    selected_area = ""
    error_message = ""

    # variables for saved tab filters and sorting
    saved_sort = "newest"
    saved_filter_category = ""
    saved_categories = []

    if active_tab == "search":
        search_query = request.args.get("q", "").strip()
        selected_category = request.args.get("category", "").strip()
        selected_area = request.args.get("area", "").strip()

        if search_query:
            api_results = search_recipes(search_query)
            if len(api_results) == 0:
                error_message = f"no recipes found for '{search_query}', try something else"

        elif selected_category:
            api_results = filter_by_category(selected_category)
            if len(api_results) == 0:
                error_message = f"no recipes found in '{selected_category}'"

        elif selected_area:
            api_results = filter_by_area(selected_area)
            if len(api_results) == 0:
                error_message = f"no recipes found for '{selected_area}' cuisine"

    elif active_tab == "saved":
        saved_sort = request.args.get("sort", "newest")
        saved_filter_category = request.args.get("filter_category", "").strip()

        query = Recipe.query.filter_by(user_id=current_user.id)

        if saved_filter_category:
            query = query.filter(Recipe.category == saved_filter_category)

        if saved_sort == "name_az":
            query = query.order_by(Recipe.name.asc())
        elif saved_sort == "name_za":
            query = query.order_by(Recipe.name.desc())
        elif saved_sort == "oldest":
            query = query.order_by(Recipe.id.asc())
        else:
            query = query.order_by(Recipe.id.desc())

        saved_recipes = query.all()

        # get up to 5 unique categories from saved recipes for the filter dropdown
        all_saved = Recipe.query.filter_by(user_id=current_user.id).all()
        seen = []
        for r in all_saved:
            if r.category and r.category not in seen:
                seen.append(r.category)
            if len(seen) == 5:
                break
        saved_categories = seen

    elif active_tab == "created":
        # all custom recipes - current user's and other users' combined
        created_recipes = Recipe.query.filter_by(source="Custom").order_by(Recipe.id.desc()).all()

    return render_template(
        "recipes.html",
        active_page="recipes",
        active_tab=active_tab,
        api_results=api_results,
        saved_recipes=saved_recipes,
        created_recipes=created_recipes,
        search_query=search_query,
        selected_category=selected_category,
        selected_area=selected_area,
        error_message=error_message,
        saved_sort=saved_sort,
        saved_filter_category=saved_filter_category,
        saved_categories=saved_categories
    )


@app.route("/recipe/random")
@login_required
def recipe_random():
    meal = get_random_recipe()

    if meal is None:
        return render_template("not_found.html", active_page="recipes"), 404

    return redirect(url_for("recipe_detail", meal_id=meal["idMeal"]))


@app.route("/recipe/<meal_id>")
def recipe_detail(meal_id):
    meal = get_recipe_by_id(meal_id)

    # show not found page if the recipe doesnt exist
    if meal is None:
        return render_template("not_found.html", active_page="recipes"), 404

    ingredients = get_ingredients(meal)

    # check if the user has already saved this recipe
    is_saved = Recipe.query.filter_by(
        user_id=current_user.id,
        mealdb_id=meal_id
    ).first() is not None

    # check if the user has already saved this recipe
    is_saved = Recipe.query.filter_by(
        user_id=current_user.id,
        mealdb_id=meal_id
    ).first() is not None

    return render_template(
        "recipe_detail.html",
        active_page="recipes",
        meal=meal,
        ingredients=ingredients,
        is_saved=is_saved
        ingredients=ingredients,
        is_saved=is_saved
    )


@app.route("/recipe/save/<meal_id>", methods=["POST"])
@login_required
def save_recipe(meal_id):
    # check if the user already saved this recipe
    existing = Recipe.query.filter_by(user_id=current_user.id, mealdb_id=meal_id).first()

    if existing:
        return redirect(url_for("recipe_detail", meal_id=meal_id))

    meal = get_recipe_by_id(meal_id)

    if meal is None:
        return redirect(url_for("recipes"))

    new_recipe = Recipe(
        mealdb_id=meal["idMeal"],
        name=meal["strMeal"],
        category=meal.get("strCategory", ""),
        area=meal.get("strArea", ""),
        instructions=meal.get("strInstructions", ""),
        image_url=meal.get("strMealThumb", ""),
        youtube_url=meal.get("strYoutube", ""),
        source="TheMealDB",
        user_id=current_user.id
    )
    db.session.add(new_recipe)
    db.session.flush()

    # save the ingredients linked to this recipe
    for item in get_ingredients(meal):
        ingredient = RecipeIngredient(
            name=item["name"],
            amount=item["amount"],
            recipe_id=new_recipe.id
        )
        db.session.add(ingredient)

    db.session.commit()
    return redirect(url_for("recipe_detail", meal_id=meal_id))


@app.route("/recipes/saved/<int:recipe_id>")
@login_required
def saved_recipe_detail(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    return render_template(
        "saved_recipe_detail.html",
        active_page="recipes",
        recipe=recipe
    )


@app.route("/recipes/saved/<int:recipe_id>/edit", methods=["GET", "POST"])
@login_required
def edit_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    form = EditRecipeForm()

    if form.validate_on_submit():
        recipe.name = form.name.data
        recipe.category = form.category.data
        recipe.area = form.area.data
        recipe.instructions = form.instructions.data
        recipe.image_url = form.image_url.data

        # delete old ingredients and replace with updated ones
        RecipeIngredient.query.filter_by(recipe_id=recipe.id).delete()

        raw_lines = form.ingredients.data.strip().split("\n")
        for line in raw_lines:
            line = line.strip()
            if not line:
                continue
            if "," in line:
                parts = line.split(",", 1)
                amount = parts[0].strip()
                name = parts[1].strip()
            else:
                amount = ""
                name = line
            if name:
                db.session.add(RecipeIngredient(
                    name=name,
                    amount=amount,
                    recipe_id=recipe.id
                ))

        db.session.commit()
        return redirect(url_for("saved_recipe_detail", recipe_id=recipe.id))

    # pre-populate form on GET
    form.name.data = recipe.name
    form.category.data = recipe.category or ""
    form.area.data = recipe.area or ""
    form.instructions.data = recipe.instructions or ""
    form.image_url.data = recipe.image_url or ""
    form.ingredients.data = "\n".join([
        f"{i.amount}, {i.name}" if i.amount else i.name
        for i in recipe.ingredients
    ])

    return render_template("edit_recipe.html", active_page="recipes", form=form, recipe=recipe)


@app.route("/recipes/create", methods=["GET", "POST"])
@login_required
def create_recipe():
    form = CustomRecipeForm()

    if form.validate_on_submit():
        new_recipe = Recipe(
            name=form.name.data,
            category=form.category.data,
            area=form.area.data,
            instructions=form.instructions.data,
            source="Custom",
            user_id=current_user.id
        )
        db.session.add(new_recipe)
        db.session.flush()

        # parse ingredients - each line is "amount, name" or just "name"
        raw_lines = form.ingredients.data.strip().split("\n")
        for line in raw_lines:
            line = line.strip()
            if not line:
                continue

            if "," in line:
                parts = line.split(",", 1)
                amount = parts[0].strip()
                name = parts[1].strip()
            else:
                amount = ""
                name = line

            if name:
                ingredient = RecipeIngredient(
                    name=name,
                    amount=amount,
                    recipe_id=new_recipe.id
                )
                db.session.add(ingredient)

        db.session.commit()
        return redirect(url_for("recipes", tab="created"))

    return render_template("create_recipe.html", active_page="recipes", form=form)


@app.route("/suggestions")
@login_required
def suggestions():
    return render_template("suggestions.html", active_page="suggestions")


@app.route("/planned")
@login_required
def planned():
    return render_template("planned.html", active_page="planned")


@app.route("/cooked")
@login_required
def cooked():
    return render_template("cooked.html", active_page="cooked")


@app.route("/shopping")
@login_required
def shopping():
    return render_template("shopping.html", active_page="shopping")


@app.route("/orders")
@login_required
def orders():
    return render_template("orders.html", active_page="orders")

# ============================================================================
# MAIN
# ============================================================================
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == "__main__":
    # debug=True auto-reloads the server when you save a file
    # and shows helpful error pages. Turn off for production.
    app.run(debug=True)
