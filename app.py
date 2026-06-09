from flask import Flask, render_template, request, redirect, flash, url_for
from models import db, User, PantryItem
from api_helper import search_recipes, get_recipe_by_id, get_ingredients
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LoginForm, RegisterForm, AddPantryItemForm

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

# ============================================================================
# ROUTES
# ============================================================================

# create a Login Manager Object, stored to login_manager variable, and initialize it with the Flask app.
login_manager = LoginManager()
login_manager.init_app(app)
# Tell the login_manager the name of the view function that handles logins, so it can redirect users there when they need to log in.
login_manager.login_view = 'login'
    

# Tell the login_manager how to load a user from the database, given the user's id.
# It does this automatically for every request where a session cookie exists, and sets the result to current_user
# Makes it available as current_user in all our routes and templates.
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

    
# Each route below maps a URL to a function that returns a page.
# render_template() finds the named file in templates/ and renders it,
# passing in any variables we want available inside the Jinja2 template.

@app.route("/", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('kitchen'))
        flash('Invalid email or password.', 'error')
    
    return render_template("login.html", form=form)


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(first_name=form.first_name.data, last_name=form.last_name.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully. Please log in.')
        return redirect(url_for('login'))
    
    return render_template("register.html", form=form)


# @app.route("/register_success")
# def register_success():
#     return render_template("register_success.html")


@app.route("/kitchen")
@login_required
def kitchen():
    return render_template("kitchen.html", active_page="kitchen")


@app.route("/pantry")
@login_required
def pantry():
    # get all pantry items owned by user
    pantry_items = PantryItem.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template(
        "pantry.html", 
        active_page="pantry",
        pantry_items=pantry_items
    )


@app.route("/recipes")
@login_required
def recipes():
    # get the search query from the url e.g. /recipes?q=pasta
    search_query = request.args.get("q", "").strip()

    results = []
    error_message = ""

    if search_query:
        results = search_recipes(search_query)

        if len(results) == 0:
            error_message = f"no recipes found for '{search_query}', try something else"

    return render_template(
        "recipes.html",
        active_page="recipes",
        results=results,
        search_query=search_query,
        error_message=error_message
    )


@app.route("/recipe/<meal_id>")
def recipe_detail(meal_id):
    meal = get_recipe_by_id(meal_id)

    # show not found page if the recipe doesnt exist
    if meal is None:
        return render_template("not_found.html", active_page="recipes"), 404

    ingredients = get_ingredients(meal)

    return render_template(
        "recipe_detail.html",
        active_page="recipes",
        meal=meal,
        ingredients=ingredients
    )


@app.route("/suggestions")
@login_required
def suggestions():
    return render_template("suggestions.html", active_page="suggestions")


@app.route("/planned")
@login_required
def planned():
    return render_template("planned.html", active_page="planned")


@app.route("/cooked")
@login_required
def cooked():
    return render_template("cooked.html", active_page="cooked")


@app.route("/shopping")
@login_required
def shopping():
    return render_template("shopping.html", active_page="shopping")


@app.route("/orders")
@login_required
def orders():
    return render_template("orders.html", active_page="orders")

# ============================================================================
# MAIN
# ============================================================================
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == "__main__":
    # debug=True auto-reloads the server when you save a file
    # and shows helpful error pages. Turn off for production.
    app.run(debug=True)
