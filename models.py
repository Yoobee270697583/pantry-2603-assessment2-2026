from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from constants import CATEGORY_LABELS, UNIT_LABELS

# Database instance
db = SQLAlchemy()

# ============================================================================
# DATABASE MODELS
# ============================================================================

class User(UserMixin, db.Model):
    """
    Stores user account information.

    Each user can own multiple pantry items,
    recipes, meal plans, and cooked meals.
    """

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)

    # User email address
    email = db.Column(
        db.String(120), 
        unique=True, 
        nullable=False
    )

    # Hashed password
    password = db.Column(
        db.String(255), 
        nullable=False
    )

    # Pantry items owned by this user
    pantry_items = db.relationship(
        "PantryItem",
        backref="owner",
        lazy=True
    )

    # Recipes saved by this user
    recipes = db.relationship(
        "Recipe",
        backref="owner",
        lazy=True
    )

class Ingredient(db.Model):
    """
    Canonical ingredient list, synced from TheMealDB.
    PantryItem and RecipeIngredient reference this table so that
    pantry items and recipe ingredients can be matched reliably.
    """

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # idIngredient from TheMealDB
    mealdb_id = db.Column(db.String(50), unique=True)

    # Ingredient name
    name = db.Column(
        db.String(150),
        nullable=False,
        unique=True
    )

    # Thumbnail from TheMealDB
    image_url = db.Column(db.String(500))

    # Pantry items referencing this ingredient
    pantry_items = db.relationship(
        "PantryItem",
        backref="ingredient",
        lazy=True
    )

class PantryItem(db.Model):
    """
    Represents an ingredient stored in a user's pantry.
    Used when getting shopping lists and suggesting recipes
    """

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Ingredient this pantry item refers to - must exist in Ingredient table
    ingredient_id = db.Column(
        db.Integer,
        db.ForeignKey("ingredient.id"),
        nullable=False
    )

    # Item category
    category = db.Column(
        db.String(100),
        nullable = False
    )

    # Amount currently owned
    quantity = db.Column(
        db.Float, 
        nullable=False
    )

    # Unit of measurement (kg, g, L, mL etc)
    unit = db.Column(
        db.String(50),
        nullable=False
    )

    # Optional expiry date
    expiry_date = db.Column(
        db.Date
    )

    # Links pantry item to a user
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey("user.id"), 
        nullable=False
    )

    @property
    def category_label(self):
        """Returns the display label for the stored category value."""
        return CATEGORY_LABELS.get(self.category, self.category)
    
    @property
    def unit_label(self):
        """Returns the display label for the stored unit value."""
        return UNIT_LABELS.get(self.unit, self.unit)

class RecipeIngredient(db.Model):
    """
    Represents ingredients required for recipe.
    Will use to comapare ingredients required to the ingredients
    that the user already owns in their pantry i.e. pantry_items
    """

    # Primary Key
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    
    # Ingredient Name
    name = db.Column(
        db.String(100),
        nullable=False
    )

    # Ingredient amount from TheMealDB
    amount = db.Column(
        db.String(100)
    )

    # Recipe this ingredient belongs to
    recipe_id = db.Column(
        db.Integer,
        db.ForeignKey("recipe.id"),
        nullable=False
    )

class Recipe(db.Model):
    """
    Represents stored recipes saved by the user.
    Recipes may come from TheMealDB or be manually created
    """
    # Primary DB ID Key
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # External ID from mealdb if it exists
    mealdb_id = db.Column(db.String(50))

    # Recipe name
    name = db.Column(db.String(150), nullable=False)

    # Recipe Category
    category = db.Column(db.String(100))

    # Recipe Origin Country 
    area = db.Column(db.String(100))

    # Recipe Instructions
    instructions = db.Column(db.Text)

    # Recipe Thumbnail
    image_url = db.Column(db.String(500))

    # Recipe youtube link 
    youtube_url = db.Column(db.String(500))

    # Recipe source, will be either TheMealDB or Custom
    source = db.Column(
        db.String(50),
        default="TheMealDB"
    )

    # User that saved the recipe
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )
    
    # Date recipe was saved
    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp()
    )

    # Ingredients required for this recipe
    ingredients = db.relationship(
        "RecipeIngredient",
        backref="recipe",
        lazy=True,
        cascade="all, delete-orphan"
    )

class MealPlan(db.Model):
    """
    Stores recipes planned for a specific date
    """

    # Primary key
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # Date meal is planned for
    planned_date = db.Column(
        db.Date,
        nullable=False
    )

    # User that created the plan
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    # Recipe assigned to that date
    recipe_id = db.Column(
        db.Integer,
        db.ForeignKey("recipe.id"),
        nullable=False
    )

class CookedMeal(db.Model):
    """
    Stores meals that have been cooked.
    """

    # Primary Key
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # Date meal was cooked
    cooked_date = db.Column(
        db.DateTime,
        default=db.func.current_timestamp()
    )

    # User who cooked the meal
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    # Recipe that was cooked
    recipe_id = db.Column(
        db.Integer,
        db.ForeignKey("recipe.id"),
        nullable=False
    )