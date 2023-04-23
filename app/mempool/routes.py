from feedgen.feed import FeedGenerator
from flask import make_response, redirect, render_template, url_for
from sqlalchemy import asc, desc

from app import cache, db
from app.mempool import bp
from app.models import BlogPost, Language
from app.utils.pages import get_mempool_post
from app.utils.timetils import date_to_localized_datetime


@bp.route("/", methods=["GET"])
@cache.cached()
def index():
    blog_posts = db.session.scalars(db.select(BlogPost).order_by(desc(BlogPost.added)))
    return render_template("mempool/index.html", blog_posts=blog_posts)


@bp.route("/<string:slug>/", methods=["GET"])
@cache.cached()
def detail(slug):
    # Redirect for new appcoin slug
    if slug == "appcoins-are-fraudulent":
        return redirect(url_for("mempool.detail", slug="appcoins-are-snake-oil"))
    blog_post = db.first_or_404(db.select(BlogPost).filter_by(slug=slug))
    english = db.session.scalar(db.select(Language).filter_by(ietf="en"))
    page = get_mempool_post(slug)
    translations = [translation.language for translation in blog_post.translations]
    translations.sort(key=lambda t: t.name)
    previous_post = next_post = None
    if blog_post.series:
        previous_post = db.session.scalar(
            db.select(BlogPost).filter_by(
                series=blog_post.series, series_index=blog_post.series_index - 1
            )
        )
        next_post = db.session.scalar(
            db.select(BlogPost).filter_by(
                series=blog_post.series, series_index=blog_post.series_index + 1
            )
        )
    return render_template(
        "mempool/detail.html",
        blog_post=blog_post,
        page=page,
        language=english,
        translations=translations,
        previous_post=previous_post,
        next_post=next_post,
    )


@bp.route("/<string:slug>/<string:language>/", methods=["GET"])
@cache.cached()
def detail_translation(slug, language):
    language_lower = language.lower()
    if language_lower == "en":
        return redirect(url_for("mempool.detail", slug=slug))
    elif language != language_lower:
        return redirect(
            url_for("mempool.detail_translation", slug=slug, language=language_lower)
        )
    blog_post = db.first_or_404(db.select(BlogPost).filter_by(slug=slug))
    post_language = db.session.scalar(
        db.select(Language).filter_by(ietf=language_lower)
    )
    if post_language not in [
        translation.language for translation in blog_post.translations
    ]:
        return redirect(url_for("mempool.detail", slug=slug))
    page = get_mempool_post(slug, language)
    rtl = False
    if language in ["ar", "fa", "he"]:
        rtl = True
    translations = [db.session.scalar(db.select(Language).filter_by(ietf="en"))]
    translators = None
    blog_post_translations = blog_post.translations
    blog_post_translations.sort(key=lambda x: x.language.name)
    for translation in blog_post_translations:
        if translation.language.ietf != language_lower:
            translations.append(translation.language)
        else:
            translators = translation.translators
    return render_template(
        "mempool/detail.html",
        blog_post=blog_post,
        page=page,
        language=post_language,
        rtl=rtl,
        translations=translations,
        translators=translators,
    )


@bp.route("/feed/")
@cache.cached()
def feed():
    # Entries are added backwards
    articles = db.session.scalars(db.select(BlogPost).order_by(asc(BlogPost.added)))

    fg = FeedGenerator()
    fg.title("Mempool | Satoshi Nakamoto Institute")
    fg.id("https://nakamotoinstitute.org/mempool/feed/")
    fg.updated(date_to_localized_datetime(articles[0].added))
    fg.link(href="https://nakamotoinstitute.org")
    fg.link(href="https://nakamotoinstitute.org/mempool/feed/", rel="self")
    fg.language("en")

    for article in articles:
        url = url_for("mempool.detail", slug=article.slug, _external=True)
        page = get_mempool_post(article.slug)

        fe = fg.add_entry()
        fe.id(url)
        fe.title(article.title)
        fe.link(href=url)
        fe.updated(date_to_localized_datetime(article.added))
        fe.published(date_to_localized_datetime(article.date))
        fe.author(name=str(article.author[0]))
        fe.content(page.html)

    response = make_response(fg.atom_str(encoding="utf-8", pretty=True))
    response.headers.set("Content-Type", "application/atom+xml")
    return response
