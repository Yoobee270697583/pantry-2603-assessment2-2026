from flask import Blueprint, render_template
from flask_login import current_user, login_required
from models import Order
from constants import UNIT_LABELS

orders_bp = Blueprint("orders", __name__)


@orders_bp.route("/orders")
@login_required
def orders():
    user_orders = Order.query.filter_by(
        user_id=current_user.id
    ).order_by(Order.ordered_at.desc()).all()

    return render_template(
        "orders.html",
        active_page="orders",
        orders=user_orders,
        unit_labels=UNIT_LABELS,
    )
