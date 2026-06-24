# Pantry

A Flask web app for managing your pantry, recipes, meal planning, and shopping — built around [TheMealDB](https://www.themealdb.com/) API for recipe data.

**Tagline:** Use More. Waste Less.

---

## Tech Stack

- **Backend:** Python 3 / Flask
- **Database:** SQLite (via Flask-SQLAlchemy), no migration framework — schema is created with `db.create_all()` on startup
- **Auth:** Flask-Login (session-based), Werkzeug password hashing
- **Forms:** Flask-WTF / WTForms (CSRF-protected)
- **External API:** [TheMealDB](https://www.themealdb.com/api.php) — recipe search/lookup and the canonical ingredient list
- **Frontend:** Server-rendered Jinja templates, plain CSS (no framework/build step), Font Awesome icons via CDN

---

## Project Structure

```
app.py              Flask app, all routes
models.py           SQLAlchemy models
forms.py            WTForms form definitions
constants.py        Category/unit choice lists + display labels
api_helper.py        TheMealDB API integration
pantry_helper.py     Ingredient matching, unit parsing/conversion,
                     shopping-list sync, pantry subtraction logic
templates/           Jinja templates (one per page, extending base.html)
static/css/          Page-scoped stylesheets (see CSS_GUIDE.md)
```

---

## Setup & Running Locally

### 1. Clone the repository

```bash
git clone <repository-url>
cd pantry-2603-assessment2-2026
```

### 2. Create a virtual environment

**Windows**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Mac / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python app.py
```

The app will be available at:

```
http://127.0.0.1:5000
```

### 5. First run — important

On first startup, the app connects to TheMealDB and syncs its full ingredient list (~900 ingredients) into the local `Ingredient` table. **This requires an internet connection on the very first run.** It only happens once — once `pantry.db` has ingredients in it, the app won't re-sync on later restarts, even offline (recipe search/lookup will still need internet any time it's used, since that's fetched live).

A `pantry.db` SQLite file will be created automatically in the project root the first time you run the app. Deleting it resets all data (users, pantry, recipes, etc.) and triggers a fresh ingredient sync on next run.

### 6. Deactivate the virtual environment

```bash
deactivate
```

---

## Marking / Feature Walkthrough Guide

There's no seeded demo account — register a fresh user first. The suggested order below exercises every feature and shows how they connect, rather than testing pages in isolation.

1. **Register & log in** (`/register`, then `/`) — creates a `User` row, redirects to `/kitchen` on success.

2. **Add a few Pantry items** (`/pantry`)
   - "Ingredients" tab → search (e.g. "chicken") → "+ Add to Pantry" → set quantity/unit/category/expiry.
   - "My Pantry" tab → confirm the item shows, try searching/filtering by category.

3. **Find or create a recipe** (`/recipes`)
   - "Pantry Recipe Library" tab → search TheMealDB or filter by category/cuisine → open a recipe → "Save Recipe".
   - Optionally use "My Created Recipes" → "Create Recipe" to add a custom recipe (one ingredient per line, format `amount, name`).

4. **Plan the meal** (`/planned`)
   - From the saved recipe (or directly from search results), click "Plan this meal".
   - Go to `/planned` — the recipe should appear as a card with "Cook This Meal" and "Remove from Planned Meals".

5. **Check the Shopping List** (`/shopping`)
   - It should already show what's needed for the planned recipe **minus** whatever you already have in your pantry (try planning a recipe that needs an ingredient you've already stocked, to see the quantity reduced rather than listed in full).
   - Try the `+`/`-` quantity steppers, delete an item, and the manual-add panel (search an ingredient → set quantity/unit → "+ Add").
   - Click **"Add List To Pantry"** — this should update your Pantry, clear the Shopping List, and create an entry under `/orders`.

6. **Cook the meal** (`/planned` → "Cook This Meal")
   - This moves the meal to `/cooked` **and** subtracts the recipe's ingredients from your Pantry (check `/pantry` before/after to see the quantity drop, or the item disappear if fully used).
   - The Shopping List re-syncs automatically afterward (the cooked meal is no longer "planned", so its ingredients drop off the list).

7. **Cooked Meals** (`/cooked`) — confirm the cooked entry, try "Plan This Meal Again" (re-adds to Planned Meals) and "Delete".

8. **Previous Orders** (`/orders`) — confirm the order from step 5 is listed with its ingredients/quantities and a timestamp.

9. **Suggested Recipes** (`/suggestions`) — with pantry items + at least one saved TheMealDB recipe sharing an ingredient, click "Get Suggestion". It should show a recipe; "Get Suggestion" then disables and "Refresh" enables.

10. **Logout** (`/logout`).

### Things that are intentional, not bugs

- Searching "My Recipes → My Created Recipes" shows **all** users' custom recipes, not just your own (by design — it's a shared/community tab).
- A pantry item that's fully used up by cooking is **removed** from the pantry list rather than left at `0`.
- Quantities on auto-generated Shopping List rows reset whenever planned meals change (adding/removing/cooking a meal recalculates them from scratch). Manually-added shopping list items are never touched by this.
- Recipe ingredient amounts come from TheMealDB as free text ("400g", "2 cups", "to taste"). The app parses and converts these into a common unit (grams for mass, mL for volume) to compare against pantry stock — see Known Limitations below for where this can't reconcile cleanly.

---

## Known Limitations

- **Unit families don't cross-convert.** Mass↔mass (g/kg) and volume↔volume (mL/L/tsp/tbsp/cup) conversions work; a recipe needing "2 cups" of something tracked in the pantry as `each`/`can` can't be reconciled, so it won't be subtracted/listed correctly.
- **Cup/tbsp/tsp→gram conversions are generic**, not ingredient-specific (a cup of flour and a cup of water are treated the same).
- **Custom recipe ingredients are free text** and must exactly match (case-insensitively) a name in the canonical `Ingredient` table to be tracked by the Shopping List / pantry subtraction. TheMealDB-sourced recipes match well since they share that vocabulary; hand-typed custom recipes may not.
- **"My Pantry" search** matches on ingredient name (joins to `Ingredient`), not a free-text field on `PantryItem` itself.
- **No database migrations.** Schema changes require deleting `pantry.db` and letting `db.create_all()` rebuild it (acceptable for a student project; would need Flask-Migrate/Alembic for production use).

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the branching/PR workflow and [CSS_GUIDE.md](CSS_GUIDE.md) for stylesheet structure and conventions.

---

## Team

- **Allan** — Product Owner, UX Designer, Frontend Developer
- **Ben** — Team Lead, Frontend & Backend Developer, Documentation
- **Adam** — Frontend & Backend Developer
