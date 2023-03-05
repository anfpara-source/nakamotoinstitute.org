# Custom version of Flask-FlatPages using markdown-it-py
# https://github.com/Flask-FlatPages/Flask-FlatPages


class Page(object):
    def __init__(self, path, meta, html, folder):
        self.path = path
        self.meta = meta
        self.html = html
        self.folder = folder

    def __getitem__(self, name):
        return self.meta[name]

    def __html__(self):
        return self.html

    def __repr__(self):
        return f"<Page {self.path}>"
