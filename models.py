from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from constants import CATEGORY_LABELS, UNIT_LABELS

# the SQLAlchemy db instance, shared across the whole app
db = SQLAlchemy()

# ============================================================================
# DATABASE MODELS
# ============================================================================

class User(UserMixin, db.Model):
    """A user account. Owns pantry items, recipes, meal plans, and cooked meals."""

    # primary key
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)

    # user's email address
    email = db.Column(
        db.String(120), 
        unique=True, 
        nullable=False
    )

    # hashed password, never store plain text
    password = db.Column(
        db.String(255), 
        nullable=False
    )

    # pantry items owned by this user
    pantry_items = db.relationship(
        "PantryItem",
        backref="owner",
        lazy=True
    )

    # recipes saved by this user
    recipes = db.relationship(
        "Recipe",
        backref="owner",
        lazy=True
    )

class Ingredient(db.Model):
    """The master ingredient list, synced from TheMealDB. PantryItem and
    RecipeIngredient both point back here so we can match them up reliably."""

    # primary key
    id = db.Column(db.Integer, primary_key=True)

    # idIngredient from TheMealDB
    mealdb_id = db.Column(db.String(50), unique=True)

    # ingredient name
    name = db.Column(
        db.String(150),
        nullable=False,
        unique=True
    )

    # thumbnail image from TheMealDB
    image_url = db.Column(db.String(500))

    # pantry items referencing this ingredient
    pantry_items = db.relationship(
        "PantryItem",
        backref="ingredient",
        lazy=True
    )

class PantryItem(db.Model):
    """An ingredient a user currently has in stock. Used for shopping lists and recipe suggestions."""

    # primary key
    id = db.Column(db.Integer, primary_key=True)

    # ingredient this refers to - must exist in the Ingredient table
    ingredient_id = db.Column(
        db.Integer,
        db.ForeignKey("ingredient.id"),
        nullable=False
    )

    # item category
    category = db.Column(
        db.String(100),
        nullable = False
    )

    # amount currently owned
    quantity = db.Column(
        db.Float, 
        nullable=False
    )

    # unit of measurement (kg, g, L, mL etc)
    unit = db.Column(
        db.String(50),
        nullable=False
    )

    # optional expiry date
    expiry_date = db.Column(
        db.Date
    )

    # links this pantry item to a user
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey("user.id"), 
        nullable=False
    )

    @property
    def category_label(self):
        """Display-friendly version of the stored category, e.g. "fruit_veg" -> "Fruit & Vegetables"."""
        return CATEGORY_LABELS.get(self.category, self.category)

    @property
    def unit_label(self):
        """Display-friendly version of the stored unit, e.g. "ml" -> "mL"."""
        return UNIT_LABELS.get(self.unit, self.unit)

class RecipeIngredient(db.Model):
    """One ingredient line on a recipe. Compared against pantry_items to see what a user's missing."""

    # primary key
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    
    # ingredient name
    name = db.Column(
        db.String(100),
        nullable=False
    )

    # ingredient amount, as text, from TheMealDB
    amount = db.Column(
        db.String(100)
    )

    # recipe this ingredient belongs to
    recipe_id = db.Column(
        db.Integer,
        db.ForeignKey("recipe.id"),
        nullable=False
    )

class Recipe(db.Model):
    """A recipe saved by a user - either pulled from TheMealDB or written by hand."""
    # primary key
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # mealdb's own id for this recipe, if it came from there
    mealdb_id = db.Column(db.String(50))

    # recipe name
    name = db.Column(db.String(150), nullable=False)

    # recipe category
    category = db.Column(db.String(100))

    # recipe's country of origin 
    area = db.Column(db.String(100))

    # recipe instructions
    instructions = db.Column(db.Text)

    # recipe thumbnail image
    image_url = db.Column(db.String(500))

    # recipe youtube link 
    youtube_url = db.Column(db.String(500))

    # where the recipe came from - TheMealDB or Custom
    source = db.Column(
        db.String(50),
        default="TheMealDB"
    )

    # user that saved the recipe
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )
    
    # date recipe was saved
    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp()
    )

    # ingredients required for this recipe
    ingredients = db.relationship(
        "RecipeIngredient",
        backref="recipe",
        lazy=True,
        cascade="all, delete-orphan"
    )

class MealPlan(db.Model):
    """A recipe a user has scheduled to cook on a given date."""

    # primary key
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # date meal is planned for
    planned_date = db.Column(
        db.Date,
        nullable=False
    )

    # user that created the plan
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    # recipe assigned to that date
    recipe_id = db.Column(
        db.Integer,
        db.ForeignKey("recipe.id"),
        nullable=False
    )

class CookedMeal(db.Model):
    """A log entry for a meal that's actually been cooked."""

    # primary key
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # date meal was cooked
    cooked_date = db.Column(
        db.DateTime,
        default=db.func.current_timestamp()
    )

    # user who cooked the meal
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    # recipe that was cooked
    recipe_id = db.Column(
        db.Integer,
        db.ForeignKey("recipe.id"),
        nullable=False
    )

class ShoppingListItem(db.Model):
    """One item on a user's shopping list. Auto items (is_manual=False) get
    regenerated whenever planned meals or pantry stock changes; manual
    items are left alone."""

    # primary key
    id = db.Column(db.Integer, primary_key=True)

    # user this item belongs to
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    # ingredient this refers to - must exist in the Ingredient table
    ingredient_id = db.Column(
        db.Integer,
        db.ForeignKey("ingredient.id"),
        nullable=False
    )

    # amount needed
    quantity = db.Column(db.Float, nullable=False)

    # unit of measurement (g, kg, ml, l, each etc)
    unit = db.Column(db.String(50), nullable=False)

    # false for items derived from planned meals, true for user-added items
    is_manual = db.Column(db.Boolean, default=False, nullable=False)

    # ingredient this item refers to
    ingredient = db.relationship("Ingredient")

class Order(db.Model):
    """A record of a shopping list that's been added to the pantry."""

    # primary key
    id = db.Column(db.Integer, primary_key=True)

    # user who placed the order
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    # date/time the order was placed
    ordered_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp()
    )

    # items included in this order
    items = db.relationship(
        "OrderItem",
        backref="order",
        lazy=True,
        cascade="all, delete-orphan"
    )

class OrderItem(db.Model):
    """One ingredient + quantity that was part of an Order."""

    # primary key
    id = db.Column(db.Integer, primary_key=True)

    # order this item belongs to
    order_id = db.Column(
        db.Integer,
        db.ForeignKey("order.id"),
        nullable=False
    )

    # ingredient that was added to the pantry
    ingredient_id = db.Column(
        db.Integer,
        db.ForeignKey("ingredient.id"),
        nullable=False
    )

    # amount added to the pantry
    quantity = db.Column(db.Float, nullable=False)

    # unit of measurement (g, kg, ml, l, each etc)
    unit = db.Column(db.String(50), nullable=False)

    # ingredient this item refers to
    ingredient = db.relationship("Ingredient")