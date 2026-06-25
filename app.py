from flask import Flask
from models import User, Ingredient, db
from api_helper import fetch_ingredient_list
from flask_login import LoginManager
from routes import register_blueprints

# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================

# set to False to stop printing the table list on startup
database_debug = True

# __name__ tells Flask where to find the templates/ and static/ folders
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pantry.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # don't need this, just saves memory
app.config["SECRET_KEY"] = 'thisisasecretkey'

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

db.init_app(app)

# creates tables if they don't already exist - safe to run every startup
with app.app_context():
    db.create_all()

    if database_debug:
        print("\n=== DATABASE TABLES ===")
        for table in db.metadata.tables.keys():
            print(f"✅ {table}")
        print("=======================\n")

    # one-time sync of TheMealDB's ingredient list, so pantry items can be
    # checked against our own table instead of hitting the live api every time
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

login_manager = LoginManager()
login_manager.init_app(app)
# where to send people if they try to access a @login_required page while logged out
login_manager.login_view = 'auth.login'


# flask-login calls this on every request to turn the session cookie into a
# real User, which then shows up as current_user everywhere
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
