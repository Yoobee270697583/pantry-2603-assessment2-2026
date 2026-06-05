import requests

# base url for the meal api
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
