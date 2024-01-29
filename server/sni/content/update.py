import logging
from contextlib import contextmanager

from sni.authors.importers import AuthorImporter
from sni.database import SessionLocal
from sni.library.importers import LibraryImporter
from sni.mempool.importers import MempoolImporter, MempoolSeriesImporter
from sni.podcast.importers import EpisodeImporter
from sni.satoshi.emails.importers import EmailImporter, EmailThreadImporter
from sni.satoshi.posts.importers import ForumPostImporter, ForumThreadImporter
from sni.satoshi.quotes.importers import QuoteCategoryImporter, QuoteImporter
from sni.skeptics.importers import SkepticImporter
from sni.translators.importers import TranslatorImporter

from .json import run_json_importer


@contextmanager
def session_scope():
    db_session = SessionLocal()
    try:
        yield db_session
        db_session.commit()
    except Exception as e:
        logging.error(f"Error during update: {e}")
        db_session.rollback()
        raise
    finally:
        db_session.close()


def update_content(force: bool = False):
    with session_scope() as db_session:
        # Import emails
        email_thread_updated = run_json_importer(EmailThreadImporter, db_session, force)
        email_updated = run_json_importer(
            EmailImporter, db_session, force, [email_thread_updated]
        )

        # Import forum posts
        forum_thread_updated = run_json_importer(ForumThreadImporter, db_session, force)
        forum_post_updated = run_json_importer(
            ForumPostImporter, db_session, force, [forum_thread_updated]
        )

        # Import quotes
        quote_category_updated = run_json_importer(
            QuoteCategoryImporter, db_session, force
        )
        run_json_importer(
            QuoteImporter,
            db_session,
            force,
            [
                email_thread_updated,
                email_updated,
                forum_thread_updated,
                forum_post_updated,
                quote_category_updated,
            ],
        )

        # Import skeptics
        run_json_importer(SkepticImporter, db_session, force)

    # Import markdown content
    importers = [
        AuthorImporter,
        TranslatorImporter,
        LibraryImporter,
        MempoolSeriesImporter,
        MempoolImporter,
        EpisodeImporter,
    ]
    for importer in importers:
        instance = importer()
        instance.run_import(force)