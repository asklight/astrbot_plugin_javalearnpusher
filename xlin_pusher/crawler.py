from __future__ import annotations

import hashlib
import re
from collections import deque
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urldefrag, urljoin, urlparse

import requests

from .models import LearningCard

DEFAULT_START_URL = "https://www.xiaolincoding.com/"
IMAGE_RE = re.compile(r"!\[[^\]]*]\((https?://[^)\s]+)[^)]*\)")
LINK_RE = re.compile(r"\[([^\]]+)]\((https?://[^)]+)\)")
HEADING_RE = re.compile(r"^(#{1,4})\s+(?:\[[^\]]*]\([^)]*\)\s*)?(.+?)\s*$")
SITEMAP_LOC_RE = re.compile(r"<loc>\s*(https?://[^<]+)\s*</loc>", re.IGNORECASE)


@dataclass(slots=True)
class CrawlResult:
    cards: list[LearningCard]
    visited_urls: list[str]


class _AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        for name, value in attrs:
            if name == "href" and value:
                self.hrefs.append(value)


class _ArticleHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.events: list[tuple[str, str]] = []
        self._tag_stack: list[str] = []
        self._capture_tag = ""
        self._buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        self._tag_stack.append(tag)
        if tag in {"title", "h1", "h2", "h3", "h4", "p", "li"}:
            self._capture_tag = tag
            self._buffer = []
        elif tag == "img":
            for name, value in attrs:
                if name in {"src", "data-src"} and value:
                    self.events.append(("img", value))
                    break

    def handle_data(self, data: str) -> None:
        if self._capture_tag:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._capture_tag == tag:
            text = " ".join("".join(self._buffer).split())
            if text:
                if tag == "title" and not self.title:
                    self.title = text
                elif tag in {"h1", "h2", "h3", "h4", "p", "li"}:
                    self.events.append((tag, text))
            self._capture_tag = ""
            self._buffer = []
        if self._tag_stack and self._tag_stack[-1] == tag:
            self._tag_stack.pop()


def jina_markdown_url(url: str) -> str:
    parsed = urlparse(url)
    target = f"{parsed.netloc}{parsed.path}"
    if parsed.query:
        target = f"{target}?{parsed.query}"
    return f"https://r.jina.ai/http://{target}"


def discover_sitemap_links(xml: str) -> list[str]:
    links: set[str] = set()
    for match in SITEMAP_LOC_RE.findall(xml or ""):
        url = normalize_url(match.strip())
        if _looks_like_article_url(url):
            links.add(url)
    return sorted(links)


def discover_same_site_links(html: str, base_url: str) -> list[str]:
    parser = _AnchorParser()
    parser.feed(html or "")
    links: set[str] = set()
    base_host = urlparse(base_url).netloc.replace("www.", "")
    for href in parser.hrefs:
        absolute = normalize_url(urljoin(base_url, href))
        parsed = urlparse(absolute)
        host = parsed.netloc.replace("www.", "")
        if host != base_host:
            continue
        if not _looks_like_article_url(absolute):
            continue
        links.add(absolute)
    return sorted(links)


def normalize_url(url: str) -> str:
    clean, _ = urldefrag(url)
    parsed = urlparse(clean)
    path = parsed.path or "/"
    return parsed._replace(path=path, query="").geturl()


def fetch_text(url: str, timeout: int = 30) -> str:
    response = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "zh-CN,zh;q=0.9"},
    )
    response.raise_for_status()
    if not response.encoding or response.encoding.lower() in {"iso-8859-1", "latin-1"}:
        response.encoding = "utf-8"
    return response.text


def crawl_xiaolincoding(
    start_url: str = DEFAULT_START_URL,
    *,
    max_pages: int = 80,
    timeout: int = 30,
) -> CrawlResult:
    queue: deque[str] = deque(_initial_urls(start_url, timeout))
    seen: set[str] = set()
    visited: list[str] = []
    cards: list[LearningCard] = []
    card_ids: set[str] = set()

    while queue and len(visited) < max_pages:
        url = queue.popleft()
        if url in seen:
            continue
        seen.add(url)

        try:
            html = fetch_text(url, timeout=timeout)
        except requests.RequestException:
            continue

        visited.append(url)
        for link in discover_same_site_links(html, url):
            if link not in seen:
                queue.append(link)

        if not _looks_like_article_url(url):
            continue

        try:
            markdown = fetch_text(jina_markdown_url(url), timeout=timeout)
            parsed_cards = parse_markdown_cards(
                markdown, source_url=url, category=infer_category(url)
            )
        except requests.RequestException:
            parsed_cards = parse_html_cards(html, source_url=url, category=infer_category(url))

        for card in parsed_cards:
            if card.id in card_ids:
                continue
            card_ids.add(card.id)
            cards.append(card)

    return CrawlResult(cards=cards, visited_urls=visited)


