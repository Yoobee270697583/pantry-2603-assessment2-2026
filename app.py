from flask import Flask, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError, Email, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash


# Create the Flask application instance.
# __name__ tells Flask where to look for templates/ and static/ folders.
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pantry.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'

# Create the SQLAlchemy database instance, stored to the db variable, and initialize it with the Flask app.
db = SQLAlchemy(app)


#The User Model/Table in the databse
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)


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


# The RegisterForm class defines the fields and validation rules for the registration form using Flask-WTF and WTForms.
class RegisterForm(FlaskForm):
    first_name = StringField(validators=[InputRequired(), Length(min=2, max=150)])
    last_name = StringField(validators=[InputRequired(), Length(min=1, max =150)])
    email = StringField(validators=[InputRequired(), Email(message='Invalid email'), Length(max=150)])
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=256)])
    confirm_password = PasswordField(validators=[InputRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')
    
    def validate_email(self, email):
        existing_user_email = User.query.filter_by(email=email.data).first()
        if existing_user_email:
            raise ValidationError('An account using that email already exists. Please log in instead.')
    
    
# The LoginForm class defines the fields and validation rules for the login form using Flask-WTF and WTForms.
class LoginForm(FlaskForm):
    email = StringField(validators=[InputRequired(), Email(message='Invalid email'), Length(max=150)])
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=256)])
    submit = SubmitField('Login')
    
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
