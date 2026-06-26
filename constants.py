# dropdown options shared by pantry/shopping forms + templates, so the
# wording stays the same everywhere

PANTRY_CATEGORY_CHOICES = [
    ("", "Select a category"),
    ("fruit_veg", "Fruit & Vegetables"),
    ("meat_seafood", "Meat & Seafood"),
    ("dairy_eggs", "Dairy & Eggs"),
    ("pantry_staples", "Pantry Staples"),
    ("frozen", "Frozen"),
    ("bakery", "Bakery"),
    ("herbs_spices", "Herbs & Spices"),
    ("condiments", "Sauces & Condiments"),
    ("drinks", "Drinks"),
    ("other", "Other"),
]

# quick lookup so we can turn a stored value like "fruit_veg" back into
# its display label without looping through the choices list
CATEGORY_LABELS = dict(PANTRY_CATEGORY_CHOICES)

PANTRY_UNIT_CHOICES = [
    ("", "Select a unit"),
    ("g", "g"),
    ("kg", "kg"),
    ("ml", "mL"),
    ("l", "L"),
    ("each", "Each"),
    ("tsp", "tsp"),
    ("tbsp", "tbsp"),
    ("cup", "Cup"),
    ("can", "Can"),
    ("other", "Other"),
]

# same idea as CATEGORY_LABELS but for units
UNIT_LABELS = dict(PANTRY_UNIT_CHOICES)