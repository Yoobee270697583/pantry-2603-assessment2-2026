from datetime import date, datetime
from flask import Blueprint, request, render_template, redirect, flash, url_for
from flask_login import current_user, login_required
from models import MealPlan, Recipe, CookedMeal, db
from api_helper import get_or_create_recipe
from pantry_helper import sync_shopping_list, subtract_recipe_ingredients_from_pantry

# meals a user has scheduled to cook, and marking them as cooked

planned_bp = Blueprint("planned", __name__)


@planned_bp.route("/planned")
@login_required
def planned():
    # oldest added first
    meal_plans = MealPlan.query.filter_by(user_id=current_user.id).order_by(MealPlan.id.asc()).all()

    # MealPlan doesn't store recipe details itself, so pull each recipe in alongside its plan
    planned_meals = []

    for meal in meal_plans:
        recipe = Recipe.query.get(meal.recipe_id)
        planned_meals.append({"plan": meal, "recipe": recipe})

    return render_template("planned.html", active_page="planned", planned_meals=planned_meals)


@planned_bp.route("/planned/add_saved_to_plan/<int:recipe_id>", methods=['POST'])
@login_required
def add_saved_to_plan(recipe_id):

    recipe = Recipe.query.get(recipe_id)
    if recipe is None:
        flash('That recipe could not be found.', 'error')
        return redirect(url_for('planned.planned'))

    planned_meal = MealPlan(
        planned_date=date.today(),
        user_id=current_user.id,
        recipe_id=recipe_id
        )

    try:
        db.session.add(planned_meal)
        db.session.commit()
        sync_shopping_list(current_user.id)
    except Exception:
        db.session.rollback()
        flash('Something went wrong adding the recipe to planned meals. Please try again.', 'error')
        return redirect(url_for('planned.planned'))

    flash(f'{recipe.name} added to Planned Meals! ✅', 'success')
    return redirect(url_for('recipes.recipes'))


@planned_bp.route("/planned/add_searched_to_plan/<meal_id>", methods=['POST'])
@login_required
def add_searched_to_plan(meal_id):
    # save the recipe first if the user hasn't already, then plan it
    user_id = current_user.id
    saved_recipe = get_or_create_recipe(user_id, meal_id)

    search_query = request.form.get("q") or None
    selected_category = request.form.get("category") or None
    selected_area = request.form.get("area") or None

    if saved_recipe is None:
        flash('Could not find that recipe. Please try again.', 'error')
        return redirect(url_for('recipes.recipes', tab='search', q=search_query, category=selected_category, area=selected_area))

    planned_meal = MealPlan(
        planned_date=date.today(),
        user_id=saved_recipe.user_id,
        recipe_id=saved_recipe.id
        )

    try:
        db.session.add(planned_meal)
        db.session.commit()
        sync_shopping_list(saved_recipe.user_id)
    except Exception:
        db.session.rollback()
        flash('Something went wrong adding the recipe to planned meals. Please try again.', 'error')
        return redirect(url_for('planned.planned'))

    flash(f'{saved_recipe.name} successfully added to Planned Meals! ✅', 'success')
    return redirect(url_for('recipes.recipes', tab='search', q=search_query, category=selected_category, area=selected_area))


@planned_bp.route("/planned/mark_as_cooked/<int:item_id>", methods=['POST'])
@login_required
def mark_as_cooked(item_id):

    planned_meal = MealPlan.query.filter_by(id=item_id).first()

    if planned_meal is None:
        flash('Could not find that Planned Meal. Please try again', 'error')
        return redirect(url_for('planned.planned'))

    recipe = Recipe.query.get(planned_meal.recipe_id)
    if recipe is None:
        flash('Could not find that recipe. Please try again', 'error')
        return redirect(url_for('planned.planned'))

    cooked_meal = CookedMeal(
        cooked_date=datetime.now(),
        user_id=current_user.id,
        recipe_id=planned_meal.recipe_id
    )

    try:
        subtract_recipe_ingredients_from_pantry(current_user.id, recipe)
        db.session.add(cooked_meal)
        db.session.delete(planned_meal)
        db.session.commit()
        sync_shopping_list(current_user.id)
    except Exception:
        db.session.rollback()
        flash('Something went wrong. Please try again', 'error')
        return redirect(url_for('planned.planned'))

    flash(f'{recipe.name} successfully Cooked! ✅', 'success')
    return redirect(url_for('planned.planned'))


@planned_bp.route("/planned/delete/<int:item_id>", methods=['POST'])
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
        sync_shopping_list(current_user.id)
    except Exception:
        db.session.rollback()
        flash('Something went wrong deleting that Planned Meal. Please Try again.', 'error')
        return redirect(url_for('planned.planned'))

    flash(f'{name} Successfully Deleted! ✅', 'success')
    return redirect(url_for('planned.planned'))
