"""
Telegram Bot Long-Polling Worker for Local Development.
Supports multiple independent polling workers (e.g. Visitor Bot & Staff/Ops Bot)
each maintaining its own update stream and offset without interference.
"""

import asyncio
import logging
from typing import Optional, Callable, Any, Awaitable, Dict
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.telegram.client import TelegramBotClient

logger = logging.getLogger("eventos.telegram.polling")


class TelegramPollingWorker:
    """Async background worker polling Telegram Bot API for updates."""

    def __init__(
        self,
        db_session_factory: Callable[[], Session],
        client: Optional[TelegramBotClient] = None,
        poll_interval: Optional[float] = None,
        name: str = "default",
        update_handler: Optional[Callable[[Dict[str, Any], Session], Awaitable[Any]]] = None
    ):
        self.db_session_factory = db_session_factory
        self.client = client or TelegramBotClient()
        self.poll_interval = poll_interval or settings.telegram_poll_interval
        self.name = name
        self.update_handler = update_handler
        self.offset: Optional[int] = None
        self._is_running = False
        self._task: Optional[asyncio.Task] = None

    @property
    def is_running(self) -> bool:
        return self._is_running

    def start(self) -> bool:
        """Starts the long polling background loop if configured."""
        if self._is_running:
            return False

        if not self.client.is_configured:
            logger.info(f"[TELEGRAM_POLLING:{self.name.upper()}] Token not configured — worker idle (Sandbox active)")
            return False

        if settings.get_telegram_mode() != "polling":
            logger.info(f"[TELEGRAM_POLLING:{self.name.upper()}] Operational mode is '{settings.get_telegram_mode()}' — polling disabled")
            return False

        self._is_running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(f"[TELEGRAM_POLLING:{self.name.upper()}] Worker started in background")
        return True

    def stop(self):
        """Stops the long polling loop."""
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info(f"[TELEGRAM_POLLING:{self.name.upper()}] Worker stopped")

    async def _poll_loop(self):
        """Continuous polling loop."""
        logger.info(f"[TELEGRAM_POLLING:{self.name.upper()}] Polling loop active via getUpdates")
        try:
            await self.client.delete_webhook(drop_pending_updates=False)
        except Exception as e:
            logger.debug(f"[TELEGRAM_POLLING:{self.name.upper()}] delete_webhook check: {e}")

        while self._is_running:
            try:
                updates = await self.client.get_updates(offset=self.offset, timeout=1)
                if updates:
                    for up in updates:
                        up_id = up.get("update_id")
                        if up_id is not None:
                            self.offset = up_id + 1

                        # Process update inside fresh session
                        db = self.db_session_factory()
                        try:
                            if self.update_handler:
                                await self.update_handler(up, db)
                            else:
                                from app.services.telegram.service import TelegramService
                                service = TelegramService(db=db, client=self.client)
                                await service.handle_update(up)
                        except Exception as e:
                            logger.error(f"[TELEGRAM_POLLING:{self.name.upper()}] Update processing error: {e}", exc_info=True)
                        finally:
                            db.close()

                    # Received updates, check immediately for next batch
                    continue

                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"[TELEGRAM_POLLING:{self.name.upper()}] Polling error: {type(e).__name__} - retrying in 5s")
                await asyncio.sleep(5.0)

        self._is_running = False
