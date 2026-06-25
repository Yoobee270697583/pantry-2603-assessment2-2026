from flask import Flask
from models import User, Ingredient, db
from api_helper import fetch_ingredient_list
from flask_login import LoginManager
from routes import register_blueprints

# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================
# DB Debug
database_debug = True


# Create the Flask application instance.
# __name__ tells Flask where to look for templates/ and static/ folders.
app = Flask(__name__)

# Configures the SQLite database location
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pantry.db"

# Disable modification tracking for better performance
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = 'thisisasecretkey'

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

# Connects SQLAlchemy to the Flask application instance
db.init_app(app)

# Create database tables if they do not exist
with app.app_context():
    db.create_all()

    if database_debug:
        print("\n=== DATABASE TABLES ===")
        for table in db.metadata.tables.keys():
            print(f"✅ {table}")
        print("=======================\n")

    # one-time sync of the canonical ingredient list from TheMealDB so that
    # pantry items can be validated against our own table instead of the
    # live api on every request
    if Ingredient.query.count() == 0:
        for ing in fetch_ingredient_list():
            db.session.add(Ingredient(
                mealdb_id=ing.get("idIngredient"),
                name=ing["strIngredient"],
                image_url=ing.get("image_url")
            ))
        db.session.commit()

# ============================================================================
# LOGIN MANAGER
# ============================================================================

# create a Login Manager Object, stored to login_manager variable, and initialize it with the Flask app.
login_manager = LoginManager()
login_manager.init_app(app)
# Tell the login_manager the name of the view function that handles logins, so it can redirect users there when they need to log in.
login_manager.login_view = 'auth.login'


# Tell the login_manager how to load a user from the database, given the user's id.
# It does this automatically for every request where a session cookie exists, and sets the result to current_user
# Makes it available as current_user in all our routes and templates.
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ============================================================================
# ROUTES
# ============================================================================
register_blueprints(app)


if __name__ == "__main__":
    # debug=True auto-reloads the server when you save a file
    # and shows helpful error pages. Turn off for production.
    app.run(debug=True)
