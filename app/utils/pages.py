from app import pages


def get_mempool_post(slug, lang="en"):
    if lang == "en":
        return pages.get("mempool", slug)
    return pages.get("mempool", f"{slug}.{lang}")


def get_literature_doc(slug):
    return pages.get("literature", slug)


def get_research_doc(slug):
    return pages.get("research", slug)


def get_podcast_episode(slug):
    return pages.get("podcast", slug)
