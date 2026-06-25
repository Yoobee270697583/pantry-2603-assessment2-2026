from flask import Blueprint, request, render_template, redirect, flash, url_for
from flask_login import current_user, login_required
from models import PantryItem, Ingredient, db
from constants import PANTRY_CATEGORY_CHOICES, CATEGORY_LABELS
from forms import AddPantryItemForm, DeletePantryItemForm

pantry_bp = Blueprint("pantry", __name__)


@pantry_bp.route("/pantry")
@login_required
def pantry():
    active_tab = request.args.get("tab", "pantry")
    pantry_items = []
    search_query = ""
    selected_category = ""

    api_ingredients = []
    ingredient_search_query = ""
    ingredient_error = ""

    delete_form = DeletePantryItemForm()

    if active_tab == "pantry":
        search_query = request.args.get("q", "").strip()
        selected_category = request.args.get("category", "").strip()

        query = PantryItem.query.filter_by(owner=current_user)

        if search_query:
            query = query.join(Ingredient).filter(Ingredient.name.ilike(f"%{search_query}%"))

        if selected_category:
            query = query.filter(PantryItem.category == selected_category)

        pantry_items = query.all()

    elif active_tab == "ingredients":
        ingredient_search_query = request.args.get("q", "").strip()

        if ingredient_search_query:
            api_ingredients = Ingredient.query.filter(
                Ingredient.name.ilike(f"%{ingredient_search_query}%")
            ).order_by(Ingredient.name.asc()).all()
            if len(api_ingredients) == 0:
                ingredient_error = f"no ingredients found for '{ingredient_search_query}'"

    return render_template(
        "pantry.html",
        active_page="pantry",
        active_tab=active_tab,
        pantry_items=pantry_items,
        form=delete_form,
        search_query=search_query,
        selected_category=selected_category,
        selected_category_label=CATEGORY_LABELS.get(selected_category, selected_category),
        category_choices=PANTRY_CATEGORY_CHOICES,
        api_ingredients=api_ingredients,
        ingredient_search_query=ingredient_search_query,
        ingredient_error=ingredient_error,
    )


@pantry_bp.route("/add_pantry_item", methods=['GET', 'POST'])
@login_required
def add_pantry_item():
    form = AddPantryItemForm()

    if request.method == "GET":
        ingredient_id = request.args.get("ingredient_id", "")
        form.ingredient_id.data = ingredient_id

    ingredient = None
    if form.ingredient_id.data:
        try:
            ingredient = Ingredient.query.get(int(form.ingredient_id.data))
        except (TypeError, ValueError):
            ingredient = None

    if ingredient is None:
        flash("Pick an ingredient from the Ingredients tab to add it to your pantry.", "error")
        return redirect(url_for("pantry.pantry", tab="ingredients"))

    if form.validate_on_submit():
        new_pantry_item = PantryItem(
            ingredient_id=ingredient.id,
            quantity=form.quantity.data,
            category=form.category.data,
            unit=form.unit.data,
            expiry_date = form.expiry_date.data,
            owner=current_user)
        try:
            db.session.add(new_pantry_item)
            db.session.commit()
            flash('Pantry item added successfully! ✅')
            return redirect(url_for('pantry.pantry'))  # redirect after success
        except Exception:
            db.session.rollback()
            flash('Something went wrong adding the pantry item. Please try again.', 'error')
    else:
        print("FORM ERRORS:", form.errors)
    return render_template("add_pantry_item.html", form=form, ingredient=ingredient, active_page="pantry")


@pantry_bp.route("/pantry/delete/<int:item_id>", methods=["POST"])
def delete_pantry_item(item_id):
    item = PantryItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("pantry.pantry"))


@pantry_bp.route("/pantry/edit/<int:item_id>", methods=["GET", "POST"])
def edit_pantry_item(item_id):
    item = PantryItem.query.get_or_404(item_id)
    form = AddPantryItemForm(obj=item)
    form.ingredient_id.data = item.ingredient_id

    if form.validate_on_submit():
        item.quantity = form.quantity.data
        item.category = form.category.data
        item.unit = form.unit.data
        item.expiry_date = form.expiry_date.data
        db.session.commit()
        return redirect(url_for('pantry.pantry'))
    return render_template('edit_pantry_item.html', form=form, item=item, active_page="pantry")
