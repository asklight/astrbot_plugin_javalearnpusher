from __future__ import annotations

import asyncio
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, MessageChain, filter
from astrbot.api.message_components import Plain
from astrbot.api.star import Context, Star, register
from astrbot.core.utils.astrbot_path import get_astrbot_plugin_data_path

from xlin_pusher.crawler import DEFAULT_START_URL, crawl_xiaolincoding
from xlin_pusher.formatter import format_card_message, format_status
from xlin_pusher.scheduler import is_valid_push_time, should_push_now
from xlin_pusher.store import CardStore

PLUGIN_NAME = "astrbot_plugin_javalearnpusher"


@register(PLUGIN_NAME, "asklight", "Xiaolincoding learning pusher", "1.0.0")
class XiaolincodingPusherPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig | None = None):
        super().__init__(context)
        self.config = config or {}
        self.data_dir = self._resolve_data_dir()
        self.store = CardStore(self.data_dir)
        self._schedule_task: asyncio.Task | None = None

    async def initialize(self) -> None:
        self.store.ensure_data_dir()
        self._schedule_task = asyncio.create_task(self._schedule_loop())
        logger.info("[xlin] plugin initialized")

    async def terminate(self) -> None:
        if self._schedule_task:
            self._schedule_task.cancel()
            try:
                await self._schedule_task
            except asyncio.CancelledError:
                pass
        logger.info("[xlin] plugin stopped")

    def _resolve_data_dir(self) -> Path:
        try:
            return Path(get_astrbot_plugin_data_path()) / PLUGIN_NAME
        except Exception:
            return Path(__file__).resolve().parent / "data"

    def _config_value(self, key: str, default: Any) -> Any:
        try:
            if self.config is not None and key in self.config:
                return self.config[key]
        except Exception:
            pass
        return default

    async def _schedule_loop(self) -> None:
        while True:
            try:
                now = datetime.now()
                sleep_seconds = 60 - now.second - now.microsecond / 1_000_000
                await asyncio.sleep(max(1, sleep_seconds))
                state = self.store.load_schedule()
                now = datetime.now()
                if not should_push_now(state, now):
                    continue
                card = self.store.select_next_card(now.date())
                if not card:
                    continue
                ok = await self._send_to_session(state.target_session, format_card_message(card))
                if ok:
                    state.last_push_date = now.date().isoformat()
                    self.store.save_schedule(state)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"[xlin] schedule loop failed: {exc}")

    async def _send_to_session(self, session: str, text: str) -> bool:
        chain = MessageChain(chain=[Plain(text)])
        try:
            return await self.context.send_message(session, chain)
        except Exception as exc:
            logger.error(f"[xlin] failed to send scheduled message: {exc}")
            return False

    async def _crawl_and_save(self) -> int:
        start_url = (
            str(self._config_value("start_url", DEFAULT_START_URL)).strip() or DEFAULT_START_URL
        )
        max_pages = int(self._config_value("max_pages", 80) or 80)
        timeout = int(self._config_value("request_timeout", 30) or 30)
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: crawl_xiaolincoding(start_url=start_url, max_pages=max_pages, timeout=timeout),
        )
        self.store.save_cards(result.cards)
        return len(result.cards)

    @filter.command("xlin")
    async def xlin(self, event: AstrMessageEvent):
        """Xiaolincoding learning pusher commands."""
        parts = event.message_str.strip().split()
        subcmd = parts[1].lower() if len(parts) > 1 else "status"

        if subcmd == "status":
            cards = self.store.load_cards()
            schedule = self.store.load_schedule()
            yield event.plain_result(
                format_status(
                    total_cards=len(cards),
                    due_cards=len(self.store.due_cards(date.today())),
                    enabled=schedule.enabled,
                    push_time=schedule.push_time,
                    target_session=schedule.target_session,
                    last_push_date=schedule.last_push_date,
                )
            )
            return

        if subcmd == "next":
            card = self.store.select_next_card(date.today())
            if not card:
                yield event.plain_result("No cards found. Run /xlin import first.")
                return
            yield event.plain_result(format_card_message(card))
            return

        if subcmd == "topic":
            keyword = " ".join(parts[2:]).strip()
            if not keyword:
                yield event.plain_result("Usage: /xlin topic <keyword>")
                return
            card = self.store.find_topic_card(keyword)
            if not card:
                yield event.plain_result(f"No card matched topic: {keyword}")
                return
            yield event.plain_result(format_card_message(card))
            return

        if subcmd == "set":
            if len(parts) < 3 or not is_valid_push_time(parts[2]):
                yield event.plain_result("Usage: /xlin set <HH:MM>")
                return
            state = self.store.load_schedule()
            state.enabled = True
            state.push_time = parts[2]
            state.target_session = event.unified_msg_origin
            self.store.save_schedule(state)
            yield event.plain_result(
                f"Daily push enabled at {state.push_time} for this conversation."
            )
            return

        if subcmd == "cancel":
            state = self.store.load_schedule()
            state.enabled = False
            self.store.save_schedule(state)
            yield event.plain_result("Daily push disabled.")
            return

        if subcmd == "import":
            yield event.plain_result("Starting xiaolincoding crawl. This may take a while.")
            try:
                count = await self._crawl_and_save()
            except Exception as exc:
                logger.error(f"[xlin] import failed: {exc}")
                yield event.plain_result(f"Import failed: {str(exc)[:200]}")
                return
            yield event.plain_result(f"Imported {count} learning cards into local storage.")
            return

        if subcmd == "rate":
            if len(parts) < 4:
                yield event.plain_result("Usage: /xlin rate <card_id> <again|hard|good>")
                return
            card = self.store.mark_reviewed(parts[2], parts[3], date.today())
            if not card:
                yield event.plain_result(f"Card not found: {parts[2]}")
                return
            yield event.plain_result(
                f"Recorded {parts[3]} for {card.id}. Next review: {card.next_review}"
            )
            return

        yield event.plain_result(
            "Usage:\n"
            "/xlin status\n"
            "/xlin import\n"
            "/xlin next\n"
            "/xlin topic <keyword>\n"
            "/xlin set <HH:MM>\n"
            "/xlin cancel\n"
            "/xlin rate <card_id> <again|hard|good>"
        )
