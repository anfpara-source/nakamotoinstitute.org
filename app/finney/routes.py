from flask import render_template

from app import cache, db
from app.finney import bp
from app.models import Author


@bp.route("/", methods=["GET"])
@cache.cached()
def index():
    author = db.session.scalar(db.select(Author).filter_by(slug="hal-finney"))
    docs = author.docs.all()
    return render_template("finney/index.html", docs=docs)
