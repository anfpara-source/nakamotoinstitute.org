from flask import abort, redirect, render_template, request, url_for

from app import cache, db
from app.models import Email, EmailThread
from app.satoshi.emails import bp


@bp.route("/", methods=["GET"])
@cache.cached()
def index():
    emails = db.session.scalars(
        db.select(Email).filter(Email.satoshi_id.isnot(None)).order_by(Email.date)
    )
    return render_template("satoshi/emails/index.html", emails=emails)


@bp.route("/threads/", methods=["GET"])
@cache.cached()
def index_threads():
    threads = db.session.scalars(db.select(EmailThread)).all()
    cryptography_threads = threads[:2]
    bitcoin_list_threads = threads[2:]
    return render_template(
        "satoshi/emails/index_threads.html",
        threads=threads,
        cryptography_threads=cryptography_threads,
        bitcoin_list_threads=bitcoin_list_threads,
        source=None,
    )


@bp.route("/<string:source>/", methods=["GET"])
@cache.cached()
def index_source(source):
    emails = db.session.scalars(
        db.select(Email)
        .filter(Email.satoshi_id.isnot(None))
        .join(EmailThread)
        .filter_by(source=source)
        .order_by(Email.date)
    ).all()
    if len(emails) == 0:
        return redirect(url_for("satoshi.emails.index"))
    return render_template("satoshi/emails/index.html", emails=emails, source=source)


@bp.route("/<string:source>/<int:email_id>/", methods=["GET"])
@cache.cached()
def detail(source, email_id):
    email = db.first_or_404(
        db.select(Email)
        .filter_by(satoshi_id=email_id)
        .join(EmailThread)
        .filter_by(source=source)
    )
    previous_email = db.session.scalar(
        db.select(Email).filter_by(satoshi_id=email_id - 1).join(EmailThread)
    )
    next_email = db.session.scalar(
        db.select(Email).filter_by(satoshi_id=email_id + 1).join(EmailThread)
    )
    return render_template(
        "satoshi/emails/detail.html",
        email=email,
        previous_email=previous_email,
        next_email=next_email,
    )


@bp.route("/<string:source>/threads/", methods=["GET"])
@cache.cached()
def threads(source):
    threads = db.session.scalars(
        db.select(EmailThread).filter_by(source=source).order_by(EmailThread.id)
    ).all()
    if len(threads) == 0:
        return redirect(url_for("satoshi.emails.index", view="threads"))
    return render_template(
        "satoshi/emails/index_threads.html", threads=threads, source=source
    )


@bp.route(
    "/<string:source>/threads/<int:thread_id>/",
    methods=["GET"],
)
@cache.cached()
def detail_thread(source, thread_id):
    view_query = request.args.get("view")
    emails_query = db.select(Email).filter_by(thread_id=thread_id)
    if view_query == "satoshi":
        emails_query = emails_query.filter(Email.satoshi_id.isnot(None))
    emails = db.session.scalars(emails_query).all()
    if len(emails) == 0:
        abort(404)
    thread = emails[0].email_thread
    if thread.source != source:
        return redirect(
            url_for(
                "satoshi.emails.detail_thread",
                source=thread.source,
                thread_id=thread_id,
            )
        )
    previous_thread = db.session.scalar(
        db.select(EmailThread).filter_by(id=thread_id - 1)
    )
    next_thread = db.session.scalar(db.select(EmailThread).filter_by(id=thread_id + 1))
    return render_template(
        "satoshi/emails/detail_thread.html",
        emails=emails,
        previous_thread=previous_thread,
        next_thread=next_thread,
    )
