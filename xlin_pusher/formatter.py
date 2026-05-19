from __future__ import annotations

from .models import LearningCard

CATEGORY_LABELS = {
    "network": "网络",
    "system": "操作系统",
    "mysql": "MySQL",
    "redis": "Redis",
    "interview": "面试",
    "java": "Java",
    "go": "Go",
    "cpp": "C++",
    "home": "首页",
}


def truncate_text(text: str, max_length: int) -> str:
    clean = " ".join((text or "").split())
    if max_length <= 3:
        return clean[:max_length]
    if len(clean) <= max_length:
        return clean
    return clean[: max_length - 3].rstrip() + "..."


def format_card_message(card: LearningCard, max_content_length: int = 1200) -> str:
    content = truncate_text(card.content, max_content_length)
    category = CATEGORY_LABELS.get(card.category, card.category or "未分类")
    lines = [
        "小林 Coding 学习卡片",
        f"[{category}] {card.title}",
        f"章节：{card.section}",
        "",
        f"问题：{card.prompt}",
        "",
        content,
        "",
        f"来源：{card.source_url}",
    ]
    if card.images:
        lines.append(f"配图数量：{len(card.images)}")
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
    target = target_session or "未设置"
    enabled_text = "已启用" if enabled else "未启用"
    return "\n".join(
        [
            "小林 Coding 推送状态",
            f"题库数量：{total_cards}",
            f"今日待复习：{due_cards}",
            f"定时推送：{enabled_text}",
            f"推送时间：{push_time}",
            f"推送目标：{target}",
            f"上次推送日期：{last_push_date or '从未推送'}",
        ]
    )
