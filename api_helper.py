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

def search_ingredients(search_term):
    try:
        url = BASE_URL + "list.php"
        response = requests.get(url, params={"i": "list"}, timeout=5)
        response.raise_for_status()

        data = response.json()

        if data["meals"] is None:
            return []

        all_ingredients = data["meals"]

        search_term_lower = search_term.lower()
        matches = [
            ing for ing in all_ingredients
            if search_term_lower in ing["strIngredient"].lower()
        ]

        # build the thumbnail url for each match
        for ing in matches:
            name_for_url = ing["strIngredient"].replace(" ", "_")
            ing["image_url"] = f"https://www.themealdb.com/images/ingredients/{name_for_url}-small.png"

        return matches

    except requests.exceptions.ConnectionError:
        print("no internet connection")
        return []

    except requests.exceptions.Timeout:
        print("request timed out")
        return []

    except Exception as error:
        print(f"something went wrong: {error}")
        return []