from flask import Blueprint, render_template
from flask_login import login_required

# just the home/landing page after login

kitchen_bp = Blueprint("kitchen", __name__)


@kitchen_bp.route("/kitchen")
@login_required
def kitchen():
    return render_template("kitchen.html", active_page="kitchen")
