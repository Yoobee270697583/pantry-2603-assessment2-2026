from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

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

    # Username used for login/display
    username = db.Column(
        db.String(80), 
        unique=True, 
        nullable=False
    )

    # User email address
    email = db.Column(
        db.String(120), 
        unique=True, 
        nullable=False
    )

    # Hashed password
    password_hash = db.Column(
        db.String(225), 
        nullable=False
    )

class PantryItem(db.Model):
    """
    Represents an ingredient stored in a user's pantry.
    Used when getting shopping lists and suggesting recipes
    """

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Ingredient name
    name = db.Column(
        db.String(100), 
        nullable=False
    )

    # Amount currently owned
    quantity = db.Column(
        db.Float, 
        nullable=False
    )

    # Unit of measurement (kg, g, L, mL etc)
    unit = db.Column(
        db.String(50)
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