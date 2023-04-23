#
# Satoshi Nakamoto Institute (https://nakamotoinstitute.org)
# Copyright 2013 Satoshi Nakamoto Institute
# Licensed under GNU Affero GPL (https://github.com/pierrerochard/SNI-private/blob/master/LICENSE)
#
import os

from flask import (
    abort,
    current_app,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from sqlalchemy import desc

from app import cache, db
from app.main import bp
from app.models import BlogPost, Doc, Price, ResearchDoc, Skeptic
from app.utils.pages import get_literature_doc, get_research_doc


@bp.route("/favicon.ico")
@bp.route("/favicon.ico", subdomain="satoshi")
def favicon():
    return send_from_directory(
        os.path.join(current_app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


@bp.route("/")
@cache.cached()
def index():
    blog_post = db.first_or_404(db.select(BlogPost).order_by(desc(BlogPost.added)))
    return render_template("main/index.html", latest_blog_post=blog_post)


@bp.route("/about/", methods=["GET"])
@cache.cached()
def about():
    return render_template("main/about.html")


@bp.route("/contact/", methods=["GET"])
@cache.cached()
def contact():
    return render_template("main/contact.html")


@bp.route("/events/", methods=["GET"])
@cache.cached()
def events():
    return render_template("main/events.html")


@bp.route("/donate/", methods=["GET"])
@cache.cached()
def donate():
    return render_template("main/donate.html")


@bp.route("/<string:slug>/", methods=["GET"])
@cache.cached()
def doc_view(slug):
    doc = db.session.scalar(db.select(Doc).filter_by(slug=slug))
    if doc:
        formats = [format.name for format in doc.formats]
        if "html" not in formats:
            return redirect(url_for("literature.detail", slug=slug))
        page = get_literature_doc(slug)
        return render_template(
            "literature/doc.html", doc=doc, page=page, doc_type="literature"
        )
    research_doc = db.session.scalar(db.select(ResearchDoc).filter_by(slug=slug))
    if not research_doc:
        abort(404)
    formats = [format.name for format in research_doc.formats]
    if "html" not in formats:
        return redirect(url_for("research.detail", slug=slug))
    page = get_research_doc(slug)
    return render_template(
        "literature/doc.html", doc=research_doc, page=page, doc_type="research"
    )


@bp.route("/the-skeptics/")
@cache.cached()
def skeptics():
    skeptics = db.session.scalars(db.select(Skeptic).order_by(Skeptic.date))
    latest_price = db.session.scalar(db.select(Price).order_by(desc(Price.date)))
    return render_template(
        "main/the_skeptics.html", skeptics=skeptics, last_updated=latest_price.date
    )


@bp.route("/crash-course/", methods=["GET"])
@cache.cached()
def crash_course():
    return render_template("main/crash-course.html")


# Redirect old links
@bp.route("/<string:url_slug>.<string:ext>/")
@cache.cached()
def reroute(url_slug, ext):
    doc = db.session.scalar(db.select(Doc).filter_by(slug=url_slug))
    if doc:
        return redirect(url_for("literature.view", slug=doc.slug, ext=ext))
    research_doc = db.session.scalar(db.select(ResearchDoc).filter_by(slug=url_slug))
    if not research_doc:
        abort(404)
    return redirect(url_for("research.view", slug=research_doc.slug, ext=ext))


@bp.route("/keybase.txt")
@cache.cached()
def keybase():
    return send_from_directory(current_app.static_folder, request.path[1:])
