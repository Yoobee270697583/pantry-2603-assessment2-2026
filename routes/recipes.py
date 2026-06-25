from flask import Blueprint, request, render_template, redirect, flash, url_for
from flask_login import current_user, login_required
from models import Recipe, RecipeIngredient, db
from api_helper import search_recipes, get_recipe_by_id, get_random_recipe, get_ingredients, filter_by_category, filter_by_area, get_or_create_recipe
from forms import CustomRecipeForm, EditRecipeForm

recipes_bp = Blueprint("recipes", __name__)


@recipes_bp.route("/recipes")
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


@recipes_bp.route("/recipe/random")
@login_required
def recipe_random():
    meal = get_random_recipe()

    if meal is None:
        return render_template("not_found.html", active_page="recipes"), 404

    return redirect(url_for("recipes.recipe_detail", meal_id=meal["idMeal"]))


@recipes_bp.route("/recipe/<meal_id>")
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


@recipes_bp.route("/recipe/save/<meal_id>", methods=["POST"])
@login_required
def save_recipe(meal_id):
    # check if the user already saved this recipe, and if not, save it
    recipe = get_or_create_recipe(current_user.id, meal_id)

    if recipe is None:
        return redirect(url_for("recipes.recipes"))

    db.session.commit()

    return redirect(url_for("recipes.recipe_detail", meal_id=meal_id))


@recipes_bp.route("/recipes/saved/<int:recipe_id>")
@login_required
def saved_recipe_detail(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    return render_template(
        "saved_recipe_detail.html",
        active_page="recipes",
        recipe=recipe
    )


@recipes_bp.route("/recipes/saved/<int:recipe_id>/delete", methods=["POST"])
@login_required
def delete_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)

    # only the recipe owner can delete
    if recipe.user_id != current_user.id:
        return redirect(url_for("recipes.recipes"))

    source = recipe.source
    db.session.delete(recipe)
    db.session.commit()

    if source == "Custom":
        return redirect(url_for("recipes.recipes", tab="created"))
    return redirect(url_for("recipes.recipes", tab="saved"))


@recipes_bp.route("/recipes/saved/<int:recipe_id>/edit", methods=["GET", "POST"])
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
        return redirect(url_for("recipes.saved_recipe_detail", recipe_id=recipe.id))

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


@recipes_bp.route("/recipes/create", methods=["GET", "POST"])
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
        return redirect(url_for("recipes.recipes", tab="created"))

    return render_template("create_recipe.html", active_page="recipes", form=form)
