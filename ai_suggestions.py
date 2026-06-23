import os
import json
import anthropic
from api_helper import filter_by_ingredient, get_recipe_by_id, get_ingredients

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# how many candidates we fetch full details for before sending to the ai
MAX_CANDIDATES = 15


def get_candidate_recipes(pantry_item_names):
    # calls themealdb for each pantry ingredient and collects matching recipes
    # dedupes so the same recipe doesnt appear multiple times

    seen_ids = set()
    candidates = []

    for item_name in pantry_item_names:
        results = filter_by_ingredient(item_name)
        for meal in results:
            meal_id = meal["idMeal"]
            if meal_id not in seen_ids:
                seen_ids.add(meal_id)
                candidates.append({
                    "id": meal_id,
                    "name": meal["strMeal"],
                    "thumb": meal["strMealThumb"]
                })

    return candidates


def get_full_candidate_details(candidates):
    # fetches full ingredient lists for each candidate
    # filter.php only gives us id/name/thumb, we need ingredients for the ai

    detailed = []

    for candidate in candidates[:MAX_CANDIDATES]:
        meal = get_recipe_by_id(candidate["id"])
        if meal is None:
            continue

        ingredients = get_ingredients(meal)
        detailed.append({
            "id": candidate["id"],
            "name": meal["strMeal"],
            "category": meal.get("strCategory", ""),
            "area": meal.get("strArea", ""),
            "thumb": meal.get("strMealThumb", ""),
            "ingredients": [i["name"] for i in ingredients]
        })

    return detailed


def ask_ai_for_suggestions(pantry_items, saved_recipe_names, candidate_recipes):
    # sends real recipe data to the ai and asks it to pick the best matches
    # the ai can only choose ids from the list we give it, so it cant invent anything

    if not candidate_recipes:
        return []

    prompt = f"""You are helping suggest recipes for a meal planning app called Pantry.

The user's pantry currently contains these ingredients:
{", ".join(pantry_items) if pantry_items else "(empty pantry)"}

The user has previously saved these recipes (use as a flavour preference guide only):
{", ".join(saved_recipe_names) if saved_recipe_names else "(no saved recipes yet)"}

Here is a list of real candidate recipes with their actual ingredient lists:
{json.dumps(candidate_recipes, indent=2)}

Pick exactly 6 recipes from the candidate list above (or all of them if fewer than 6 exist).
Favour recipes where the most pantry ingredients are already covered, but include all 6 even if the match is partial.
Keep the reason short - one friendly sentence mentioning which pantry items match.

Respond with ONLY valid JSON, no other text, no markdown, in this exact format:
{{
  "suggestions": [
    {{"id": "52772", "reason": "uses chicken and rice which are both in your pantry"}}
  ]
}}

Only use ids that appear in the candidate list above. Do not invent ids."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw_text = response.content[0].text.strip()

    # strip markdown fences in case the model adds them anyway
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        raw_text = raw_text.replace("json", "", 1).strip()

    try:
        parsed = json.loads(raw_text)
        return parsed.get("suggestions", [])
    except json.JSONDecodeError:
        print("couldnt parse ai response as json")
        return []


def get_suggested_recipes(pantry_item_names, saved_recipe_names):
    # main entry point - runs the full pipeline and returns a list of
    # recipe dicts ready to be passed to the suggestions template

    candidates = get_candidate_recipes(pantry_item_names)

    if not candidates:
        return []

    detailed_candidates = get_full_candidate_details(candidates)
    ai_picks = ask_ai_for_suggestions(pantry_item_names, saved_recipe_names, detailed_candidates)

    # match the ai's chosen ids back to the data we already fetched
    candidates_by_id = {c["id"]: c for c in detailed_candidates}
    suggestions = []

    for pick in ai_picks:
        recipe = candidates_by_id.get(pick["id"])
        if recipe:
            recipe_with_reason = dict(recipe)
            recipe_with_reason["reason"] = pick.get("reason", "")
            suggestions.append(recipe_with_reason)

    return suggestions
