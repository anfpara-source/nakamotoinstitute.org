from flask import redirect, render_template, url_for

from app import cache, db
from app.literature import bp
from app.models import Doc


@bp.route("/", methods=["GET"])
@cache.cached()
def index():
    docs = db.session.scalars(db.select(Doc).order_by(Doc.id)).all()
    formats = {}
    for doc in docs:
        format_names = [doc_format.name for doc_format in doc.formats]
        formats[doc.slug] = format_names
    return render_template("literature/index.html", docs=docs, formats=formats)


@bp.route("/<string:slug>/", methods=["GET"])
@cache.cached()
def detail(slug):
    doc = db.first_or_404(db.select(Doc).filter_by(slug=slug))
    formats = [doc_format.name for doc_format in doc.formats]
    return render_template(
        "literature/detail.html", doc=doc, formats=formats, is_lit=True
    )


@bp.route("/<int:doc_id>/", methods=["GET"])
@cache.cached()
def detail_id(doc_id):
    doc = db.get_or_404(Doc, doc_id)
    return redirect(url_for("literature.detail", slug=doc.slug))


@bp.route("/<string:slug>/<string:ext>/", methods=["GET"])
@cache.cached()
def view(slug, ext):
    doc = db.first_or_404(db.select(Doc).filter_by(slug=slug))
    formats = [doc_format.name for doc_format in doc.formats]
    if ext not in formats:
        return redirect(url_for("literature.detail", slug=slug))
    elif ext == "html":
        return redirect(url_for("main.doc_view", slug=slug))
    return redirect(url_for("static", filename=f"docs/{slug}.{ext}"))


@bp.route("/<int:doc_id>/<string:ext>/", methods=["GET"])
@cache.cached()
def view_id(doc_id, ext):
    doc = db.get_or_404(Doc, doc_id)
    formats = [doc_format.name for doc_format in doc.formats]
    slug = doc.slug
    if ext not in formats:
        return redirect(url_for("literature.detail", slug=slug))
    elif ext == "html":
        return redirect(url_for("main.doc_view", slug=slug))
    return redirect(url_for("static", filename=f"docs/{slug}.{ext}"))
