# Custom version of Flask-FlatPages using markdown-it-py
# https://github.com/Flask-FlatPages/Flask-FlatPages

import os

from flask import abort
from werkzeug.utils import cached_property

from .markdown import MDRender
from .page import Page


class FlatPages(object):
    default_config = (
        ("root", "pages"),
        ("extension", ".html"),
        ("auto_reload", "if debug"),
    )

    def __init__(self, app=None, name=None):
        self.name = name

        if name is None:
            self.config_prefix = "FLATPAGES"
        else:
            self.config_prefix = "_".join(("FLATPAGES", name.upper()))

        self._file_cache = {}

        if app:
            self.init_app(app)

    def __iter__(self):
        return iter(self._pages)

    def config(self, key):
        return self.app.config["_".join((self.config_prefix, key.upper()))]

    def get(self, *args, default=None):
        value = self._pages
        try:
            for key in args:
                value = value[key]
            return value
        except KeyError:
            return default

    def get_or_404(self, path):
        page = self.get(path)
        if not page:
            abort(404)
        return page

    def init_app(self, app):
        for key, value in self.default_config:
            config_key = "_".join((self.config_prefix, key.upper()))
            app.config.setdefault(config_key, value)

        app.before_request(self._conditional_auto_reset)

        if "flatpages" not in app.extensions:
            app.extensions["flatpages"] = {}
        app.extensions["flatpages"][self.name] = self
        self.app = app
        self._pages

    def reload(self):
        try:
            # This will "unshadow" the cached_property.
            # The property will be re-executed on next access.
            del self.__dict__["_pages"]
        except KeyError:
            pass

    @property
    def root(self):
        return os.path.join(self.app.root_path, self.config("root"))

    def _conditional_auto_reset(self):
        auto = self.config("auto_reload")
        if auto == "if debug":
            auto = self.app.debug
        if auto:
            self.reload()

    def _load_file(self, path, filename, rel_path, slug):
        mtime = os.path.getmtime(filename)
        cached = self._file_cache.get(filename)

        if cached and cached[1] == mtime:
            page = cached[0]
        else:
            page = self._parse(filename, rel_path, slug)
            self._file_cache[filename] = (page, mtime)

        return page

    @cached_property
    def _pages(self):
        """
        Walk the page root directory and return a dict of pages.
        Returns a dictionary of pages keyed by their path.
        """

        def _walker():
            """
            Walk over directory and find all possible flatpages.
            Returns files which end with the string or sequence given by
            ``FLATPAGES_%(name)s_EXTENSION``.
            """
            for cur_path, _, filenames in os.walk(self.root):
                rel_path = cur_path.replace(self.root, "").lstrip(os.sep)
                path_prefix = tuple(rel_path.split(os.sep)) if rel_path else ()

                for name in filenames:
                    if not name.endswith(extension):
                        continue

                    full_name = os.path.join(cur_path, name)
                    name_without_extension = [
                        name[: -len(item)] for item in extension if name.endswith(item)
                    ][0]
                    path = "/".join(path_prefix + (name_without_extension,))
                    # if self.config("case_insensitive"):
                    #     path = path.lower()
                    yield (path, full_name, rel_path, name_without_extension)

        # Read extension from config
        extension = self.config("extension")

        # Support for multiple extensions
        if isinstance(extension, str):
            if "," in extension:
                extension = tuple(extension.split(","))
            else:
                extension = (extension,)
        elif isinstance(extension, (list, set)):
            extension = tuple(extension)

        # FlatPage extension should be a string or a sequence
        if not isinstance(extension, tuple):
            raise ValueError(
                "Invalid value for FlatPages extension. Should be a string or "
                "a sequence, got {0} instead: {1}".format(
                    type(extension).__name__, extension
                )
            )
        pages = {}
        for path, full_name, rel_path, name_without_extension in _walker():
            file_path = os.path.normpath(path)
            path_parts = file_path.split(os.path.sep)
            current_level = pages
            for part in path_parts[:-1]:
                current_level = current_level.setdefault(part, {})
            if name_without_extension in current_level:
                raise ValueError(
                    "Multiple pages found which correspond to the same path. "
                    "This error can arise when using multiple extensions."
                )
            current_level[name_without_extension] = self._load_file(
                path, full_name, rel_path, name_without_extension
            )

        return pages

    def _parse(self, path, rel_path, slug):
        """Parse a flatpage file, i.e. read and parse its meta data and body.
        :return: initialized :class:`Page` instance.
        """
        meta, html = MDRender.process_md(path)

        # Assign the relative path (to root) for use in the page object
        folder = rel_path

        # Initialize and return Page instance
        return Page(path, meta, html, folder, slug)
