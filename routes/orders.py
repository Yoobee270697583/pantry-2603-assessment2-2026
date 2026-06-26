from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required
from models import Order
from constants import UNIT_LABELS

# read-only history of shopping lists that were checked out into the pantry

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
    )


@orders_bp.route("/orders/<int:order_id>")
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)

    if order.user_id != current_user.id:
        return redirect(url_for("orders.orders"))

    return render_template(
        "order_detail.html",
        active_page="orders",
        order=order,
        unit_labels=UNIT_LABELS,
    )
