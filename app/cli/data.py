import json
import os.path
from datetime import datetime

import click
import sqlalchemy as sa
from flask import Blueprint
from flask.cli import with_appcontext

from app import db, pages
from app.cli.skeptics import fetch_prices, update_skeptics
from app.cli.utils import DONE, color_text
from app.models import (
    Author,
    BlogPost,
    BlogPostTranslation,
    BlogSeries,
    Category,
    Doc,
    Email,
    EmailThread,
    Episode,
    Format,
    ForumThread,
    Language,
    Post,
    Price,
    Quote,
    QuoteCategory,
    ResearchDoc,
    Skeptic,
    Translator,
)
from app.utils.pages import get_mempool_post

bp = Blueprint("data", __name__)

bp.cli.help = "Update database."


def get_file_contents(filepath):
    with open(filepath) as data_file:
        return json.load(data_file)


def write_file_contents(content, filepath):
    with open(filepath, "w") as f:
        json.dump(content, f, indent=4)


def model_exists(model_class):
    engine = db.get_engine()
    insp = sa.inspect(engine)
    return insp.has_table(model_class.__tablename__)


def get(model, **kwargs):
    return db.session.scalar(db.select(model).filter_by(**kwargs))


# See if object already exists for uniqueness
def get_or_create(model, **kwargs):
    instance = get(model, **kwargs)
    if instance:
        return instance
    else:
        return model(**kwargs)


def string_to_date(s):
    return datetime.strptime(s, "%Y-%m-%d")


def string_to_datetime(s, tz=False):
    dt_format = "%Y-%m-%dT%H:%M:%S"
    if tz:
        dt_format += "%z"
    return datetime.strptime(s, dt_format)


def flush_db():
    click.echo("Initializing database...", nl=False)
    db.drop_all()
    db.create_all()
    click.echo(DONE)


def export_prices_to_file():
    prices = db.session.scalars(db.select(Price))
    serialized_prices = [price.serialize() for price in prices]
    write_file_contents(serialized_prices, "data/prices.json")


def export_prices():
    if not model_exists(Price):
        return
    click.echo("Exporting Prices...", nl=False)
    export_prices_to_file()
    click.echo(DONE)


def import_prices():
    click.echo("Importing Prices...", nl=False)
    fname = "data/prices.json"
    if os.path.isfile(fname):
        prices = get_file_contents(fname)
        if prices:
            for price in prices:
                price["date"] = string_to_date(price["date"])
                new_price = Price(**price)
                db.session.add(new_price)
            db.session.commit()
        else:
            fetch_prices()
    else:
        fetch_prices()


def import_language():
    click.echo("Importing Language...", nl=False)
    languages = get_file_contents("data/languages.json")
    for language in languages:
        new_language = Language(**language)
        db.session.add(new_language)
    db.session.commit()
    click.echo(DONE)


def import_translator():
    click.echo("Importing Translator...", nl=False)
    translators = get_file_contents("data/translators.json")
    for translator in translators:
        new_translator = Translator(**translator)
        db.session.add(new_translator)
    db.session.commit()
    click.echo(DONE)


def import_email_thread():
    click.echo("Importing EmailThread...", nl=False)
    threads = get_file_contents("data/threads_emails.json")
    for thread in threads:
        new_thread = EmailThread(**thread)
        db.session.add(new_thread)
    db.session.commit()
    click.echo(DONE)


def import_email():
    click.echo("Importing Email...", nl=False)
    emails = get_file_contents("data/emails.json")

    for email in emails:
        email.pop("original_date", None)
        email["date"] = string_to_datetime(email["date"])
        parent = email.get("parent", None)
        if parent:
            email["parent"] = db.session.get(Email, parent)
        new_email = Email(**email)
        db.session.add(new_email)
    db.session.commit()
    click.echo(DONE)


def import_forum_thread():
    click.echo("Importing ForumThread...", nl=False)
    threads = get_file_contents("data/threads_forums.json")
    for thread in threads:
        thread.pop("num_satoshi", None)
        new_thread = ForumThread(**thread)
        db.session.add(new_thread)
    db.session.commit()
    click.echo(DONE)


def import_post():
    click.echo("Importing Post...", nl=False)
    posts = get_file_contents("data/posts.json")

    for i, post in enumerate(posts, start=1):
        post["date"] = string_to_datetime(post["date"])
        new_post = Post(id=i, **post)
        db.session.add(new_post)
    db.session.commit()
    click.echo(DONE)


def import_quote_category():
    click.echo("Importing QuoteCategory...", nl=False)
    quote_categories = get_file_contents("data/quotecategories.json")
    for quote_category in quote_categories:
        new_quote_category = QuoteCategory(**quote_category)
        db.session.add(new_quote_category)
    db.session.commit()
    click.echo(DONE)


