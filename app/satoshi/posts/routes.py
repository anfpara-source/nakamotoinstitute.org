from flask import abort, redirect, render_template, request, url_for

from app import cache, db
from app.models import ForumThread, Post
from app.satoshi.posts import bp


@bp.route("/", methods=["GET"])
@cache.cached()
def index():
    posts = db.session.scalars(
        db.select(Post).filter(Post.satoshi_id.isnot(None)).order_by(Post.date)
    )
    return render_template("satoshi/posts/index.html", posts=posts)


@bp.route("/threads/", methods=["GET"])
@cache.cached()
def index_threads():
    threads = db.session.scalars(db.select(ForumThread)).all()
    p2pfoundation_threads = threads[:1]
    bitcointalk_threads = threads[1:]
    return render_template(
        "satoshi/posts/index_threads.html",
        threads=threads,
        p2pfoundation_threads=p2pfoundation_threads,
        bitcointalk_threads=bitcointalk_threads,
        source=None,
    )


@bp.route("/<string:source>/", methods=["GET"])
@cache.cached()
def index_source(source):
    posts = db.session.scalars(
        db.select(Post)
        .filter(Post.satoshi_id.isnot(None))
        .join(ForumThread)
        .filter_by(source=source)
        .order_by(Post.date)
    ).all()
    if len(posts) == 0:
        return redirect(url_for("satoshi.posts.index"))
    return render_template("satoshi/posts/index.html", posts=posts, source=source)


@bp.route("/<string:source>/<int:post_id>/", methods=["GET"])
@cache.cached()
def detail(source, post_id):
    post = db.first_or_404(
        db.select(Post)
        .filter_by(satoshi_id=post_id)
        .join(ForumThread)
        .filter_by(source=source)
    )
    previous_post = db.session.scalar(
        db.select(Post).filter_by(satoshi_id=post_id - 1).join(ForumThread)
    )
    next_post = db.session.scalar(
        db.select(Post).filter_by(satoshi_id=post_id + 1).join(ForumThread)
    )
    return render_template(
        "satoshi/posts/detail.html",
        post=post,
        previous_post=previous_post,
        next_post=next_post,
    )


@bp.route("/<string:source>/threads/", methods=["GET"])
@cache.cached()
def threads(source):
    threads = db.session.scalars(
        db.select(ForumThread).filter_by(source=source).order_by(ForumThread.id)
    ).all()
    if len(threads) == 0:
        return redirect(url_for("satoshi.posts.index", view="threads"))
    return render_template(
        "satoshi/posts/index_threads.html", threads=threads, source=source
    )


@bp.route(
    "/<string:source>/threads/<int:thread_id>/",
    methods=["GET"],
)
@cache.cached()
def detail_thread(source, thread_id):
    view_query = request.args.get("view")
    posts_query = db.select(Post).filter_by(thread_id=thread_id)
    if view_query == "satoshi":
        posts_query = posts_query.filter(Post.satoshi_id.isnot(None))
    posts = db.session.scalars(posts_query).all()
    if len(posts) == 0:
        abort(404)
    thread = posts[0].forum_thread
    if thread.source != source:
        return redirect(
            url_for(
                "satoshi.posts.detail_thread", source=thread.source, thread_id=thread_id
            )
        )
    previous_thread = db.session.scalar(
        db.select(ForumThread).filter_by(id=thread_id - 1)
    )
    next_thread = db.session.scalar(db.select(ForumThread).filter_by(id=thread_id + 1))
    return render_template(
        "satoshi/posts/detail_thread.html",
        posts=posts,
        previous_thread=previous_thread,
        next_thread=next_thread,
    )
