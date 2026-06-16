from flask import Flask, render_template, request, redirect, flash, url_for
from models import db, User, Recipe, RecipeIngredient, PantryItem
from api_helper import search_recipes, get_recipe_by_id, get_random_recipe, get_ingredients, get_categories, get_areas, filter_by_category, filter_by_area
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LoginForm, RegisterForm, CustomRecipeForm, AddPantryItemForm, DeletePantryItemForm

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

# Pantry functionalities
@app.route("/pantry")
@login_required
def pantry():
    pantry_items = PantryItem.query.filter_by(owner=current_user).all()
    deleteForm = DeletePantryItemForm()
    return render_template("pantry.html", active_page="pantry", pantry_items=pantry_items, form=deleteForm)

@app.route("/add_pantry_item", methods=['GET', 'POST'])
@login_required
def add_pantry_item():
    form = AddPantryItemForm()
    if form.validate_on_submit():
        new_pantry_item = PantryItem(
            name=form.name.data, 
            quantity=form.quantity.data,
            category=form.category.data,
            unit=form.unit.data, 
            expiry_date = form.expiry_date.data,
            owner=current_user)
        try:
            db.session.add(new_pantry_item)
            db.session.commit()
            # flash('Pantry item added successfully.')
            return redirect(url_for('pantry'))  # redirect after success
        except Exception:
            db.session.rollback()
            # flash('Something went wrong adding the pantry item. Please try again.', 'error')
    else:
        print("FORM ERRORS:", form.errors)
    return render_template("add_pantry_item.html", form=form, active_page="pantry")

@app.route("/pantry/delete/<int:item_id>", methods=["POST"])
def delete_pantry_item(item_id):
    item = PantryItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("pantry"))

@app.route("/pantry/edit/<int:item_id>", methods=["GET", "POST"])
def edit_pantry_item(item_id):
    item = PantryItem.query.get_or_404(item_id)
    form = AddPantryItemForm(obj=item)

    if form.validate_on_submit():
        item.name = form.name.data
        item.quantity = form.quantity.data
        item.unit = form.unit.data
        item.expiry_date = form.expiry_date.data
        db.session.commit()
        return redirect(url_for('pantry'))
    return render_template('edit_pantry_item.html', form=form, item=item, active_page="pantry")

@app.route("/recipes")
@login_required
def recipes():
    # which tab is active, default to saved
    active_tab = request.args.get("tab", "saved")

    # variables used by different tabs
    api_results = []
    saved_recipes = []
    community_recipes = []
    custom_recipes = []
    search_query = ""
    selected_category = ""
    selected_area = ""
    error_message = ""
    categories = []
    areas = []

    if active_tab == "search":
        # pantry recipe library tab - search the api
        search_query = request.args.get("q", "").strip()
        selected_category = request.args.get("category", "").strip()
        selected_area = request.args.get("area", "").strip()

        categories = get_categories()
        areas = get_areas()

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
        # all recipes this user has saved
        saved_recipes = Recipe.query.filter_by(user_id=current_user.id).all()

    elif active_tab == "community":
        # custom recipes submitted by other users
        community_search = request.args.get("q", "").strip()
        search_query = community_search

        query = Recipe.query.filter(
            Recipe.source == "Custom",
            Recipe.user_id != current_user.id
        )

        if community_search:
            query = query.filter(Recipe.name.ilike(f"%{community_search}%"))

        community_recipes = query.all()

    elif active_tab == "custom":
        # recipes the current user created themselves
        custom_recipes = Recipe.query.filter_by(
            user_id=current_user.id,
            source="Custom"
        ).all()

    return render_template(
        "recipes.html",
        active_page="recipes",
        active_tab=active_tab,
        api_results=api_results,
        saved_recipes=saved_recipes,
        community_recipes=community_recipes,
        custom_recipes=custom_recipes,
        search_query=search_query,
        selected_category=selected_category,
        selected_area=selected_area,
        error_message=error_message,
        categories=categories,
        areas=areas
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

    return render_template(
        "recipe_detail.html",
        active_page="recipes",
        meal=meal,
        ingredients=ingredients,
        is_saved=is_saved
    )


@app.route("/recipe/save/<meal_id>", methods=["POST"])
@login_required
def save_recipe(meal_id):
    # check if the user already saved this recipe
    existing = Recipe.query.filter_by(user_id=current_user.id, mealdb_id=meal_id).first()

    if existing:
        flash("recipe already saved")
        return redirect(url_for("recipe_detail", meal_id=meal_id))

    meal = get_recipe_by_id(meal_id)

    if meal is None:
        flash("could not find that recipe")
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
    flash("recipe saved!")
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
        flash("recipe created!")
        return redirect(url_for("recipes", tab="custom"))

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
