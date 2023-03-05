import yaml
from markdown_it import MarkdownIt
from markdown_it.renderer import RendererHTML
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.front_matter import front_matter_plugin


class SNIMarkdownRenderer(RendererHTML):
    def __init__(self, *args, **kwargs):
        self._front_matter = None
        super().__init__(*args, **kwargs)

    def front_matter(self, tokens, idx, options, env):
        self._front_matter = yaml.safe_load(tokens[idx].content)
        return self.renderToken(tokens, idx, options, env)


class MDRender:
    @classmethod
    def process_md(cls, md_file_path):
        md = (
            MarkdownIt(
                "commonmark",
                {"breaks": True, "html": True},
                renderer_cls=SNIMarkdownRenderer,
            )
            .use(front_matter_plugin)
            .use(footnote_plugin)
        )
        content = cls._get_md_string(md_file_path)
        html_string = md.render(content)

        return (md.renderer._front_matter, html_string)

    @classmethod
    def _get_md_string(cls, md_file_path):
        with open(md_file_path, "r") as reader:
            md_string = reader.read()
        return md_string
