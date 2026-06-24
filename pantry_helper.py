import re
from models import db, Ingredient, PantryItem, MealPlan, Recipe, ShoppingListItem

# ============================================================================
# AMOUNT PARSING / UNIT SANITIZING
# ============================================================================
# Recipe ingredients come from TheMealDB as free text amounts like "400g",
# "2 cups", "to taste". These helpers parse + sanitize that text into the
# same unit vocabulary pantry items already use (see PANTRY_UNIT_CHOICES),
# and then convert mass/volume units onto a common base unit (g or ml) so
# that quantities can be compared/subtracted even when the recipe and the
# pantry item use different (but compatible) units.

AMOUNT_RE = re.compile(r"^\s*([\d]+(?:[.,]\d+)?(?:\s*/\s*\d+)?)\s*([a-zA-Z]*)")

# maps free-text unit words/synonyms onto the PANTRY_UNIT_CHOICES vocabulary
UNIT_SYNONYMS = {
    "g": "g", "gram": "g", "grams": "g", "gm": "g",
    "kg": "kg", "kilogram": "kg", "kilograms": "kg",
    "ml": "ml", "millilitre": "ml", "milliliter": "ml", "millilitres": "ml",
    "l": "l", "litre": "l", "liter": "l", "litres": "l",
    "tsp": "tsp", "teaspoon": "tsp", "teaspoons": "tsp",
    "tbsp": "tbsp", "tbs": "tbsp", "tablespoon": "tbsp", "tablespoons": "tbsp",
    "cup": "cup", "cups": "cup",
    "can": "can", "cans": "can", "tin": "can", "tins": "can",
    "each": "each",
    "oz": "oz", "ounce": "oz", "ounces": "oz",
    "lb": "lb", "lbs": "lb", "pound": "lb", "pounds": "lb",
}

# (qty_per_unit, base_unit) - only units with a known, safe conversion
MASS_TO_GRAMS = {"g": 1, "kg": 1000, "oz": 28, "lb": 454}
VOLUME_TO_ML = {"ml": 1, "l": 1000, "tsp": 5, "tbsp": 15, "cup": 240}


def _parse_fraction(text):
    text = text.strip()
    if "/" in text:
        whole, _, frac = text.partition(" ")
        if "/" in whole and not frac:
            num, _, den = whole.partition("/")
            return float(num) / float(den)
        num, _, den = text.partition("/")
        return float(num) / float(den)
    return float(text.replace(",", "."))


def parse_amount(amount_str):
    """Parses a free-text recipe amount like '400g' or '2 cups' into (quantity, raw_unit)."""
    if not amount_str:
        return 1.0, ""

    match = AMOUNT_RE.match(amount_str)
    if not match:
        return 1.0, ""

    qty_text, unit_text = match.groups()
    try:
        quantity = _parse_fraction(qty_text)
    except (ValueError, ZeroDivisionError):
        quantity = 1.0

    return quantity, unit_text.strip().lower()


def normalize_unit(raw_unit):
    """Sanitizes a free-text unit word into the pantry's unit vocabulary, or 'other' if unknown."""
    if not raw_unit:
        return "other"
    return UNIT_SYNONYMS.get(raw_unit.strip().lower(), "other")


def to_base(quantity, unit):
    """Converts a (quantity, unit) into a common base unit when a safe conversion exists.

    Mass units convert to grams, volume units convert to millilitres.
    Count-style units (each, can, other) have no safe conversion and are
    returned unchanged.
    """
    if unit in MASS_TO_GRAMS:
        return quantity * MASS_TO_GRAMS[unit], "g"
    if unit in VOLUME_TO_ML:
        return quantity * VOLUME_TO_ML[unit], "ml"
    return quantity, unit


def sanitize_amount(amount_str):
    """Parses + normalizes + converts a recipe amount straight into pantry-comparable (quantity, unit)."""
    quantity, raw_unit = parse_amount(amount_str)
    unit = normalize_unit(raw_unit)
    return to_base(quantity, unit)


def find_matching_ingredient(name):
    """Finds the canonical Ingredient row matching a recipe ingredient's free-text name."""
    if not name:
        return None
    return Ingredient.query.filter(
        db.func.lower(Ingredient.name) == name.strip().lower()
    ).first()


# ============================================================================
# SHOPPING LIST GENERATION
# ============================================================================

