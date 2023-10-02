from typing import List

from flask import jsonify

from app import db
from app.models import QuoteCategory
from app.utils.decorators import response_model

from . import bp
from .schemas import QuoteCategoryDetailResponse, QuoteCategoryResponse


@bp.route("/", methods=["GET"])
@response_model(List[QuoteCategoryResponse])
def get_quote_categories():
    categories = db.session.scalars(
        db.select(QuoteCategory).order_by(QuoteCategory.slug)
    ).all()
    return categories


@bp.route("/<string:slug>", methods=["GET"])
def get_quote_category(slug):
    category = db.first_or_404(db.select(QuoteCategory).filter_by(slug=slug))
    quotes = category.quotes

    response_data = QuoteCategoryDetailResponse(category=category, quotes=quotes)

    return jsonify(response_data.dict())