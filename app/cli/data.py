import json
import os.path
from datetime import datetime

import click
import requests
import sqlalchemy as sa
from dateutil import parser
from flask import Blueprint

from app import db
from app.cli.skeptics import API_URL, update_skeptics
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
        for price in prices:
            new_price = Price(
                date=parser.parse(price["date"]),
                price=price["price"],
            )
            db.session.add(new_price)
        db.session.commit()
    else:
        click.echo("Fetching Prices...", nl=False)
        resp = requests.get(API_URL).json()
        click.echo("Adding Prices...", nl=False)
        series = resp["data"]
        for se in series:
            date = parser.parse(se["time"])
            price = se["PriceUSD"]
            new_price = Price(
                date=date,
                price=price,
            )
            db.session.add(new_price)
        db.session.commit()
        export_prices()
    click.echo(DONE)


def import_language():
    click.echo("Importing Language...", nl=False)
    languages = get_file_contents("data/languages.json")

    for language in languages:
        new_language = Language(name=language["name"], ietf=language["ietf"])
        db.session.add(new_language)
    db.session.commit()
    click.echo(DONE)


def import_translator():
    click.echo("Importing Translator...", nl=False)
    translators = get_file_contents("data/translators.json")

    for translator in translators:
        new_translator = Translator(name=translator["name"], url=translator["url"])
        db.session.add(new_translator)
    db.session.commit()
    click.echo(DONE)


def import_email_thread():
    click.echo("Importing EmailThread...", nl=False)
    threads = get_file_contents("data/threads_emails.json")

    for thread in threads:
        new_thread = EmailThread(
            id=thread["id"], title=thread["title"], source=thread["source"]
        )
        db.session.add(new_thread)
    db.session.commit()
    click.echo(DONE)


def import_email():
    click.echo("Importing Email...", nl=False)
    emails = get_file_contents("data/emails.json")

    for e in emails:
        satoshi_id = None
        if "satoshi_id" in e.keys():
            satoshi_id = e["satoshi_id"]
        parent = None
        if "parent" in e.keys():
            parent = db.session.get(Email, e["parent"])
        new_email = Email(
            id=e["id"],
            satoshi_id=satoshi_id,
            url=e["url"],
            subject=e["subject"],
            sent_from=e["sender"],
            date=parser.parse(e["date"]),
            text=e["text"],
            source=e["source"],
            source_id=e["source_id"],
            thread_id=e["thread_id"],
        )
        if parent:
            new_email.parent = parent
        db.session.add(new_email)
    db.session.commit()
    click.echo(DONE)


def import_forum_thread():
    click.echo("Importing ForumThread...", nl=False)
    threads = get_file_contents("data/threads_forums.json")

    for thread in threads:
        new_thread = ForumThread(
            id=thread["id"],
            title=thread["title"],
            url=thread["url"],
            source=thread["source"],
        )
        db.session.add(new_thread)
    db.session.commit()
    click.echo(DONE)


def import_post():
    click.echo("Importing Post...", nl=False)
    posts = get_file_contents("data/posts.json")

    for i, p in enumerate(posts, start=1):
        satoshi_id = None
        if "satoshi_id" in p.keys():
            satoshi_id = p["satoshi_id"]
        post = Post(
            id=i,
            satoshi_id=satoshi_id,
            url=p["url"],
            subject=p["subject"],
            poster_name=p["name"],
            poster_url=p["poster_url"],
            post_num=p["post_num"],
            is_displayed=p["is_displayed"],
            nested_level=p["nested_level"],
            date=parser.parse(p["date"]),
            text=p["content"],
            thread_id=p["thread_id"],
        )
        db.session.add(post)
    db.session.commit()
    click.echo(DONE)


def import_quote_category():
    click.echo("Importing QuoteCategory...", nl=False)
    quote_categories = get_file_contents("data/quotecategories.json")

    for qc in quote_categories:
        quote_category = QuoteCategory(slug=qc["slug"], name=qc["name"])
        db.session.add(quote_category)
    db.session.commit()
    click.echo(DONE)


def import_quote():
    click.echo("Importing Quote...", nl=False)
    quotes = get_file_contents("data/quotes.json")

    for i, quote in enumerate(quotes, start=1):
        q = Quote(
            id=i,
            text=quote["text"],
            date=parser.parse(quote["date"]).date(),
            medium=quote["medium"],
        )
        if "email_id" in quote:
            q.email_id = quote["email_id"]
        if "post_id" in quote:
            q.post_id = quote["post_id"]
        categories = []
        for cat in quote["category"].split(", "):
            categories += [get(QuoteCategory, slug=cat)]
        q.categories = categories
        db.session.add(q)
    db.session.commit()
    click.echo(DONE)


def import_author():
    click.echo("Importing Author...", nl=False)
    authors = get_file_contents("data/authors.json")

    for i, author in enumerate(authors, start=1):
        author = Author(
            id=i,
            first=author["first"],
            middle=author["middle"],
            last=author["last"],
            slug=author["slug"],
        )
        db.session.add(author)
    db.session.commit()
    click.echo(DONE)


