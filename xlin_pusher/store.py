from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from .models import LearningCard, ScheduleState

MASTER_STEPS = [1, 3, 7, 15, 30, 60]


class CardStore:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.cards_path = self.data_dir / "cards.json"
        self.schedule_path = self.data_dir / "schedule.json"

    def ensure_data_dir(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def load_cards(self) -> list[LearningCard]:
        if not self.cards_path.exists():
            return []
        with self.cards_path.open("r", encoding="utf-8") as file:
            raw = json.load(file)
        return [LearningCard.from_dict(item) for item in raw]

    def save_cards(self, cards: list[LearningCard]) -> None:
        self.ensure_data_dir()
        with self.cards_path.open("w", encoding="utf-8") as file:
            json.dump([card.to_dict() for card in cards], file, ensure_ascii=False, indent=2)

    def load_schedule(self) -> ScheduleState:
        if not self.schedule_path.exists():
            return ScheduleState()
        with self.schedule_path.open("r", encoding="utf-8") as file:
            raw = json.load(file)
        return ScheduleState.from_dict(raw)

    def save_schedule(self, state: ScheduleState) -> None:
        self.ensure_data_dir()
        with self.schedule_path.open("w", encoding="utf-8") as file:
            json.dump(state.to_dict(), file, ensure_ascii=False, indent=2)

    def due_cards(self, today: date) -> list[LearningCard]:
        cards = self.load_cards()
        due: list[LearningCard] = []
        for card in cards:
            if _is_due(card.next_review, today):
                due.append(card)
        return due

    def select_next_card(self, today: date) -> LearningCard | None:
        cards = self.load_cards()
        for card in cards:
            if _is_due(card.next_review, today):
                return card
        return cards[0] if cards else None

    def find_topic_card(self, keyword: str) -> LearningCard | None:
        needle = (keyword or "").strip().lower()
        if not needle:
            return None
        for card in self.load_cards():
            haystack = " ".join(
                [
                    card.category,
                    card.title,
                    card.section,
                    card.prompt,
                    card.content,
                    " ".join(card.tags),
                ]
            ).lower()
            if needle in haystack:
                return card
        return None

    def mark_reviewed(self, card_id: str, level: str, today: date) -> LearningCard | None:
        cards = self.load_cards()
        found: LearningCard | None = None
        for card in cards:
            if card.id != card_id:
                continue
            interval = compute_interval(level, card.interval_days, card.review_count)
            card.interval_days = interval
            card.review_count += 1
            card.next_review = (today + timedelta(days=interval)).isoformat()
            card.status = "reviewed"
            found = card
            break
        if found is not None:
            self.save_cards(cards)
        return found


def _is_due(value: str | None, today: date) -> bool:
    if not value:
        return True
    try:
        return date.fromisoformat(value) <= today
    except ValueError:
        return True


def compute_interval(level: str, current_interval: int, review_count: int) -> int:
    normalized = (level or "").strip().lower()
    if normalized in {"again", "bad", "forgot"}:
        return 1
    if normalized in {"hard", "fuzzy"}:
        return max(3, current_interval // 2 if current_interval else 3)
    idx = min(max(review_count, 0), len(MASTER_STEPS) - 1)
    return MASTER_STEPS[idx]
