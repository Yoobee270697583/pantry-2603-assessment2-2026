from flask import Blueprint, request, render_template, redirect, flash, url_for
from flask_login import current_user, login_required
from models import ShoppingListItem, Ingredient, Order, OrderItem, db
from constants import UNIT_LABELS
from forms import AddShoppingItemForm, ShoppingItemActionForm
from pantry_helper import add_quantity_to_pantry

shopping_bp = Blueprint("shopping", __name__)


@shopping_bp.route("/shopping")
@login_required
def shopping():
    shopping_items = ShoppingListItem.query.filter_by(
        user_id=current_user.id
    ).join(Ingredient).order_by(Ingredient.name.asc()).all()

    ingredient_search_query = request.args.get("q", "").strip()
    api_ingredients = []
    if ingredient_search_query:
        api_ingredients = Ingredient.query.filter(
            Ingredient.name.ilike(f"%{ingredient_search_query}%")
        ).order_by(Ingredient.name.asc()).all()

    return render_template(
        "shopping.html",
        active_page="shopping",
        shopping_items=shopping_items,
        unit_labels=UNIT_LABELS,
        action_form=ShoppingItemActionForm(),
        add_form=AddShoppingItemForm(),
        ingredient_search_query=ingredient_search_query,
        api_ingredients=api_ingredients,
    )


@shopping_bp.route("/shopping/add", methods=["POST"])
@login_required
def add_shopping_item():
    form = AddShoppingItemForm()

    if form.validate_on_submit():
        new_item = ShoppingListItem(
            user_id=current_user.id,
            ingredient_id=int(form.ingredient_id.data),
            quantity=form.quantity.data,
            unit=form.unit.data,
            is_manual=True
        )
        db.session.add(new_item)
        db.session.commit()
        flash('Item added to your Shopping List! ✅', 'success')
    else:
        flash('Could not add that item to your Shopping List. Please try again.', 'error')

    return redirect(url_for('shopping.shopping'))


@shopping_bp.route("/shopping/update/<int:item_id>", methods=["POST"])
@login_required
def update_shopping_item(item_id):
    item = ShoppingListItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()

    direction = request.form.get("direction")
    step = 1 if item.quantity >= 1 else 0.1

    if direction == "increase":
        item.quantity += step
    elif direction == "decrease":
        item.quantity = max(0.1, item.quantity - step)

    db.session.commit()
    return redirect(url_for('shopping.shopping'))


@shopping_bp.route("/shopping/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_shopping_item(item_id):
    item = ShoppingListItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash('Item removed from your Shopping List.', 'success')
    return redirect(url_for('shopping.shopping'))


@shopping_bp.route("/shopping/add_to_pantry/<int:item_id>", methods=["POST"])
@login_required
def add_shopping_item_to_pantry(item_id):
    item = ShoppingListItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    ingredient_name = item.ingredient.name

    add_quantity_to_pantry(current_user.id, item.ingredient_id, item.quantity, item.unit)
    db.session.delete(item)
    db.session.commit()

    flash(f'{ingredient_name} added to your Pantry! ✅', 'success')
    return redirect(url_for('shopping.shopping'))


@shopping_bp.route("/shopping/checkout", methods=["POST"])
@login_required
def checkout_shopping_list():
    shopping_items = ShoppingListItem.query.filter_by(user_id=current_user.id).all()

    if not shopping_items:
        flash('Your Shopping List is empty.', 'error')
        return redirect(url_for('shopping.shopping'))

    order = Order(user_id=current_user.id)
    db.session.add(order)

    for item in shopping_items:
        add_quantity_to_pantry(current_user.id, item.ingredient_id, item.quantity, item.unit)
        db.session.add(OrderItem(
            order=order,
            ingredient_id=item.ingredient_id,
            quantity=item.quantity,
            unit=item.unit
        ))
        db.session.delete(item)

    db.session.commit()

    flash('Shopping List added to your Pantry! ✅', 'success')
    return redirect(url_for('orders.orders'))
