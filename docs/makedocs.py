import logging
import os
import re
import sys
import time
from os.path import getmtime
from pathlib import Path
from typing import Callable, Optional, Union

import requests
import yaml
from frontmatter import Frontmatter
from jinja2 import BaseLoader, Environment, TemplateNotFound, select_autoescape
from watchdog.events import (
    DirModifiedEvent,
    FileModifiedEvent,
    FileSystemEventHandler,
    LoggingEventHandler,
)
from watchdog.observers import Observer


WATCH = "-w" in sys.argv
"""Watch for changes"""

DOTFILES_DIR = os.environ.get("DOTFILES_DIR")
if not DOTFILES_DIR:
    raise EnvironmentError("$DOTFILES_DIR is not set.")
else:
    DOTFILES_DIR = Path(DOTFILES_DIR)

DOCS_DIR = DOTFILES_DIR / "docs"
ROOT = os.environ.get("DOCS_ROOT", "/docs")
MANPAGES = [
    DOCS_DIR / "man" / (p + ".1.html")
    for p in [
        "dot",
        "dot-ln",
        "dot-rm",
        "dot-sync",
        "dot-manage",
        "dot-unmanage",
        "dot-adopt",
        "dot-orphan",
        "dot-list",
        "dot-edit",
        "dot-cat",
        "dot-mod",
        "dot-git",
    ]
]


class TemplateLoader(BaseLoader):
    def __init__(self, path: Path):
        self.path = path.resolve()
        # print(self.path)

    def get_source(self, _: Environment, template: str) -> tuple[str, Path, Callable[[], bool]]:
        # path = join(self.path, template)
        p = self.path / template
        if not p.exists():
            raise TemplateNotFound(template)
        mtime = getmtime(p)
        with open(p) as f:
            source, __ = extract_frontmatter(f.read())

        # converted = markdown.markdown(source)

        return source, p, lambda: mtime == getmtime(p)


class RenderEventHandler(FileSystemEventHandler):
    def __init__(self) -> None:
        self.leh = LoggingEventHandler()
        super().__init__()

    def on_modified(self, event: Union[DirModifiedEvent, FileModifiedEvent]) -> None:
        p = Path(str(event.src_path))
        if p.suffix in [".jinja", ".css"]:
            print(f"{p.name} was saved, rendering")
            render()
        else:
            print(f"{p.name} was updated")
        # if p.suffix not in ['.jinja', '.css']:
        #     print('no')
        # else:
        #     render()
        #     print('yes')
        #     return super().on_modified(event)


def render_markdown(source: str):
    """
    Yes, this is just a wrapper around GitHub's Markdown rendering API. The `markdown` Python module sucked.
    """
    response = requests.post(
        "https://api.github.com/markdown",
        headers={
            "Accept": "text/html",
            "X-GitHub-Api-Version": "2026-03-10",
        },
        json={"text": source, "mode": "gfm"},
    )
    if response.status_code != 200:
        raise Exception("Api request failed")
    return str(response.content, encoding="utf-8")


def extract_frontmatter(source: str, loads: Callable = yaml.safe_load) -> tuple[str, Optional[str]]:
    if source.startswith("---\n"):
        frontmatter_end = source.find("\n---\n", 4)
        if frontmatter_end == -1:
            frontmatter = source[4:]
            source = ""
        else:
            frontmatter = source[4:frontmatter_end]
            source = source[frontmatter_end + 5 :]
        if loads:
            frontmatter = loads(frontmatter)
        return source, frontmatter
    return source, None


tl = TemplateLoader(DOCS_DIR)
env = Environment(
    loader=tl,
    autoescape=select_autoescape(),
)


# region Manpages links

manpages_text = ["<details>", "<summary>Expand to see links</summary>", "<ul>"]
for mp in MANPAGES:
    parts = mp.stem.split(".")
    # print(parts)
    with open(mp, "r") as f:
        # print(mp)
        pattern = r"<title>([A-Za-z0-9,\x39\.\-\(\)\$\/&;# ]+)</title>"
        try:
            desc = str(
                re.findall(
                    pattern,
                    f.read(),
                )[0].split(" - ")[1]
            )
        except IndexError:
            desc = ""
    # print(desc)
    s = f'<li><a href="{mp!s}">{parts[0]}({parts[1]})</a> &mdash; {desc}</li>'
    # s = f'- [{parts[0]}({parts[1]})]({mp!s}) &mdash; {desc}'
    manpages_text.append(s)
manpages_text += [
    "</ul>",
    "</details>",
]

# endregion


# Copy over readme content
with open(DOCS_DIR.parent / "README.md", "r") as f:
    c = f.read()

_search_term_main = "## New dotfile manager"
idx_readme_start = c.find(_search_term_main)

_search_term_mods = "## Mods"
idx_mods_start = c.find(_search_term_mods)

_search_term_see_mods = "#mods"
idx_see_mods_start = c.find(_search_term_see_mods)
idx_see_mods_end = idx_see_mods_start + len(_search_term_see_mods)

# Grab the content slices
readme_content = (
    c[idx_readme_start + len(_search_term_main) : idx_see_mods_start]
    + "mods.md"
    + c[idx_see_mods_end:idx_mods_start]
)

mods_content = c[idx_mods_start + len(_search_term_mods) :].strip()


def render():
    # Index template
    index_fm = Frontmatter.read_file(DOCS_DIR / "index.md.jinja")
    index_rendered = env.get_template("index.md.jinja").render(
        manpages="\n".join(manpages_text),
        readme=render_markdown(readme_content),
        root=ROOT,
        page_title=index_fm["attributes"].get("page_title", "index.md"),
    )
    (DOCS_DIR / "index.html").write_text(index_rendered)

    # Mods template
    mods_fm = Frontmatter.read_file(DOCS_DIR / "mods.md.jinja")
    mods_rendered = env.get_template("mods.md.jinja").render(
        mods=render_markdown(mods_content),
        root=ROOT,
        page_title=mods_fm["attributes"].get("page_title", "mods.md"),
    )
    (DOCS_DIR / "mods.html").write_text(mods_rendered)


def observe(observer):
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    return observer.join()


if WATCH:
    print("Watching for changes in docs/ ... (Ctrl+C to stop) ")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    event_handler = RenderEventHandler()
    observer = Observer()
    observer.schedule(event_handler, str(DOCS_DIR), recursive=True)
    try:
        render()
        observe(observer)
    except Exception as e:
        print(e)
        observer.stop()
        observe(observer)

else:
    render()
