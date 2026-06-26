import re
from models import db, Ingredient, PantryItem, MealPlan, Recipe, ShoppingListItem

# ============================================================================
# AMOUNT PARSING / UNIT SANITIZING
# ============================================================================
# recipe amounts come from TheMealDB as free text like "400g", "2 cups",
# "to taste". these helpers turn that text into numbers + units we
# recognise (see PANTRY_UNIT_CHOICES), then convert everything to a
# common base unit (g or ml) so we can compare/subtract pantry stock
# against what a recipe needs even if the units don't match exactly.

# tried in order: mixed number ("1 1/2 cups"), fraction ("1/2 cup"),
# then plain decimal/integer ("400g", "2 cups")
MIXED_NUMBER_RE = re.compile(r"^\s*(\d+)\s+(\d+)\s*/\s*(\d+)\s*([a-zA-Z]*)")
FRACTION_RE = re.compile(r"^\s*(\d+)\s*/\s*(\d+)\s*([a-zA-Z]*)")
DECIMAL_RE = re.compile(r"^\s*(\d+(?:[.,]\d+)?)\s*([a-zA-Z]*)")

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

# words like "1 chopped onion" - "chopped" isn't a unit, it just describes
# the ingredient, so we treat these as if no unit was given at all
NON_UNIT_WORDS = {
    "chopped", "diced", "sliced", "minced", "crushed", "grated", "ground",
    "peeled", "drained", "melted", "softened", "beaten", "sifted",
    "large", "medium", "small", "whole", "fresh", "frozen", "ripe",
    "halved", "quartered", "cooked", "raw", "thinly", "finely", "roughly",
}

# (qty_per_unit, base_unit) - only units with a known, safe conversion
MASS_TO_GRAMS = {"g": 1, "kg": 1000, "oz": 28, "lb": 454}
VOLUME_TO_ML = {"ml": 1, "l": 1000, "tsp": 5, "tbsp": 15, "cup": 240}


def parse_amount(amount_str):
    """Splits a free-text amount like '400g' or '1 1/2 cups' into (quantity, raw_unit)."""
    if not amount_str:
        return 1.0, ""

    mixed_match = MIXED_NUMBER_RE.match(amount_str)
    if mixed_match:
        whole, num, den, unit_text = mixed_match.groups()
        quantity = float(whole) + float(num) / float(den)
        return quantity, unit_text.strip().lower()

    fraction_match = FRACTION_RE.match(amount_str)
    if fraction_match:
        num, den, unit_text = fraction_match.groups()
        quantity = float(num) / float(den)
        return quantity, unit_text.strip().lower()

    decimal_match = DECIMAL_RE.match(amount_str)
    if decimal_match:
        qty_text, unit_text = decimal_match.groups()
        quantity = float(qty_text.replace(",", "."))
        return quantity, unit_text.strip().lower()

    return 1.0, ""


def normalize_unit(raw_unit):
    """Maps a free-text unit word onto our known unit vocabulary.

    Known synonyms (e.g. "grams" -> "g") get mapped so they can be
    compared/converted. Unknown words (e.g. "bunch", "clove") are kept
    as-is instead of being lumped together - we don't want "1 bunch"
    and a bare "2" treated as the same unit. No unit at all, or a prep
    word like "chopped", just means "each".
    """
    if not raw_unit:
        return "each"
    cleaned = raw_unit.strip().lower()
    if cleaned in NON_UNIT_WORDS:
        return "each"
    return UNIT_SYNONYMS.get(cleaned, cleaned)


def to_base(quantity, unit):
    """Converts mass units to grams and volume units to mL. Count units (each, can, other) pass through unchanged."""
    if unit in MASS_TO_GRAMS:
        return quantity * MASS_TO_GRAMS[unit], "g"
    if unit in VOLUME_TO_ML:
        return quantity * VOLUME_TO_ML[unit], "ml"
    return quantity, unit


def sanitize_amount(amount_str):
    """Runs a raw recipe amount through parse -> normalize -> base unit, all in one go."""
    quantity, raw_unit = parse_amount(amount_str)
    unit = normalize_unit(raw_unit)
    return to_base(quantity, unit)


def find_matching_ingredient(name):
    """Looks up the Ingredient row matching a recipe ingredient's name (case-insensitive)."""
    if not name:
        return None
    return Ingredient.query.filter(
        db.func.lower(Ingredient.name) == name.strip().lower()
    ).first()


# ============================================================================
# SHOPPING LIST GENERATION
# ============================================================================

def get_required_ingredients(user_id):
    """Returns {(ingredient_id, base_unit): total_qty} needed across all of a user's planned meals."""
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
    """Returns {(ingredient_id, base_unit): total_qty} currently sitting in a user's pantry."""
    stock = {}

    pantry_items = PantryItem.query.filter_by(user_id=user_id).all()
    for item in pantry_items:
        base_qty, base_unit = to_base(item.quantity, item.unit)
        key = (item.ingredient_id, base_unit)
        stock[key] = stock.get(key, 0) + base_qty

    return stock


def sync_shopping_list(user_id):
    """Rebuilds the auto-generated part of a user's shopping list.

    Works out what's needed for planned meals minus what's already in the
    pantry, then replaces the old auto items with the fresh result.
    Manually-added items are left alone.
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
    """Adds quantity onto a user's PantryItem for this ingredient + unit, creating it if needed."""
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


def get_missing_ingredients(user_id, recipe):
    """Returns the names of any recipe ingredients the user doesn't have enough of in their pantry.

    Uses the same matching/unit rules as subtract_recipe_ingredients_from_pantry,
    so this only flags ingredients that function can actually account for - an
    ingredient name we can't match to anything counts as missing too, since
    there's no pantry stock to check it against either way.
    """
    missing = []

    for recipe_ingredient in recipe.ingredients:
        ingredient = find_matching_ingredient(recipe_ingredient.name)
        if ingredient is None:
            missing.append(recipe_ingredient.name)
            continue

        needed_base_qty, needed_base_unit = sanitize_amount(recipe_ingredient.amount)

        pantry_item = PantryItem.query.filter_by(
            user_id=user_id, ingredient_id=ingredient.id
        ).first()
        if pantry_item is None:
            missing.append(recipe_ingredient.name)
            continue

        pantry_base_qty, pantry_base_unit = to_base(pantry_item.quantity, pantry_item.unit)
        if pantry_base_unit != needed_base_unit or pantry_base_qty < needed_base_qty:
            missing.append(recipe_ingredient.name)

    return missing


def subtract_recipe_ingredients_from_pantry(user_id, recipe):
    """Takes a recipe's ingredients off the user's pantry stock when cooked.

    Skips anything we can't match to a known ingredient, or where the
    pantry unit and recipe unit aren't compatible (e.g. g vs each).
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