def get_required_ingredients(user_id):
    """Returns {(ingredient_id, base_unit): total_base_qty} needed across all of a user's planned meals."""
    needed = {}

    meal_plans = MealPlan.query.filter_by(user_id=user_id).all()
    for plan in meal_plans:
        recipe = Recipe.query.get(plan.recipe_id)
        if recipe is None:
            continue

        for recipe_ingredient in recipe.ingredients:
            ingredient = find_matching_ingredient(recipe_ingredient.name)
            if ingredient is None:
                continue

            base_qty, base_unit = sanitize_amount(recipe_ingredient.amount)

            key = (ingredient.id, base_unit)
            needed[key] = needed.get(key, 0) + base_qty

    return needed


def get_pantry_stock_in_base_units(user_id):
    """Returns {(ingredient_id, base_unit): total_base_qty} currently owned by a user."""
    stock = {}

    pantry_items = PantryItem.query.filter_by(user_id=user_id).all()
    for item in pantry_items:
        base_qty, base_unit = to_base(item.quantity, item.unit)
        key = (item.ingredient_id, base_unit)
        stock[key] = stock.get(key, 0) + base_qty

    return stock


def sync_shopping_list(user_id):
    """Regenerates the auto (non-manual) shopping list rows for a user.

    Computes ingredients required by all planned meals, subtracts what's
    already in the pantry (compared in a common base unit), and replaces
    every existing auto-generated ShoppingListItem with a fresh set
    reflecting the current delta. Manually-added items are left untouched.
    """
    needed = get_required_ingredients(user_id)
    stock = get_pantry_stock_in_base_units(user_id)

    ShoppingListItem.query.filter_by(user_id=user_id, is_manual=False).delete()

    for (ingredient_id, unit), needed_qty in needed.items():
        owned_qty = stock.get((ingredient_id, unit), 0)
        delta = needed_qty - owned_qty

        if delta > 0:
            db.session.add(ShoppingListItem(
                user_id=user_id,
                ingredient_id=ingredient_id,
                quantity=round(delta, 2),
                unit=unit,
                is_manual=False
            ))

    db.session.commit()


# ============================================================================
# PANTRY <-> SHOPPING LIST / COOKING HELPERS
# ============================================================================

def add_quantity_to_pantry(user_id, ingredient_id, quantity, unit, default_category="other"):
    """Finds-or-creates a PantryItem for (user, ingredient, unit) and adds quantity onto it."""
    pantry_item = PantryItem.query.filter_by(
        user_id=user_id, ingredient_id=ingredient_id, unit=unit
    ).first()

    if pantry_item is None:
        pantry_item = PantryItem(
            user_id=user_id,
            ingredient_id=ingredient_id,
            quantity=0,
            unit=unit,
            category=default_category
        )
        db.session.add(pantry_item)

    pantry_item.quantity += quantity
    return pantry_item


def subtract_recipe_ingredients_from_pantry(user_id, recipe):
    """Subtracts a recipe's ingredients from the user's pantry, where a confident match exists.

    Ingredients with no canonical Ingredient match, or whose pantry unit
    family is incompatible with the recipe's unit, are skipped silently.
    """
    for recipe_ingredient in recipe.ingredients:
        ingredient = find_matching_ingredient(recipe_ingredient.name)
        if ingredient is None:
            continue

        needed_base_qty, needed_base_unit = sanitize_amount(recipe_ingredient.amount)

        pantry_item = PantryItem.query.filter_by(
            user_id=user_id, ingredient_id=ingredient.id
        ).first()
        if pantry_item is None:
            continue

        pantry_base_qty, pantry_base_unit = to_base(pantry_item.quantity, pantry_item.unit)
        if pantry_base_unit != needed_base_unit:
            continue

        used_base_qty = min(needed_base_qty, pantry_base_qty)
        remaining_base_qty = pantry_base_qty - used_base_qty

        if remaining_base_qty <= 0:
            db.session.delete(pantry_item)
            continue

        # convert the remaining base quantity back into the pantry item's original unit
        if pantry_item.unit != pantry_base_unit:
            conversion_table = MASS_TO_GRAMS if pantry_base_unit == "g" else VOLUME_TO_ML
            factor = conversion_table.get(pantry_item.unit, 1)
            pantry_item.quantity = remaining_base_qty / factor
        else:
            pantry_item.quantity = remaining_base_qty
