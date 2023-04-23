from flask import render_template
from sqlalchemy import desc

from app import cache, db
from app.mempool.series import bp
from app.models import BlogSeries


@bp.route("/")
@cache.cached()
def index():
    series = db.session.scalars(db.select(BlogSeries).order_by(desc(BlogSeries.id)))
    return render_template("mempool/series/index.html", series=series)


@bp.route("/<string:slug>/")
@cache.cached()
def detail(slug):
    series = db.first_or_404(db.select(BlogSeries).filter_by(slug=slug))
    return render_template("mempool/series/detail.html", series=series)
