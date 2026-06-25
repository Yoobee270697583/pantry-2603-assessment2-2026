from datetime import date
from flask import Blueprint, render_template, redirect, flash, url_for
from flask_login import current_user, login_required
from models import CookedMeal, Recipe, MealPlan, db
from pantry_helper import sync_shopping_list

# history of meals that have actually been cooked

cooked_bp = Blueprint("cooked", __name__)


@cooked_bp.route("/cooked")
@login_required
def cooked():
    # oldest cooked first
    all_cooked_meals = CookedMeal.query.filter_by(user_id=current_user.id).order_by(CookedMeal.id.asc()).all()

    # CookedMeal doesn't store recipe details itself, so pull each recipe in alongside it
    cooked_meals = []
    for meal in all_cooked_meals:
        recipe = Recipe.query.get(meal.recipe_id)
        cooked_meals.append({"cooked": meal, "recipe": recipe})

    return render_template("cooked.html", active_page="cooked", cooked_meals=cooked_meals)


@cooked_bp.route("/cooked/add_cooked_to_plan/<int:recipe_id>", methods=['POST'])
@login_required
def add_cooked_to_plan(recipe_id):

    recipe = Recipe.query.get(recipe_id)
    if recipe is None:
        flash('Could not find that recipe. Please try again.', 'error')
        return redirect(url_for('cooked.cooked'))

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
        flash('Something went wrong adding the recipe to Planned Meals. Please try again.', 'error')
        return redirect(url_for('cooked.cooked'))

    flash(f'{recipe.name} successfully added to Planned Meals! ✅', 'success')
    return redirect(url_for('cooked.cooked'))


@cooked_bp.route("/cooked/delete/<int:item_id>", methods=['POST'])
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
        return redirect(url_for('cooked.cooked'))

    flash(f'{name} Successfully Deleted! ✅', 'success')
    return redirect(url_for('cooked.cooked'))
