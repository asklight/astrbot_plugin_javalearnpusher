from xlin_pusher.formatter import format_card_message, format_status, truncate_text
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

    assert "小林 Coding 学习卡片" in message
    assert "[网络]" in message
    assert "TCP" in message
    assert "What is the purpose" in message
    assert "It confirms both sides" in message
    assert "https://www.xiaolincoding.com/network/1_base/tcp.html" in message
    assert "配图数量：1" in message


def test_format_status_is_chinese_and_mentions_local_storage():
    status = format_status(
        total_cards=0,
        due_cards=0,
        enabled=False,
        push_time="09:00",
        target_session="",
        last_push_date="",
        cards_path="cards.json",
        last_import_at="",
    )

    assert "小林 Coding 推送状态" in status
    assert "题库数量：0" in status
    assert "今日待复习：0" in status
    assert "定时推送：未启用" in status
    assert "推送目标：未设置" in status
    assert "上次推送日期：从未推送" in status
    assert "上次导入：尚未导入" in status
    assert "数据模式：本地题库（推送时不重新抓取）" in status
    assert "Xiaolincoding Pusher Status" not in status
    assert "Cards:" not in status
    assert "disabled" not in status
