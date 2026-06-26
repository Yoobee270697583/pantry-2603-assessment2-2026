import random
from flask import Blueprint, request, render_template, redirect, url_for
from flask_login import current_user, login_required
from models import PantryItem, Recipe

# suggests a saved recipe based on what's in the user's pantry

suggestions_bp = Blueprint("suggestions", __name__)


def get_makable_recipes(user_id):
    """Returns every saved TheMealDB recipe the user can fully make from their current pantry."""
    pantry_items = PantryItem.query.filter_by(user_id=user_id).all()
    pantry_item_names = set(item.ingredient.name.lower() for item in pantry_items)

    if not pantry_item_names:
        return []

    saved_recipes = Recipe.query.filter_by(user_id=user_id, source="TheMealDB").all()

    if not saved_recipes:
        return []

    makable_recipes = []
    for recipe in saved_recipes:
        ingredient_names = set(i.name.lower() for i in recipe.ingredients)
        if ingredient_names <= pantry_item_names:
            makable_recipes.append(recipe)

    return makable_recipes


def get_random_suggested_recipe(user_id):
    """Picks a random saved recipe that shares at least one ingredient with the user's pantry."""
    pantry_items = PantryItem.query.filter_by(user_id=user_id).all()
    pantry_item_names = set(item.ingredient.name.lower() for item in pantry_items)

    if not pantry_item_names:
        return None

    saved_recipes = Recipe.query.filter_by(user_id=user_id, source="TheMealDB").all()

    if not saved_recipes:
        return None

    # score each recipe by how many of its ingredients are in the pantry
    recipe_scores = []
    for recipe in saved_recipes:
        ingredient_names = set(i.name.lower() for i in recipe.ingredients)
        matches = len(pantry_item_names & ingredient_names)
        recipe_scores.append((recipe, matches))

    # ignore recipes with zero matches
    matched = [(r, score) for r, score in recipe_scores if score > 0]

    if not matched:
        return None

    # pick any matched recipe at random - not just the best-scoring ones,
    # otherwise the same handful of recipes keep winning every time
    chosen_recipe, _ = random.choice(matched)
    return chosen_recipe


@suggestions_bp.route("/suggestions", methods=["GET", "POST"])
@login_required
def suggestions():
    user_id = current_user.id
    random_suggested_recipe = None
    error_message = ""

    # shown as a fallback list whenever there's no random pick on screen
    all_suggestable_recipes = get_makable_recipes(user_id)

    if request.method == "POST":
        random_suggested_recipe = get_random_suggested_recipe(user_id)

        if random_suggested_recipe is None:
            has_pantry = PantryItem.query.filter_by(user_id=user_id).first()
            if not has_pantry:
                error_message = "add some items to your pantry first to get recipe suggestions"
            else:
                error_message = "none of your saved recipes match your current pantry items"

    return render_template(
        "suggestions.html",
        active_page="suggestions",
        random_suggested_recipe=random_suggested_recipe,
        all_suggestable_recipes=all_suggestable_recipes,
        error_message=error_message
    )


@suggestions_bp.route("/suggestions/refresh", methods=["POST"])
@login_required
def suggestions_refresh():
    # clears the page by redirecting back to the clean GET
    return redirect(url_for("suggestions.suggestions"))
