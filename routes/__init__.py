# wires up every blueprint onto the app - app.py just calls register_blueprints(app)

from routes.auth import auth_bp
from routes.kitchen import kitchen_bp
from routes.pantry import pantry_bp
from routes.recipes import recipes_bp
from routes.suggestions import suggestions_bp
from routes.planned import planned_bp
from routes.cooked import cooked_bp
from routes.shopping import shopping_bp
from routes.orders import orders_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(kitchen_bp)
    app.register_blueprint(pantry_bp)
    app.register_blueprint(recipes_bp)
    app.register_blueprint(suggestions_bp)
    app.register_blueprint(planned_bp)
    app.register_blueprint(cooked_bp)
    app.register_blueprint(shopping_bp)
    app.register_blueprint(orders_bp)