def import_quote():
    click.echo("Importing Quote...", nl=False)
    quotes = get_file_contents("data/quotes.json")
    for i, quote in enumerate(quotes, start=1):
        quote["date"] = string_to_date(quote["date"])
        quote["categories"] = [
            get(QuoteCategory, slug=category) for category in quote["categories"]
        ]
        new_quote = Quote(id=i, **quote)
        db.session.add(new_quote)
    db.session.commit()
    click.echo(DONE)


def import_author():
    click.echo("Importing Author...", nl=False)
    authors = get_file_contents("data/authors.json")
    for i, author in enumerate(authors, start=1):
        new_author = Author(id=i, **author)
        db.session.add(new_author)
    db.session.commit()
    click.echo(DONE)


def import_doc():
    click.echo("Importing Doc...", nl=False)
    docs = get_file_contents("data/literature.json")
    for doc in docs:
        doc["authors"] = [get(Author, slug=author) for author in doc["authors"]]
        doc["formats"] = [
            get_or_create(Format, name=_format) for _format in doc["formats"]
        ]
        doc["categories"] = [
            get_or_create(Category, name=category) for category in doc["categories"]
        ]
        doc["external"] = doc.get("external", None)
        new_doc = Doc(**doc)
        db.session.add(new_doc)
    db.session.commit()
    click.echo(DONE)


def import_research_doc():
    click.echo("Importing ResearchDoc...", nl=False)
    docs = get_file_contents("data/research.json")
    for doc in docs:
        doc["authors"] = [get(Author, slug=author) for author in doc["authors"]]
        doc["formats"] = [
            get_or_create(Format, name=_format) for _format in doc["formats"]
        ]
        doc["categories"] = [
            get_or_create(Category, name=category) for category in doc["categories"]
        ]
        doc["external"] = doc.get("external", None)
        doc["lit_id"] = doc.get("lit_id", None)
        new_doc = ResearchDoc(**doc)
        db.session.add(new_doc)
    db.session.commit()
    click.echo(DONE)


def import_blog_series():
    click.echo("Importing BlogSeries...", nl=False)
    blog_series_data = get_file_contents("data/blogseries.json")
    for i, blog_series in enumerate(blog_series_data, start=1):
        new_blog_series = BlogSeries(id=i, **blog_series)
        db.session.add(new_blog_series)
    db.session.commit()
    click.echo(DONE)


def import_blog_post():
    click.echo("Importing BlogPost...", nl=False)
    english_posts = []
    translated_posts = []
    for post in pages.get("mempool"):
        if "." in post:
            translated_posts.append(post)
        else:
            english_posts.append(post)

    for i, post in enumerate(english_posts, start=1):
        page = get_mempool_post(post)
        meta = page.meta
        meta_keys = ["title", "date", "added", "excerpt"]
        blog_post_data = {key: meta[key] for key in meta_keys}
        blog_post_data["slug"] = post
        blog_post_data["author"] = [get(Author, slug=meta["author"])]
        series = meta.get("series", None)
        if series:
            blog_post_data["series"] = get(BlogSeries, slug=series)
            blog_post_data["series_index"] = meta["series_index"]
        new_blog_post = BlogPost(id=i, **blog_post_data)
        db.session.add(new_blog_post)
    db.session.commit()

    for post in translated_posts:
        slug, lang = post.split(".")
        page = get_mempool_post(slug, lang=lang)
        meta = page.meta
        post_translation = BlogPostTranslation(
            language=get(Language, ietf=lang),
            translators=[
                get(Translator, slug=translator) for translator in meta["translators"]
            ],
        )
        blog_post = get(BlogPost, slug=slug)
        blog_post.translations.append(post_translation)
        db.session.add(blog_post)
    db.session.commit()
    click.echo(DONE)


def import_skeptic():
    click.echo("Importing Skeptic...", nl=False)
    skeptics = get_file_contents("data/skeptics.json")
    for i, skeptic in enumerate(skeptics, start=1):
        skeptic["date"] = string_to_date(skeptic["date"])
        skeptic["slug"] = f"{skeptic['slug']}-{skeptic['date']}"
        new_skeptic = Skeptic(id=i, **skeptic)
        db.session.add(new_skeptic)
    db.session.commit()
    click.echo(DONE)
    update_skeptics()


def import_episode():
    click.echo("Importing Episode...", nl=False)
    episodes = get_file_contents("data/episodes.json")
    for episode in episodes:
        episode["datetime"] = string_to_datetime(episode["datetime"], tz=True)
        new_episode = Episode(**episode)
        db.session.add(new_episode)
    db.session.commit()
    click.echo(DONE)


@bp.cli.command()
@with_appcontext
def seed():
    """Initialize and seed database."""
    export_prices()
    flush_db()
    import_language()
    import_translator()
    import_email_thread()
    import_email()
    import_forum_thread()
    import_post()
    import_quote_category()
    import_quote()
    import_author()
    import_doc()
    import_research_doc()
    import_blog_series()
    import_blog_post()
    import_prices()
    import_skeptic()
    import_episode()
    click.echo(color_text("Finished importing data!"))
