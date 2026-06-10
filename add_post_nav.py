from __future__ import annotations

import html
import json
from pathlib import Path


ROOT = Path(__file__).parent
SITE_DIR = ROOT / "_site"
LISTINGS_PATH = SITE_DIR / "listings.json"
SEARCH_PATH = SITE_DIR / "search.json"
START_MARKER = "<!-- post-nav:start -->"
END_MARKER = "<!-- post-nav:end -->"


def normalize_item_path(path: str) -> str:
    return path if path.startswith("/") else f"/{path}"


def load_listing_items() -> list[str]:
    listings = json.loads(LISTINGS_PATH.read_text(encoding="utf-8"))
    home_listing = next(
        (entry for entry in listings if entry.get("listing") == "/index.html"),
        None,
    )
    if not home_listing:
        return []
    return [normalize_item_path(item) for item in home_listing.get("items", [])]


def load_titles() -> dict[str, str]:
    search_index = json.loads(SEARCH_PATH.read_text(encoding="utf-8"))
    titles: dict[str, str] = {}
    for entry in search_index:
        href = entry.get("href")
        title = entry.get("title")
        if isinstance(href, str) and isinstance(title, str) and href.startswith("posts/"):
            titles[normalize_item_path(href)] = title
    return titles


def nav_link(current_file: Path, target: str, label: str, arrow: str, class_name: str, titles: dict[str, str]) -> str:
    target_file = SITE_DIR / target.lstrip("/")
    href = html.escape(target_file.relative_to(current_file.parent).as_posix())
    title = html.escape(titles.get(target, target_file.stem))
    return (
        f'<a class="post-nav-link {class_name}" href="{href}">'
        f'<span class="post-nav-meta">{arrow} {label}</span>'
        f'<span class="post-nav-title">{title}</span>'
        "</a>"
    )


def build_nav(current_file: Path, newer: str | None, older: str | None, titles: dict[str, str]) -> str:
    links: list[str] = []
    if newer:
        links.append(nav_link(current_file, newer, "Newer", "&larr;", "post-nav-newer", titles))
    if older:
        links.append(nav_link(current_file, older, "Older", "&rarr;", "post-nav-older", titles))

    if not links:
        return ""

    return (
        f"\n{START_MARKER}\n"
        '<nav class="post-nav" aria-label="Post navigation">\n'
        + "\n".join(links)
        + "\n</nav>\n"
        f"{END_MARKER}\n"
    )


def strip_existing_nav(content: str) -> str:
    if START_MARKER not in content or END_MARKER not in content:
        return content

    start = content.index(START_MARKER)
    end = content.index(END_MARKER) + len(END_MARKER)
    return content[:start] + content[end:]


def main() -> None:
    if not LISTINGS_PATH.exists() or not SEARCH_PATH.exists():
        return

    items = load_listing_items()
    titles = load_titles()

    for index, item in enumerate(items):
        current_file = SITE_DIR / item.lstrip("/")
        if not current_file.exists():
            continue

        newer = items[index - 1] if index > 0 else None
        older = items[index + 1] if index < len(items) - 1 else None
        nav = build_nav(current_file, newer, older, titles)

        content = strip_existing_nav(current_file.read_text(encoding="utf-8"))
        marker = "</main> <!-- /main -->"
        if marker not in content:
            continue

        current_file.write_text(content.replace(marker, nav + marker, 1), encoding="utf-8")


if __name__ == "__main__":
    main()
