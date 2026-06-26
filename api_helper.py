import requests
from models import Recipe, RecipeIngredient, db

# everything here talks to TheMealDB's free api - no api key needed

BASE_URL = "https://www.themealdb.com/api/json/v1/1/"


def search_recipes(search_term):
    # searches for recipes by name and returns a list

    try:
        url = BASE_URL + "search.php"
        response = requests.get(url, params={"s": search_term}, timeout=5)
        response.raise_for_status()

        data = response.json()

        # api returns null if nothing is found
        if data["meals"] is None:
            return []

        return data["meals"]

    except requests.exceptions.ConnectionError:
        print("no internet connection")
        return []

    except requests.exceptions.Timeout:
        print("request timed out")
        return []

    except Exception as error:
        print(f"something went wrong: {error}")
        return []


def get_recipe_by_id(meal_id):
    # gets full details for one recipe using its id

    try:
        url = BASE_URL + "lookup.php"
        response = requests.get(url, params={"i": meal_id}, timeout=5)
        response.raise_for_status()

        data = response.json()

        if data["meals"] is None:
            return None

        # comes back as a list so grab index 0
        return data["meals"][0]

    except Exception as error:
        print(f"couldnt get recipe: {error}")
        return None


def get_random_recipe():
    # calls the random endpoint and returns one meal

    try:
        url = BASE_URL + "random.php"
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()

        if data["meals"] is None:
            return None

        return data["meals"][0]

    except Exception as error:
        print(f"couldnt get random recipe: {error}")
        return None


def get_categories():
    # returns a list of all category names

    try:
        url = BASE_URL + "list.php"
        response = requests.get(url, params={"c": "list"}, timeout=5)
        response.raise_for_status()

        data = response.json()

        if data["meals"] is None:
            return []

        return [meal["strCategory"] for meal in data["meals"]]

    except Exception as error:
        print(f"couldnt get categories: {error}")
        return []


def get_areas():
    # returns a list of all cuisine area names

    try:
        url = BASE_URL + "list.php"
        response = requests.get(url, params={"a": "list"}, timeout=5)
        response.raise_for_status()

        data = response.json()

        if data["meals"] is None:
            return []

        return [meal["strArea"] for meal in data["meals"]]

    except Exception as error:
        print(f"couldnt get areas: {error}")
        return []


def filter_by_category(category):
    # returns meals that match the given category

    try:
        url = BASE_URL + "filter.php"
        response = requests.get(url, params={"c": category}, timeout=5)
        response.raise_for_status()

        data = response.json()

        if data["meals"] is None:
            return []

        return data["meals"]

    except Exception as error:
        print(f"couldnt filter by category: {error}")
        return []


def filter_by_area(area):
    # returns meals that match the given cuisine area

    try:
        url = BASE_URL + "filter.php"
        response = requests.get(url, params={"a": area}, timeout=5)
        response.raise_for_status()

        data = response.json()

        if data["meals"] is None:
            return []

        return data["meals"]

    except Exception as error:
        print(f"couldnt filter by area: {error}")
        return []


def filter_by_ingredient(ingredient):
    # returns meals that use the given ingredient as a main component
    # used by the suggested recipes feature to find pantry-matching candidates

    try:
        url = BASE_URL + "filter.php"
        response = requests.get(url, params={"i": ingredient}, timeout=5)
        response.raise_for_status()

        data = response.json()

        if data["meals"] is None:
            return []

        return data["meals"]

    except Exception as error:
        print(f"couldnt filter by ingredient: {error}")
        return []


def get_ingredients(meal):
    # the api stores ingredients as strIngredient1, strIngredient2 etc up to 20
    # this turns that into a normal list

    ingredients = []

    for i in range(1, 21):
        ingredient = meal.get(f"strIngredient{i}", "")
        measure = meal.get(f"strMeasure{i}", "")

        # skip empty slots
        if ingredient and ingredient.strip():
            ingredients.append({
                "name": ingredient.strip(),
                "amount": measure.strip() if measure else ""
            })

    return ingredients

def fetch_ingredient_list():
    # gets the full canonical ingredient list from TheMealDB, used to sync
    # our local Ingredient table - not used for per-search calls since the
    # api has no auth/SLA and we don't want pantry validation depending on it

    try:
        url = BASE_URL + "list.php"
        response = requests.get(url, params={"i": "list"}, timeout=5)
        response.raise_for_status()

        data = response.json()

        if data["meals"] is None:
            return []

        all_ingredients = data["meals"]

        # build the thumbnail url for each ingredient
        for ing in all_ingredients:
            name_for_url = ing["strIngredient"].replace(" ", "_")
            ing["image_url"] = f"https://www.themealdb.com/images/ingredients/{name_for_url}-small.png"

        return all_ingredients

    except requests.exceptions.ConnectionError:
        print("no internet connection")
        return []

    except requests.exceptions.Timeout:
        print("request timed out")
        return []

    except Exception as error:
        print(f"something went wrong: {error}")
        return []


def get_or_create_recipe(user_id, meal_id):
    # returns the user's saved copy of a mealdb recipe, saving one first if they don't have it yet

    existing = Recipe.query.filter_by(user_id=user_id, mealdb_id=meal_id).first()
    if existing:
        return existing

    meal = get_recipe_by_id(meal_id)
    if meal is None:
        return None

    new_recipe = Recipe(
        mealdb_id=meal["idMeal"],
        name=meal["strMeal"],
        category=meal.get("strCategory", ""),
        area=meal.get("strArea", ""),
        instructions=meal.get("strInstructions", ""),
        image_url=meal.get("strMealThumb", ""),
        youtube_url=meal.get("strYoutube", ""),
        source="TheMealDB",
        user_id=user_id
    )
    db.session.add(new_recipe)
    db.session.flush()  # need new_recipe.id before we can attach ingredients to it

    for item in get_ingredients(meal):
        ingredient = RecipeIngredient(
            name=item["name"],
            amount=item["amount"],
            recipe_id=new_recipe.id
        )
        db.session.add(ingredient)

    return new_recipe
