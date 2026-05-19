from xlin_pusher.crawler import (
    discover_same_site_links,
    discover_sitemap_links,
    jina_markdown_url,
    parse_html_cards,
    parse_markdown_cards,
)


def test_jina_markdown_url_uses_http_proxy_format():
    assert (
        jina_markdown_url("https://www.xiaolincoding.com/network/")
        == "https://r.jina.ai/http://www.xiaolincoding.com/network/"
    )


def test_discovers_only_xiaolincoding_article_links():
    html = """
    <a href="/network/1_base/tcp.html">tcp</a>
    <a href="https://www.xiaolincoding.com/mysql/index.html">mysql</a>
    <a href="https://example.com/nope.html">external</a>
    <a href="#section">anchor</a>
    <a href="/about/">about</a>
    """

    links = discover_same_site_links(html, "https://www.xiaolincoding.com/")

    assert links == [
        "https://www.xiaolincoding.com/mysql/index.html",
        "https://www.xiaolincoding.com/network/1_base/tcp.html",
    ]


def test_parse_markdown_cards_splits_sections_and_images():
    markdown = """
Title: TCP
URL Source: https://www.xiaolincoding.com/network/1_base/tcp.html

Markdown Content:
# TCP

Intro paragraph that should not become a card.

## TCP basics

TCP is reliable.
![tcp](https://cdn.xiaolincoding.com/tcp.png)

### Why three-way handshake?

It confirms both sides can send and receive data.

## Empty
"""

    cards = parse_markdown_cards(
        markdown,
        source_url="https://www.xiaolincoding.com/network/1_base/tcp.html",
        category="network",
    )

    assert [card.section for card in cards] == ["TCP basics", "Why three-way handshake?"]
    assert cards[0].images == ["https://cdn.xiaolincoding.com/tcp.png"]
    assert cards[1].prompt == "Why three-way handshake?"


def test_discovers_sitemap_article_links():
    xml = """
    <urlset>
      <url><loc>https://www.xiaolincoding.com/network/1_base/tcp.html</loc></url>
      <url><loc>https://www.xiaolincoding.com/about/</loc></url>
      <url><loc>https://www.xiaolincoding.com/interview/java.html</loc></url>
    </urlset>
    """

    links = discover_sitemap_links(xml)

    assert links == [
        "https://www.xiaolincoding.com/interview/java.html",
        "https://www.xiaolincoding.com/network/1_base/tcp.html",
    ]


def test_parse_html_cards_falls_back_when_markdown_proxy_fails():
    html = """
    <html>
      <head><title>TCP article</title></head>
      <body>
        <main class="vp-doc">
          <h1>TCP</h1>
          <p>Intro paragraph.</p>
          <h2>TCP basics</h2>
          <p>TCP is reliable and ordered.</p>
          <img src="https://cdn.xiaolincoding.com/tcp.png" />
          <h3>Why handshake?</h3>
          <p>It confirms both sides can send and receive data.</p>
        </main>
      </body>
    </html>
    """

    cards = parse_html_cards(
        html,
        source_url="https://www.xiaolincoding.com/network/1_base/tcp.html",
        category="network",
    )

    assert [card.section for card in cards] == ["TCP basics", "Why handshake?"]
    assert cards[0].images == ["https://cdn.xiaolincoding.com/tcp.png"]


def test_parse_html_cards_removes_heading_anchor_marker():
    html = """
    <html>
      <head><title>网络模型</title></head>
      <body>
        <article>
          <h2># 应用层</h2>
          <p>应用层负责给应用程序提供网络服务。</p>
        </article>
      </body>
    </html>
    """

    cards = parse_html_cards(
        html,
        source_url="https://www.xiaolincoding.com/network/1_base/tcp_ip_model.html",
        category="network",
    )

    assert cards[0].section == "应用层"
