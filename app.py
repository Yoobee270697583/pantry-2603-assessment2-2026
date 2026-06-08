from flask import Flask, render_template
from models import db

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

# ============================================================================
# ROUTES
# ============================================================================

# Each route below maps a URL to a function that returns a page.
# render_template() finds the named file in templates/ and renders it,
# passing in any variables we want available inside the Jinja2 template.

@app.route("/")
def home():
    return render_template("home.html", active_page="home")


@app.route("/pantry")
def pantry():
    return render_template("pantry.html", active_page="pantry")


@app.route("/recipes")
def recipes():
    return render_template("recipes.html", active_page="recipes")


@app.route("/suggestions")
def suggestions():
    return render_template("suggestions.html", active_page="suggestions")


@app.route("/planned")
def planned():
    return render_template("planned.html", active_page="planned")


@app.route("/cooked")
def cooked():
    return render_template("cooked.html", active_page="cooked")


@app.route("/shopping")
def shopping():
    return render_template("shopping.html", active_page="shopping")


@app.route("/orders")
def orders():
    return render_template("orders.html", active_page="orders")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # debug=True auto-reloads the server when you save a file
    # and shows helpful error pages. Turn off for production.
    app.run(debug=True)
