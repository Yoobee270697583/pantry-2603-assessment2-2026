from datetime import date
from flask import Blueprint, render_template
from flask_login import current_user, login_required
from models import PantryItem, Recipe
from routes.planned import get_meal_plans

# home/landing page after login - shows what's expiring soon, recipes that
# would use it up, and a quick look at planned meals

kitchen_bp = Blueprint("kitchen", __name__)


def get_recipes_using_expiring(user_id, expiring_items):
    """Returns saved recipes the user can fully make that also use up at least one expiring ingredient."""
    expiring_names = set(item.ingredient.name.lower() for item in expiring_items)

    # nothing expiring means nothing to suggest using up
    if not expiring_names:
        return []

    pantry_items = PantryItem.query.filter_by(user_id=user_id).all()
    pantry_names = set(item.ingredient.name.lower() for item in pantry_items)

    saved_recipes = Recipe.query.filter_by(user_id=user_id, source="TheMealDB").all()

    makable_with_expiring = []
    for recipe in saved_recipes:
        recipe_names = set(i.name.lower() for i in recipe.ingredients)
        if recipe_names <= pantry_names and recipe_names & expiring_names:
            makable_with_expiring.append(recipe)

    return makable_with_expiring


@kitchen_bp.route("/kitchen")
@login_required
def kitchen():
    user_id = current_user.id

    # next 15 pantry items to expire, soonest first
    expiring_soon = (
        PantryItem.query
        .filter_by(owner=current_user)
        .filter(PantryItem.expiry_date.isnot(None))
        .filter(PantryItem.expiry_date >= date.today())
        .order_by(PantryItem.expiry_date.asc())
        .limit(15)
    )

    suggested_recipes = get_recipes_using_expiring(user_id, expiring_soon)
    planned_meals = get_meal_plans(user_id)

    return render_template(
        "kitchen.html",
        active_page="kitchen",
        expiring_soon=expiring_soon,
        suggested_recipes=suggested_recipes,
        planned_meals=planned_meals,
    )
