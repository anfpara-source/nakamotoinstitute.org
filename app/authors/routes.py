from flask import redirect, render_template, url_for

from app import cache, db
from app.authors import bp
from app.models import Author


@bp.route("/", methods=["GET"])
@cache.cached()
def index():
    authors = db.session.scalars(db.select(Author).order_by(Author.last))
    return render_template("authors/index.html", authors=authors)


@bp.route("/<string:slug>/", methods=["GET"])
@cache.cached()
def detail(slug):
    if slug == "satoshi-nakamoto":
        return redirect(url_for("satoshi.index"))
    author = db.first_or_404(db.select(Author).filter_by(slug=slug))
    mempool_posts = author.blogposts.all()
    literature_docs = author.docs.all()
    research_docs = author.researchdocs.all()
    return render_template(
        "authors/detail.html",
        author=author,
        mempool_posts=mempool_posts,
        literature_docs=literature_docs,
        research_docs=research_docs,
    )