def parse_html_cards(html: str, *, source_url: str, category: str) -> list[LearningCard]:
    parser = _ArticleHTMLParser()
    parser.feed(html or "")
    title = _clean_inline_markdown(parser.title) or _title_from_url(source_url)
    cards: list[LearningCard] = []
    current_heading = ""
    current_level = 0
    buffer: list[str] = []
    images: list[str] = []

    def flush() -> None:
        nonlocal current_heading, current_level, buffer, images
        content = _clean_content(buffer)
        if current_heading and len(content) >= 10:
            cards.append(
                LearningCard(
                    id=stable_card_id(category, source_url, current_heading),
                    source_url=source_url,
                    category=category,
                    title=title,
                    section=current_heading,
                    prompt=_prompt_from_heading(current_heading, title),
                    content=content,
                    images=list(dict.fromkeys(images)),
                    tags=list(
                        dict.fromkeys([category, _slug_text(title), _slug_text(current_heading)])
                    ),
                )
            )
        current_heading = ""
        current_level = 0
        buffer = []
        images = []

    for tag, value in parser.events:
        if tag in {"h1", "h2", "h3", "h4"}:
            if current_heading:
                flush()
            level = int(tag[1])
            if level == 1:
                continue
            current_heading = _clean_inline_markdown(value)
            current_level = level
            continue
        if not current_heading or current_level > 3:
            continue
        if tag == "img":
            images.append(value)
        elif tag in {"p", "li"}:
            cleaned = _clean_inline_markdown(value)
            if cleaned:
                buffer.append(cleaned)

    if current_heading:
        flush()
    return cards


def parse_markdown_cards(markdown: str, *, source_url: str, category: str) -> list[LearningCard]:
    lines = (markdown or "").splitlines()
    title = _extract_title(lines) or _title_from_url(source_url)
    body_start = _markdown_body_start(lines)
    cards: list[LearningCard] = []
    current_heading = ""
    current_level = 0
    buffer: list[str] = []
    images: list[str] = []

    def flush() -> None:
        nonlocal buffer, images, current_heading, current_level
        content = _clean_content(buffer)
        if current_heading and len(content) >= 10:
            card = LearningCard(
                id=stable_card_id(category, source_url, current_heading),
                source_url=source_url,
                category=category,
                title=title,
                section=current_heading,
                prompt=_prompt_from_heading(current_heading, title),
                content=content,
                images=list(dict.fromkeys(images)),
                tags=list(
                    dict.fromkeys([category, _slug_text(title), _slug_text(current_heading)])
                ),
            )
            cards.append(card)
        buffer = []
        images = []
        current_heading = ""
        current_level = 0

    for raw in lines[body_start:]:
        line = raw.strip()
        heading = HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            if current_heading:
                flush()
            if level == 1:
                current_heading = ""
                current_level = 0
                continue
            current_heading = _clean_inline_markdown(heading.group(2))
            current_level = level
            continue

        if not current_heading or current_level > 3:
            continue
        images.extend(IMAGE_RE.findall(raw))
        cleaned = _clean_line(raw)
        if cleaned:
            buffer.append(cleaned)

    if current_heading:
        flush()
    return cards


def stable_card_id(category: str, source_url: str, section: str) -> str:
    digest = hashlib.sha1(f"{source_url}#{section}".encode()).hexdigest()[:10]
    return f"{_slug_text(category)}-{digest}"


def infer_category(url: str) -> str:
    path = urlparse(url).path.strip("/")
    if not path:
        return "home"
    first = path.split("/", 1)[0]
    aliases = {
        "network": "network",
        "os": "system",
        "mysql": "mysql",
        "redis": "redis",
        "interview": "interview",
        "java": "java",
        "go": "go",
        "cpp": "cpp",
    }
    return aliases.get(first.lower(), first.lower())


def _initial_urls(start_url: str, timeout: int) -> list[str]:
    normalized = normalize_url(start_url)
    parsed = urlparse(normalized)
    sitemap_urls = [
        f"{parsed.scheme}://{parsed.netloc}/sitemap.xml",
        "https://xiaolincoding.com/sitemap.xml",
        "https://www.xiaolincoding.com/sitemap.xml",
    ]
    for sitemap_url in dict.fromkeys(sitemap_urls):
        try:
            links = discover_sitemap_links(fetch_text(sitemap_url, timeout=timeout))
        except requests.RequestException:
            continue
        if links:
            return links
    return [normalized]


def _looks_like_article_url(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path
    if any(part in path for part in ("/tag/", "/categories/", "/about", "/reader", "/site")):
        return False
    return path.endswith(".html")


def _extract_title(lines: list[str]) -> str:
    for line in lines[:20]:
        if line.startswith("Title:"):
            return _clean_inline_markdown(line.removeprefix("Title:").strip())
    for line in lines:
        heading = HEADING_RE.match(line.strip())
        if heading:
            return _clean_inline_markdown(heading.group(2))
    return ""


def _markdown_body_start(lines: list[str]) -> int:
    for idx, line in enumerate(lines):
        if line.strip() == "Markdown Content:":
            return idx + 1
    return 0


def _title_from_url(url: str) -> str:
    name = urlparse(url).path.rstrip("/").rsplit("/", 1)[-1]
    return name.removesuffix(".html") or "xiaolincoding"


def _prompt_from_heading(section: str, title: str) -> str:
    if section.endswith("?") or section.endswith("？"):
        return section
    return f"Review: {section or title}"


def _clean_content(lines: list[str]) -> str:
    return "\n".join(line for line in lines if line).strip()


def _clean_line(line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return ""
    if stripped.startswith(("Title:", "URL Source:", "Published Time:")):
        return ""
    if stripped in {"Markdown Content:", "* * *", "---"}:
        return ""
    if IMAGE_RE.fullmatch(stripped):
        return ""
    return _clean_inline_markdown(stripped)


def _clean_inline_markdown(text: str) -> str:
    value = LINK_RE.sub(r"\1", text)
    value = re.sub(r"`([^`]*)`", r"\1", value)
    value = value.replace("**", "").replace("__", "")
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"^#+\s*", "", value)
    return " ".join(value.split()).strip()


def _slug_text(text: str) -> str:
    value = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", text or "").strip("-").lower()
    return value or "card"
