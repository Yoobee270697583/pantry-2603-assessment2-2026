## CSS Guide — Structure & Template Conventions

Purpose: document where styles live, which responsibilities belong in each file, and how to use template blocks for page-specific styles so the team stays consistent.

---

### 1) File responsibilities (what goes where)

| File | Loaded by | Responsibility |
|---|---|---|
| `static/css/base.css` | `base.html` (always) | Resets, `:root` design tokens, typography, flash messages, shared primitives reused across most pages: buttons (`.btn-primary`, `.btn-secondary`, `.btn-rounded`, `.btn-danger`), `table`, `.form-field`, `.toolbar`/`.search-input`/`.btn-search`, `.filter-bar`, `.grid`/`.card`/`.card-*`, `.tab-bar`, `.page-header` |
| `static/css/app-shell.css` | `base.html` (always) | App-shell layout/navigation: `.left-nav`, `.bottom-nav`, `.content`, global layout breakpoints |
| `static/css/auth.css` | `auth_base.html` (login/register) | `.auth-page`, `.auth-card`, auth-specific button/form tweaks |
| `static/css/pantry.css` | `pantry.html`, `shopping.html` | Pantry-tinted form variant (`.pantry-form-field`), `.ingredient-card`, `.item-actions`, `.btn-icon` |
| `static/css/recipes.css` | `recipes.html`, `recipe_detail.html`, `saved_recipe_detail.html`, `create_recipe.html`, `edit_recipe.html`, `planned.html`, `cooked.html`, `suggestions.html` | Recipe cards/detail, `.tag`, `.search-error`/`.empty-state`, `.recipe-form`, `.btn-submit`, suggestion buttons |
| `static/css/shopping.css` | `shopping.html`, `orders.html` | Quantity stepper, manual-add panel, order cards |

Guideline: keep selectors local to their responsibility — no layout rules in page CSS, no page-specific rules in `base.css`. If a class is genuinely shared across 3+ pages (not just visually similar but the *same* component), it belongs in `base.css`, not duplicated.

**Known duplication:** `.empty-state` and `.search-error` were duplicated across `recipes.css`/`shopping.css` and have since been promoted into `base.css` (along with `.search-input`, `.btn-search`, `.filter-bar`/`.filter-select`/`.filter-clear`, and `.back-link`) since they're used widely enough to count as shared primitives. `.tag` is still defined separately in both `recipes.css` and `shopping.css` on purpose — the shopping-list version is a smaller inline label, the recipe version is a bigger pill, so they're genuinely different components that happen to share a name.

---

### 2) Template pattern (blocks & ordering)

`templates/base.html` loads the shared files and exposes a `styles` block for page CSS:

```html
<head>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/base.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/app-shell.css') }}">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    {% block styles %}{% endblock %}
</head>
```

`templates/auth_base.html` loads `base.css` + `auth.css` instead of the app shell, and still exposes its own `styles` block.

A typical page extends `base.html` and loads only the page CSS it needs:

```jinja
{% extends "base.html" %}
{% block title %}Shopping List — Pantry{% endblock %}
{% block styles %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/pantry.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='css/shopping.css') }}">
{% endblock %}
{% block content %}
  <!-- page markup -->
{% endblock %}
```

Why: this keeps the reset & tokens consistently applied while letting pages opt into extra CSS only when needed. A page can load more than one page-specific stylesheet (see `shopping.html` above) when it genuinely reuses components from another page.

---

### 3) Adding a new page (step-by-step)

1. Create the template, extend `base.html`, and load the CSS file(s) it needs in the `styles` block (see example above).
2. Add `static/css/<page>.css` with only the rules that page needs (controls, grid, cards) — check the table in section 1 first in case an existing file already covers it.
3. Add the route in `app.py` and pass `active_page` so the correct nav link gets `.is-active`:

```py
@app.route('/shopping')
@login_required
def shopping():
    return render_template('shopping.html', active_page='shopping')
```

4. If the page should appear in the left-nav (`templates/base.html`) and bottom-nav, add the link there — the nav CSS already uses `.left-nav-links a.is-active` / `.bottom-nav a.is-active`.

---

### 4) Naming and organization rules

- Prefer component-prefixed classes for clarity: `.recipe-header`, `.ingredient-card`, `.qty-stepper` instead of very generic names like `.box` or `.item`.
- Keep media queries next to the component they change, within the same file. `base.css` has the two global breakpoints (`768px`, `480px`); page CSS only needs its own breakpoint overrides for things not already handled globally (see `recipes.css`'s mobile block for an example).
- One reset only — it lives in `base.css`. Don't add resets to page-specific files.

---

### 5) Design tokens

`base.css` defines the actual tokens used throughout the app, under `:root`:

```css
:root {
    --bg: #f7f8f7;
    --surface: #ffffff;
    --surface-soft: #f6f6f3;
    --text: #1f2421;
    --muted: #6b7a6e;
    --brand: #0f6e56;
    --brand-hover: #1d9e75;
    --danger: #FF575A;
    --border: #e3e6e3;
    --radius-md: 12px;
    --radius-lg: 24px;
    --shadow-sm: 0 4px 24px rgba(0, 0, 0, 0.06);
}
```

Usage:

```css
.card {
    background: var(--surface);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-sm);
}
```

Notes:
- A lot of older/page-specific CSS (e.g. most of `recipes.css`, `pantry.css`) still uses hardcoded hex values (`#2f7d57`, `#6b7a6e`, etc.) instead of these tokens, predating the token system. **New CSS should use the `var(--...)` tokens above**, not hardcoded colors — don't copy the hardcoded-hex pattern from older files just because it's already there.
- Add new tokens to `base.css` only. If a page needs a one-off value that isn't reusable, keep it scoped to that page's CSS file rather than polluting `:root`.

---
