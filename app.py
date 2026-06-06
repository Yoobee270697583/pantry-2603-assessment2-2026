from flask import Flask, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash


# Create the Flask application instance.
# __name__ tells Flask where to look for templates/ and static/ folders.
app = Flask(__name__)


# Each route below maps a URL to a function that returns a page.
# render_template() finds the named file in templates/ and renders it,
# passing in any variables we want available inside the Jinja2 template.

@app.route("/")
def login():
    return render_template("login.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/kitchen")
def kitchen():
    return render_template("kitchen.html", active_page="kitchen")


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


if __name__ == "__main__":
    # debug=True auto-reloads the server when you save a file
    # and shows helpful error pages. Turn off for production.
    app.run(debug=True)
