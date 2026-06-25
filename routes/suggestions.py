import random
from flask import Blueprint, request, render_template, redirect, url_for
from flask_login import current_user, login_required
from models import PantryItem, Recipe

suggestions_bp = Blueprint("suggestions", __name__)


def get_random_suggested_recipe(user_id):
    # get all pantry ingredient names for this user
    pantry_items = PantryItem.query.filter_by(user_id=user_id).all()
    pantry_names = set(item.ingredient.name.lower() for item in pantry_items)

    if not pantry_names:
        return None

    # get all saved TheMealDB recipes with their stored ingredients
    saved_recipes = Recipe.query.filter_by(user_id=user_id, source="TheMealDB").all()

    if not saved_recipes:
        return None

    # count how many of each recipe's ingredients are in the pantry
    recipe_scores = []
    for recipe in saved_recipes:
        recipe_ingredient_names = set(i.name.lower() for i in recipe.ingredients)
        matches = len(pantry_names & recipe_ingredient_names)
        recipe_scores.append((recipe, matches))

    # only keep recipes that match at least one pantry item
    matched = [(r, score) for r, score in recipe_scores if score > 0]

    if not matched:
        return None

    # find the highest match count then pick randomly from those
    best_score = max(score for _, score in matched)
    best_recipes = [r for r, score in matched if score == best_score]

    return random.choice(best_recipes)


@suggestions_bp.route("/suggestions", methods=["GET", "POST"])
@login_required
def suggestions():
    suggested_recipe = None
    error_message = ""

    if request.method == "POST":
        suggested_recipe = get_random_suggested_recipe(current_user.id)

        if suggested_recipe is None:
            has_pantry = PantryItem.query.filter_by(user_id=current_user.id).first()
            if not has_pantry:
                error_message = "add some items to your pantry first to get recipe suggestions"
            else:
                error_message = "none of your saved recipes match your current pantry items"

    return render_template(
        "suggestions.html",
        active_page="suggestions",
        suggested_recipe=suggested_recipe,
        error_message=error_message
    )


@suggestions_bp.route("/suggestions/refresh", methods=["POST"])
@login_required
def suggestions_refresh():
    # clears the page by redirecting back to the clean GET
    return redirect(url_for("suggestions.suggestions"))