def import_doc():
    click.echo("Importing Doc...", nl=False)
    docs = get_file_contents("data/literature.json")

    for doc in docs:
        authorlist = doc["author"]
        dbauthor = []
        for auth in authorlist:
            dbauthor += [get(Author, slug=auth)]
        formlist = doc["formats"]
        dbformat = []
        for form in formlist:
            dbformat += [get_or_create(Format, name=form)]
        catlist = doc["categories"]
        dbcat = []
        for cat in catlist:
            dbcat += [get_or_create(Category, name=cat)]
        if "external" in doc:
            ext = doc["external"]
        else:
            ext = None
        doc = Doc(
            id=doc["id"],
            title=doc["title"],
            author=dbauthor,
            date=doc["date"],
            slug=doc["slug"],
            formats=dbformat,
            categories=dbcat,
            doctype=doc["doctype"],
            external=ext,
        )
        db.session.add(doc)
    db.session.commit()
    click.echo(DONE)


def import_research_doc():
    click.echo("Importing ResearchDoc...", nl=False)
    docs = get_file_contents("data/research.json")

    for doc in docs:
        authorlist = doc["author"]
        dbauthor = []
        for auth in authorlist:
            dbauthor += [get(Author, slug=auth)]
        formlist = doc["formats"]
        dbformat = []
        for form in formlist:
            dbformat += [get_or_create(Format, name=form)]
        catlist = doc["categories"]
        dbcat = []
        for cat in catlist:
            dbcat += [get_or_create(Category, name=cat)]
        if "external" in doc:
            ext = doc["external"]
        else:
            ext = None
        if "lit_id" in doc:
            lit = doc["lit_id"]
        else:
            lit = None
        doc = ResearchDoc(
            id=doc["id"],
            title=doc["title"],
            author=dbauthor,
            date=doc["date"],
            slug=doc["slug"],
            formats=dbformat,
            categories=dbcat,
            doctype=doc["doctype"],
            external=ext,
            lit_id=lit,
        )
        db.session.add(doc)
    db.session.commit()
    click.echo(DONE)


def import_blog_series():
    click.echo("Importing BlogSeries...", nl=False)
    blog_series = get_file_contents("data/blogseries.json")

    for i, blogs in enumerate(blog_series, start=1):
        blog_series = BlogSeries(
            id=i,
            title=blogs["title"],
            slug=blogs["slug"],
            chapter_title=blogs["chapter_title"],
        )
        db.session.add(blog_series)
    db.session.commit()
    click.echo(DONE)


def import_blog_post():
    click.echo("Importing BlogPost...", nl=False)
    blog_posts = get_file_contents("data/blogposts.json")

    for i, bp in enumerate(blog_posts, start=1):
        blogpost = BlogPost(
            id=i,
            title=bp["title"],
            author=[get(Author, slug=bp["author"])],
            date=parser.parse(bp["date"]),
            added=parser.parse(bp["added"]),
            slug=bp["slug"],
            excerpt=bp["excerpt"],
        )
        db.session.add(blogpost)
        try:
            blogpost.series = get(BlogSeries, slug=bp["series"])
            blogpost.series_index = bp["series_index"]
        except KeyError:
            pass
        db.session.add(blogpost)
        for lang in bp["translations"]:
            translators = bp["translations"][lang]
            dbtranslator = []
            for translator in translators:
                dbtranslator += [get(Translator, name=translator)]
            blog_translation = BlogPostTranslation(
                language=get(Language, ietf=lang),
                translators=dbtranslator,
            )
            blogpost.translations.append(blog_translation)
        db.session.add(blogpost)
    db.session.commit()
    click.echo(DONE)


def import_skeptic():
    click.echo("Importing Skeptic...", nl=False)
    skeptics = get_file_contents("data/skeptics.json")

    for i, skeptic in enumerate(skeptics, start=1):
        slug_date = datetime.strftime(parser.parse(skeptic["date"]), "%Y-%m-%d")
        try:
            media_embed = skeptic["media_embed"]
        except KeyError:
            media_embed = ""
        try:
            twitter_screenshot = skeptic["twitter_screenshot"]
        except KeyError:
            twitter_screenshot = False
        skeptic = Skeptic(
            id=i,
            name=skeptic["name"],
            title=skeptic["title"],
            article=skeptic["article"],
            date=parser.parse(skeptic["date"]),
            source=skeptic["source"],
            excerpt=skeptic["excerpt"],
            price=skeptic["price"],
            link=skeptic["link"],
            waybacklink=skeptic["waybacklink"],
            media_embed=media_embed,
            twitter_screenshot=twitter_screenshot,
            slug=f"{skeptic['slug']}-{slug_date}",
        )
        db.session.add(skeptic)
    db.session.commit()
    click.echo(DONE)
    update_skeptics()


def import_episode():
    click.echo("Importing Episode...", nl=False)
    episodes = get_file_contents("data/episodes.json")

    for ep in episodes:
        episode = Episode(
            id=ep["id"],
            title=ep["title"],
            date=parser.parse(ep["date"]),
            duration=ep["duration"],
            subtitle=ep["subtitle"],
            summary=ep["summary"],
            slug=ep["slug"],
            youtube=ep["youtube"],
            time=parser.parse(ep["time"]),
        )
        db.session.add(episode)
    db.session.commit()
    click.echo(DONE)


@bp.cli.command()
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
