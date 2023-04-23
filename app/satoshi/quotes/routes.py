from flask import render_template, request
from sqlalchemy import desc

from app import cache, db
from app.models import Quote, QuoteCategory
from app.satoshi.quotes import bp


@bp.route("/")
@cache.cached()
def index():
    categories = db.session.scalars(
        db.select(QuoteCategory).order_by(QuoteCategory.slug)
    )
    return render_template("satoshi/quotes/index.html", categories=categories)


@bp.route("/<string:slug>/")
@cache.cached()
def detail_category(slug):
    order = request.args.get("order")
    category = db.first_or_404(db.select(QuoteCategory).filter_by(slug=slug))
    if order == "desc":
        quotes = category.quotes.order_by(desc(Quote.date))
    else:
        quotes = category.quotes.order_by(Quote.date)
    return render_template(
        "satoshi/quotes/detail_category.html",
        quotes=quotes,
        category=category,
        order=order,
    )
