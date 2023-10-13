import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, g, redirect, request
from flask_caching import Cache
from flask_flatpages import FlatPages
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


db = SQLAlchemy(model_class=Base)
pages = FlatPages()
cache = Cache(
    config={
        "CACHE_TYPE": "filesystem",
        "CACHE_DIR": "cache",
        "CACHE_DEFAULT_TIMEOUT": 1800,
    }
)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.url_map.strict_slashes = False
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    db.init_app(app)
    pages.init_app(app)

    if app.debug:
        cache.init_app(
            app,
            config={
                "CACHE_TYPE": "null",
                "CACHE_DEFAULT_TIMEOUT": 0,
            },
        )
    else:
        cache.init_app(app)

    from sni.authors import authors as authors_bp
    from sni.errors import bp as errors_bp
    from sni.library import library as library_bp
    from sni.mempool import mempool as mempool_bp
    from sni.podcast import bp as podcast_bp
    from sni.satoshi import satoshi as satoshi_bp
    from sni.skeptics import bp as skeptics_bp

    app.register_blueprint(errors_bp)
    app.register_blueprint(satoshi_bp, url_prefix="/api/satoshi")
    app.register_blueprint(authors_bp, url_prefix="/api/authors")
    app.register_blueprint(library_bp, url_prefix="/api/library")
    app.register_blueprint(mempool_bp, url_prefix="/api/mempool")
    app.register_blueprint(skeptics_bp, url_prefix="/api/skeptics")
    app.register_blueprint(podcast_bp, url_prefix="/api/podcast")

    @app.before_request
    def remove_trailing_slash():
        if request.path != "/" and request.path.endswith("/"):
            return redirect(request.path[:-1])

    @app.url_value_preprocessor
    def set_locale(endpoint, values):
        g.locale = request.args.get("locale", "en")

    if not app.debug:
        if not os.path.exists("logs"):
            os.mkdir("logs")
        file_handler = RotatingFileHandler(
            "logs/sni.log", maxBytes=10240, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s " "[in %(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info("SNI startup")

    return app