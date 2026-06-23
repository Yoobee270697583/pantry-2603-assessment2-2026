from flask import Flask, request, render_template, redirect, flash, url_for
from datetime import date, datetime
from models import User, Recipe, MealPlan, RecipeIngredient, PantryItem, db, Ingredient, CookedMeal
from constants import PANTRY_CATEGORY_CHOICES, CATEGORY_LABELS
from api_helper import search_recipes, get_recipe_by_id, get_random_recipe, get_ingredients, filter_by_category, filter_by_area, fetch_ingredient_list, get_or_create_recipe
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LoginForm, RegisterForm,CustomRecipeForm, AddPantryItemForm, EditRecipeForm, DeletePantryItemForm

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

    # one-time sync of the canonical ingredient list from TheMealDB so that
    # pantry items can be validated against our own table instead of the
    # live api on every request
    if Ingredient.query.count() == 0:
        for ing in fetch_ingredient_list():
            db.session.add(Ingredient(
                mealdb_id=ing.get("idIngredient"),
                name=ing["strIngredient"],
                image_url=ing.get("image_url")
            ))
        db.session.commit()

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
        except Exception:
            db.session.rollback()
            flash('Something went wrong creating your account. Please try again.', 'error')
            return render_template("register.html", form=form)
        
        flash('Account created! ✅ Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template("register.html", form=form)


@app.route("/kitchen")
@login_required
def kitchen():
    return render_template("kitchen.html", active_page="kitchen")

# Pantry functionalities
@app.route("/pantry")
@login_required
def pantry():
    active_tab = request.args.get("tab", "pantry")
    pantry_items = []
    search_query = ""
    selected_category = ""

    api_ingredients = []
    ingredient_search_query = ""
    ingredient_error = ""

    delete_form = DeletePantryItemForm()

    if active_tab == "pantry":
        search_query = request.args.get("q", "").strip()
        selected_category = request.args.get("category", "").strip()

        query = PantryItem.query.filter_by(owner=current_user)

        if search_query:
            query = query.filter(PantryItem.name.ilike(f"%{search_query}%"))

        if selected_category:
            query = query.filter(PantryItem.category == selected_category)

        pantry_items = query.all()

    elif active_tab == "ingredients":
        ingredient_search_query = request.args.get("q", "").strip()

        if ingredient_search_query:
            api_ingredients = Ingredient.query.filter(
                Ingredient.name.ilike(f"%{ingredient_search_query}%")
            ).order_by(Ingredient.name.asc()).all()
            if len(api_ingredients) == 0:
                ingredient_error = f"no ingredients found for '{ingredient_search_query}'"

    return render_template(
        "pantry.html",
        active_page="pantry",
        active_tab=active_tab,
        pantry_items=pantry_items,
        form=delete_form,
        search_query=search_query,
        selected_category=selected_category,
        selected_category_label=CATEGORY_LABELS.get(selected_category, selected_category),
        category_choices=PANTRY_CATEGORY_CHOICES,
        api_ingredients=api_ingredients,
        ingredient_search_query=ingredient_search_query,
        ingredient_error=ingredient_error,
    )

@app.route("/add_pantry_item", methods=['GET', 'POST'])
@login_required
def add_pantry_item():
    form = AddPantryItemForm()

    if request.method == "GET":
        ingredient_id = request.args.get("ingredient_id", "")
        form.ingredient_id.data = ingredient_id

    ingredient = None
    if form.ingredient_id.data:
        try:
            ingredient = Ingredient.query.get(int(form.ingredient_id.data))
        except (TypeError, ValueError):
            ingredient = None

    if ingredient is None:
        flash("Pick an ingredient from the Ingredients tab to add it to your pantry.", "error")
        return redirect(url_for("pantry", tab="ingredients"))

    if form.validate_on_submit():
        new_pantry_item = PantryItem(
            ingredient_id=ingredient.id,
            quantity=form.quantity.data,
            category=form.category.data,
            unit=form.unit.data,
            expiry_date = form.expiry_date.data,
            owner=current_user)
        try:
            db.session.add(new_pantry_item)
            db.session.commit()
            flash('Pantry item added successfully! ✅')
            return redirect(url_for('pantry'))  # redirect after success
        except Exception:
            db.session.rollback()
            flash('Something went wrong adding the pantry item. Please try again.', 'error')
    else:
        print("FORM ERRORS:", form.errors)
    return render_template("add_pantry_item.html", form=form, ingredient=ingredient, active_page="pantry")

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
    form.ingredient_id.data = item.ingredient_id

    if form.validate_on_submit():
        item.quantity = form.quantity.data
        item.category = form.category.data
        item.unit = form.unit.data
        item.expiry_date = form.expiry_date.data
        db.session.commit()
        return redirect(url_for('pantry'))
    return render_template('edit_pantry_item.html', form=form, item=item, active_page="pantry")


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
    # check if the user already saved this recipe, and if not, save it
    recipe = get_or_create_recipe(meal_id, user_id=current_user.id)
    
    if recipe is None:
        return redirect(url_for("recipes"))

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
    # Retrieve all meal plans for the current user, ordered by ascending or oldest/lowest id - which means oldest added to newest added planned meals
    meal_plans = MealPlan.query.filter_by(user_id=current_user.id).order_by(MealPlan.id.asc()).all()
    
    # Get and store the recipe data including img, all metadata - because it's not in the MealPlan model
    planned_meals = []
    
    for meal in meal_plans:
        recipe = Recipe.query.get(meal.recipe_id)
        # Put the retrieved meal_plans and recipes together into one variable     
        planned_meals.append({"plan": meal, "recipe": recipe})
        
    return render_template("planned.html", active_page="planned", planned_meals=planned_meals)
    
    
@app.route("/planned/add_saved_to_plan/<int:recipe_id>", methods=['POST'])
@login_required
def add_saved_to_plan(recipe_id):
    
    recipe = Recipe.query.get(recipe_id)
    if recipe is None:
        flash('That recipe could not be found.', 'error')
        return redirect(url_for('planned'))
    
    planned_meal = MealPlan(
        planned_date=date.today(), 
        user_id=current_user.id, 
        recipe_id=recipe_id
        )
    
    try:
        db.session.add(planned_meal)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('Something went wrong adding the recipe to planned meals. Please try again.', 'error')
        return redirect(url_for('planned'))

    flash(f'{recipe.name} added to Planned Meals! ✅')
    return redirect(url_for('planned'))


@app.route("/planned/add_searched_to_plan/<meal_id>", methods=['POST'])
@login_required
def add_searched_to_plan(meal_id):
    # Check the recipe is already in the user's saved meals tab. If not, save it first
    # Either way, retieve the row for the reciple being added to planned meals, as saved_recipe
    user_id=current_user.id
    saved_recipe = get_or_create_recipe(user_id, meal_id)
    
    if saved_recipe is None:
        flash('Could not find that recipe. Please try again.', 'error')
        return redirect(url_for('recipes', tab='search'))
    
    planned_meal = MealPlan(
        planned_date=date.today(), 
        user_id=saved_recipe.user_id, 
        recipe_id=saved_recipe.id
        )
    
    try:
        db.session.add(planned_meal)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('Something went wrong adding the recipe to planned meals. Please try again.', 'error')
        return redirect(url_for('planned'))
    
    flash(f'{saved_recipe.name} successfully added to Planned Meals! ✅', 'success')
    return redirect(url_for('recipes', tab='search'))
    

@app.route("/planned/mark_as_cooked/<int:item_id>", methods=['POST'])
@login_required
def mark_as_cooked(item_id):
    
    planned_meal = MealPlan.query.filter_by(id=item_id).first()
    
    if planned_meal is None:
        flash('Could not find that Planned Meal. Please try again', 'error')
        return redirect(url_for('planned'))
    
    recipe = Recipe.query.get(planned_meal.recipe_id)
    if recipe is None:
        flash('Could not find that recipe. Please try again', 'error')
        return redirect(url_for('planned'))
    
    cooked_meal = CookedMeal(
        cooked_date=datetime.now(),
        user_id=current_user.id,
        recipe_id=planned_meal.recipe_id
    )
    
    try:
        db.session.add(cooked_meal)
        db.session.delete(planned_meal)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('Something went wrong. Please try again', 'error')
        return redirect(url_for('planned'))
        
    flash(f'{recipe.name} successfully Cooked! ✅', 'success')
    return redirect(url_for('cooked'))


@app.route("/planned/delete/<int:item_id>", methods=['POST'])
@login_required
def delete_planned_meal(item_id):
    instance = MealPlan.query.get_or_404(item_id)
    
    recipe = Recipe.query.get(instance.recipe_id)
    if recipe is None:
        name = 'Meal '
    else:
        name = recipe.name
    
    try:
        db.session.delete(instance)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('Something went wrong deleting that Planned Meal. Please Try again.', 'error')
        return redirect(url_for('planned'))
    
    flash(f'{name} Successfully Deleted! ✅')
    return redirect(url_for('planned'))


@app.route("/cooked")
@login_required
def cooked():
    
    # Retrieve all cooked meals for the current user, ordered by ascending or oldest/lowest id - which means oldest cooked to newest cooked meals
    all_cooked_meals = CookedMeal.query.filter_by(user_id=current_user.id).order_by(CookedMeal.id.asc()).all()
    
    # Get and store the recipe data including img, all metadata - because it's not in the CookedMeal model
    cooked_meals = []
    for meal in all_cooked_meals:   
        recipe = Recipe.query.get(meal.recipe_id)
        # Put the retrieved meal_plans and recipes together into one variable     
        cooked_meals.append({"cooked": meal, "recipe": recipe})
    
    # Pass the data to the template
    return render_template("cooked.html", active_page="cooked", cooked_meals=cooked_meals)


@app.route("/cooked/add_cooked_to_plan/<int:recipe_id>", methods=['POST'])
@login_required
def add_cooked_to_plan(recipe_id):
    
    recipe = Recipe.query.get(recipe_id)
    if recipe is None:
        flash('Could not find that recipe. Please try again.', 'error')
        return redirect(url_for('cooked'))
    
    planned_meal = MealPlan(
        planned_date=date.today(), 
        user_id=current_user.id, 
        recipe_id=recipe_id
        )
    
    try:
        db.session.add(planned_meal)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('Something went wrong adding the recipe to Planned Meals. Please try again.', 'error')
        return redirect(url_for('planned'))
    
    flash(f'{recipe.name} successfully added to Planned Meals! ✅', 'success')
    return redirect(url_for('planned'))


@app.route("/cooked/delete/<int:item_id>", methods=['POST'])
@login_required
def delete_cooked_instance(item_id):
    instance = CookedMeal.query.get_or_404(item_id)
    
    recipe = Recipe.query.get(instance.recipe_id)
    if recipe is None:
        name = 'Meal'
    else:
        name = recipe.name
        
    try:
        db.session.delete(instance)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('Something went wrong deleting that Cooked Meal. Please try again.', 'error')
        return redirect(url_for('cooked'))
    
    flash(f'{name} Successfully Deleted! ✅', 'success')
    return redirect(url_for('cooked'))


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
