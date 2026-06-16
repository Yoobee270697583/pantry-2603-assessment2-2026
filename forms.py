from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FloatField, DateField, SelectField
from wtforms.validators import InputRequired, Length, ValidationError, Email, EqualTo, Optional, Regexp
from models import User
from constants import PANTRY_CATEGORY_CHOICES

# The RegisterForm class defines the fields and validation rules for the registration form using Flask-WTF and WTForms.
class RegisterForm(FlaskForm):
    first_name = StringField(validators=[InputRequired(), Length(min=2, max=150)])
    last_name = StringField(validators=[InputRequired(), Length(min=1, max =150)])
    email = StringField(validators=[InputRequired(), Email(message='Invalid email'), Length(max=150)])
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=256), 
                                         Regexp(
                                             r'(?=.*\d)(?=.*[a-z])(?=.*[A-Z])',
                                         message='Password must contain an uppercase letter, a lowercase letter, and a number'
                                                )
                                        ]
                            )
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


# form for creating a custom recipe
class CustomRecipeForm(FlaskForm):
    name = StringField(validators=[InputRequired(), Length(min=2, max=150)])
    category = StringField(validators=[Optional(), Length(max=100)])
    area = StringField(validators=[Optional(), Length(max=100)])
    # one ingredient per line, format: "amount, ingredient name"
    ingredients = TextAreaField(validators=[InputRequired()])
    instructions = TextAreaField(validators=[InputRequired()])
    submit = SubmitField('Save Recipe')

# Add Pantry Item Form
class AddPantryItemForm(FlaskForm):
    # Pantry item name
    name = StringField(validators=[InputRequired(), Length(min=1, max=150)])
    # Pantry Item quantity, using FloatField to allow for decimal quantities (e.g., 1.5 cups)
    quantity = FloatField(validators=[InputRequired()])
    # Pantry Item category
    category = SelectField(
        "Category",
        choices=PANTRY_CATEGORY_CHOICES,
        validators=[InputRequired()]
    )
    # Pantry Item unit, i.e. kg, g, ml, L, cup etc.
    unit = StringField(validators=[InputRequired(), Length(min=1, max=50)])
    expiry_date = DateField('Expiry Date', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Add Item')

class DeletePantryItemForm(FlaskForm):
    pass