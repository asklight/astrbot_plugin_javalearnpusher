from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class LearningCard:
    id: str
    source_url: str
    category: str
    title: str
    section: str
    prompt: str
    content: str
    images: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    status: str = "new"
    next_review: str | None = None
    review_count: int = 0
    interval_days: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LearningCard:
        return cls(
            id=str(data.get("id", "")).strip(),
            source_url=str(data.get("source_url", "")).strip(),
            category=str(data.get("category", "")).strip(),
            title=str(data.get("title", "")).strip(),
            section=str(data.get("section", "")).strip(),
            prompt=str(data.get("prompt", "")).strip(),
            content=str(data.get("content", "")).strip(),
            images=[str(item).strip() for item in data.get("images", []) if str(item).strip()],
            tags=[str(item).strip() for item in data.get("tags", []) if str(item).strip()],
            status=str(data.get("status", "new")).strip() or "new",
            next_review=data.get("next_review") or None,
            review_count=int(data.get("review_count", 0) or 0),
            interval_days=int(data.get("interval_days", 0) or 0),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ScheduleState:
    enabled: bool = False
    push_time: str = "09:00"
    target_session: str = ""
    last_push_date: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ScheduleState:
        return cls(
            enabled=bool(data.get("enabled", False)),
            push_time=str(data.get("push_time", "09:00")).strip() or "09:00",
            target_session=str(data.get("target_session", "")).strip(),
            last_push_date=str(data.get("last_push_date", "")).strip(),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
