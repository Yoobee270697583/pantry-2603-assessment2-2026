from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, DateField
from wtforms.validators import InputRequired, Length, ValidationError, Email, EqualTo
from models import User
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

class AddPantryItemForm(FlaskForm):
    """
    Form used to add an item to the users pantry
    """

    # Ingredient name
    name = StringField(
        validators=[
            InputRequired(),
            Length(min=1, max=100)
        ]
    )

    # Qty Owned
    quantity = FloatField(
        validators=[
            InputRequired()
        ]
    )

    # Unit (kg, g, L, mL etc)
    unit = StringField(
        validators=[
            Length(max=50)
        ]
    )

    # Optional Exp date
    expiry_date = DateField(
        format="%Y-%m-%d",
        validators=[],
        default=None
    )

    submit = SubmitField("Add Item")