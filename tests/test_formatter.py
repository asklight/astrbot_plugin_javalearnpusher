from xlin_pusher.formatter import format_card_message, truncate_text
from xlin_pusher.models import LearningCard


def test_truncate_text_keeps_short_text_unchanged():
    assert truncate_text("short text", 20) == "short text"


def test_truncate_text_limits_long_text_with_suffix():
    text = "a" * 20
    assert truncate_text(text, 10) == "aaaaaaa..."


def test_format_card_message_includes_source_and_content():
    card = LearningCard(
        id="network-tcp",
        source_url="https://www.xiaolincoding.com/network/1_base/tcp.html",
        category="network",
        title="TCP",
        section="TCP three-way handshake",
        prompt="What is the purpose of TCP three-way handshake?",
        content="It confirms both sides can send and receive data.",
        images=["https://cdn.example.com/tcp.png"],
        tags=["network", "tcp"],
    )

    message = format_card_message(card, max_content_length=200)

    assert "Xiaolincoding Learning Card" in message
    assert "TCP" in message
    assert "What is the purpose" in message
    assert "It confirms both sides" in message
    assert "https://www.xiaolincoding.com/network/1_base/tcp.html" in message
    assert "Images: 1" in message
