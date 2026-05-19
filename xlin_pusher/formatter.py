from __future__ import annotations

from .models import LearningCard


def truncate_text(text: str, max_length: int) -> str:
    clean = " ".join((text or "").split())
    if max_length <= 3:
        return clean[:max_length]
    if len(clean) <= max_length:
        return clean
    return clean[: max_length - 3].rstrip() + "..."


def format_card_message(card: LearningCard, max_content_length: int = 1200) -> str:
    content = truncate_text(card.content, max_content_length)
    lines = [
        "Xiaolincoding Learning Card",
        f"[{card.category}] {card.title}",
        f"Section: {card.section}",
        "",
        f"Prompt: {card.prompt}",
        "",
        content,
        "",
        f"Source: {card.source_url}",
    ]
    if card.images:
        lines.append(f"Images: {len(card.images)}")
        lines.extend(card.images[:3])
    return "\n".join(lines).strip()


def format_status(
    *,
    total_cards: int,
    due_cards: int,
    enabled: bool,
    push_time: str,
    target_session: str,
    last_push_date: str,
) -> str:
    target = target_session or "not set"
    enabled_text = "enabled" if enabled else "disabled"
    return "\n".join(
        [
            "Xiaolincoding Pusher Status",
            f"Cards: {total_cards}",
            f"Due today: {due_cards}",
            f"Schedule: {enabled_text}",
            f"Push time: {push_time}",
            f"Target: {target}",
            f"Last push date: {last_push_date or 'never'}",
        ]
    )
