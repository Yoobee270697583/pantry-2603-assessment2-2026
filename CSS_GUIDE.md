## CSS Guide — Structure & Template Conventions

Purpose: document where styles live, which responsibilities belong in each file, and how to use template blocks for page-specific styles so the team stays consistent.

---

1) File responsibilities (what goes where)

- `static/css/base.css` — resets, CSS variables (design tokens), typography, small utilities, and form/button primitives. Always load this first.
- `static/css/app-shell.css` — app-shell layout and navigation: left-nav, bottom-nav, `.content` container, global layout breakpoints. Loaded by templates that extend `base.html`.
- `static/css/auth.css` — login/register screens and auth-specific components. Loaded by `auth-base.html` (or auth templates).
- `static/css/<page>.css` — page-specific styles (e.g., `recipes.css`). Only load these on the pages that need them via the template `styles` block.

Guideline: keep selectors local to their responsibility (no layout rules in page CSS; no page-specific rules in `base.css`).

---

2) Template pattern (blocks & ordering)

- `templates/base.html` should load the shared files and expose a `styles` block for page CSS:

```html
<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/base.css') }}">
  <link rel="stylesheet" href="{{ url_for('static', filename='css/dashboard-style.css') }}">
  {% block styles %}{% endblock %}
  <title>{% block title %}Pantry{% endblock %}</title>
</head>
<body>
  {% block content %}{% endblock %}
</body>
</html>
```

- `templates/auth-base.html` should load `base.css` + `auth.css` and also provide a `styles` block:

```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/base.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='css/auth.css') }}">
{% block styles %}{% endblock %}
```

Why: this keeps the reset & tokens consistently applied while letting pages opt into extra CSS only when needed.

---

3) Adding a new page (step-by-step)

1. Create the template and extend the correct base:

```jinja
{% extends "base.html" %}
{% block title %}My Page — Pantry{% endblock %}
{% block styles %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/my-page.css') }}">
{% endblock %}
{% block content %}
  <!-- page markup -->
{% endblock %}
```

2. Add `static/css/my-page.css` with only rules needed for this page (controls, grid, cards).

3. Add the route in Flask and pass `active_page` when the page should highlight a sidebar item:

```py
@app.route('/my-page')
def my_page():
    return render_template('my-page.html', active_page='recipes')
```

4. If the page should be linked in the left-nav, add the link in `base.html` and rely on the `active_page` variable to add the `.is-active` class.

---

4) Example: recipes page and nested nav styles

- `templates/recipes.html` should extend `base.html` and load `recipes.css` via `styles` block (see above). Put search, grid, and card rules in `static/css/recipes.css`.

- If you add a nested page (for example `/recipes/new` or `/recipes/vegetarian`) that should keep the Recipes nav item active, render it with `active_page='recipes'` from the view function. The left-nav CSS already uses `.left-nav-links a.is-active` to style the active link.

Example Flask snippet:

```py
@app.route('/recipes/vegetarian')
def recipes_vegetarian():
    results = get_vegetarian_recipes()
    return render_template('recipes-veg.html', results=results, active_page='recipes')
```

In `recipes-veg.html` use the same `recipes.css` or create a small `recipes-veg.css` and load it in the `styles` block. Keep visual differences small and driven by variables in `base.css`.

---

5) Naming and organization rules (short)

- Prefer component-prefixed classes for clarity: `.form-field`, `.auth-card`, `.recipe-card` instead of very generic `.field`.
- Keep utility classes (e.g., `.text-center`, `.mt-8`) small and documented in `base.css` if you use them.
- Keep media queries next to the component they change (within the same file). Only extract shared responsive helpers if duplicated across files.

---

6) CSS resets and tokens

- One reset only: put it in `base.css`.
- Define colors, radii, shadows as `:root` variables in `base.css` so all files use the same tokens.

---

### Tokens (examples and usage)

Use CSS custom properties in `:root` inside `base.css` so every stylesheet can consume the same design tokens.

Example `:root` token set (keep names short and semantic):

```css
:root {
  --color-bg: #f7f8f7;
  --color-surface: #ffffff;
  --color-text: #1f2421;
  --color-muted: #6b7a6e;
  --brand: #0f6e56;
  --brand-600: #1d9e75;

  --radius-sm: 6px;
  --radius-md: 12px;
  --radius-lg: 24px;

  --shadow-sm: 0 4px 12px rgba(0,0,0,0.06);
  --shadow-md: 0 8px 24px rgba(0,0,0,0.08);

  --space-1: 4px;
  --space-2: 8px;
  --space-3: 16px;
}
```

Usage patterns:

- Reference tokens in component CSS: `background: var(--color-surface); border-radius: var(--radius-md);`.
- Compose tokens for variants: `background: linear-gradient(0deg, rgba(15,110,86,0.08), transparent), var(--color-surface);`.
- Provide fallback values when necessary: `color: var(--color-text, #1f2421);`.

Developer notes:

- Keep token names semantic (e.g., `--brand`, `--color-surface`) rather than tied to a single use-case (`--panel-green`), so they remain reusable.
- Add tokens to `base.css` only. If a page needs a one-off value, prefer a component-level variable prefixed with the component name.


---