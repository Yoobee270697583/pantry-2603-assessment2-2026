from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FloatField, DateField, SelectField, HiddenField
from wtforms.validators import InputRequired, Length, ValidationError, Email, EqualTo, Optional, Regexp
from models import User, Ingredient
from constants import PANTRY_CATEGORY_CHOICES, PANTRY_UNIT_CHOICES


# ============================================================================
# USER FORMS
# ============================================================================

# sign up form - checks passwords match and email isn't already taken
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

# login form
class LoginForm(FlaskForm):
    email = StringField(validators=[InputRequired(), Email(message='Invalid email'), Length(max=150)])
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=256)])
    submit = SubmitField('Login')
    
    
# ============================================================================
# PANTRY FORMS / CLASSES
# ============================================================================

# add pantry item form
class AddPantryItemForm(FlaskForm):
    # has to match a real Ingredient row - picked from the Ingredients tab, not typed in
    ingredient_id = HiddenField(validators=[InputRequired()])
    # float so we can handle stuff like 1.5 cups
    quantity = FloatField(validators=[InputRequired()])
    category = SelectField(
        "Category",
        choices=PANTRY_CATEGORY_CHOICES,
        validators=[InputRequired()]
    )
    # kg, g, ml, L, cup etc - see PANTRY_UNIT_CHOICES
    unit = SelectField(
        "Unit",
        choices=PANTRY_UNIT_CHOICES,
        validators=[InputRequired()]
    )
    expiry_date = DateField('Expiry Date', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Add Item')

    def validate_ingredient_id(self, ingredient_id):
        try:
            ingredient = Ingredient.query.get(int(ingredient_id.data))
        except (TypeError, ValueError):
            ingredient = None
        if ingredient is None:
            raise ValidationError('Choose an ingredient from the list.')

class DeletePantryItemForm(FlaskForm):
    pass


# ============================================================================
# SHOPPING LIST FORMS
# ============================================================================

# lets a user manually add an item to their shopping list
class AddShoppingItemForm(FlaskForm):
    # same deal as AddPantryItemForm - must be a real Ingredient, picked from search
    ingredient_id = HiddenField(validators=[InputRequired()])
    quantity = FloatField(validators=[InputRequired()])
    unit = SelectField(
        "Unit",
        choices=PANTRY_UNIT_CHOICES,
        validators=[InputRequired()]
    )
    submit = SubmitField('Add Item')

    def validate_ingredient_id(self, ingredient_id):
        try:
            ingredient = Ingredient.query.get(int(ingredient_id.data))
        except (TypeError, ValueError):
            ingredient = None
        if ingredient is None:
            raise ValidationError('Choose an ingredient from the list.')


class ShoppingItemActionForm(FlaskForm):
    pass


# ============================================================================
# RECIPE FORMS
# ============================================================================

# form for creating a custom recipe
class CustomRecipeForm(FlaskForm):
    name = StringField(validators=[InputRequired(), Length(min=2, max=150)])
    category = StringField(validators=[Optional(), Length(max=100)])
    area = StringField(validators=[Optional(), Length(max=100)])
    image_url = StringField(validators=[Optional(), Length(max=500)])
    # one ingredient per line, format: "amount, ingredient name"
    ingredients = TextAreaField(validators=[InputRequired()])
    instructions = TextAreaField(validators=[InputRequired()])
    submit = SubmitField('Save Recipe')

# form for editing an existing saved recipe
class EditRecipeForm(FlaskForm):
    name = StringField(validators=[InputRequired(), Length(min=2, max=150)])
    category = StringField(validators=[Optional(), Length(max=100)])
    area = StringField(validators=[Optional(), Length(max=100)])
    image_url = StringField(validators=[Optional(), Length(max=500)])
    ingredients = TextAreaField(validators=[InputRequired()])
    instructions = TextAreaField(validators=[InputRequired()])
    submit = SubmitField('Save Changes')