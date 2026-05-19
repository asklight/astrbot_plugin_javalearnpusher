from datetime import date, datetime

from xlin_pusher.models import LearningCard, ScheduleState
from xlin_pusher.scheduler import is_valid_push_time, should_push_now
from xlin_pusher.store import CardStore, compute_interval


def make_card(
    card_id: str, *, next_review: str | None = None, category: str = "java"
) -> LearningCard:
    return LearningCard(
        id=card_id,
        source_url=f"https://www.xiaolincoding.com/{card_id}.html",
        category=category,
        title=f"Title {card_id}",
        section="Section",
        prompt=f"Prompt {card_id}",
        content=f"Content {card_id}",
        tags=[category],
        next_review=next_review,
    )


def test_card_store_saves_and_loads_cards(tmp_path):
    store = CardStore(tmp_path)
    store.save_cards([make_card("a"), make_card("b")])

    loaded = store.load_cards()

    assert [card.id for card in loaded] == ["a", "b"]


def test_card_store_saves_import_metadata(tmp_path):
    store = CardStore(tmp_path)
    store.save_import_metadata(card_count=3, source_url="https://www.xiaolincoding.com/")

    metadata = store.load_import_metadata()

    assert metadata["card_count"] == 3
    assert metadata["source_url"] == "https://www.xiaolincoding.com/"
    assert metadata["last_import_at"]


def test_card_store_selects_due_cards_before_future_cards(tmp_path):
    store = CardStore(tmp_path)
    store.save_cards(
        [
            make_card("future", next_review="2099-01-01"),
            make_card("due", next_review="2026-05-20"),
        ]
    )

    selected = store.select_next_card(date(2026, 5, 20))

    assert selected is not None
    assert selected.id == "due"


def test_card_store_finds_topic_by_category_title_and_content(tmp_path):
    store = CardStore(tmp_path)
    store.save_cards(
        [
            make_card("mysql", category="mysql"),
            LearningCard(
                id="redis-lock",
                source_url="https://www.xiaolincoding.com/redis/lock.html",
                category="redis",
                title="Redis distributed lock",
                section="Lock",
                prompt="How does a Redis lock work?",
                content="SET NX PX can create a lock.",
                tags=["redis", "lock"],
            ),
        ]
    )

    selected = store.find_topic_card("distributed")

    assert selected is not None
    assert selected.id == "redis-lock"


def test_validates_push_time():
    assert is_valid_push_time("09:30")
    assert not is_valid_push_time("24:00")
    assert not is_valid_push_time("9:30")


def test_should_push_once_per_day_at_configured_minute():
    state = ScheduleState(
        enabled=True, push_time="08:15", target_session="aiocqhttp:FriendMessage:1"
    )

    assert should_push_now(state, datetime(2026, 5, 20, 8, 15))

    state.last_push_date = "2026-05-20"
    assert not should_push_now(state, datetime(2026, 5, 20, 8, 15))
    assert not should_push_now(state, datetime(2026, 5, 21, 8, 14))


def test_compute_interval_accepts_chinese_review_levels():
    assert compute_interval("不会", 30, 3) == 1
    assert compute_interval("模糊", 10, 3) == 5
    assert compute_interval("掌握", 0, 2) == 7
