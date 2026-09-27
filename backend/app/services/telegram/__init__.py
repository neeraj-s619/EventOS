"""
EVENTOS Telegram Operations Network Package.
Provides two-bot operational architecture:
- Visitor Bot (Visitor services, accommodation matching)
- Staff / Ops Bot (Volunteers, gate staff, venue operators, transport & hotel coordinators)
- TelegramBotManager (Central orchestration)
"""
from app.services.telegram.client import TelegramBotClient
from app.services.telegram.parser import parse_operational_message, parse_operational_response, OperationalParseResult
from app.services.telegram.service import TelegramService
from app.services.telegram.polling import TelegramPollingWorker
from app.services.telegram.visitor_bot import VisitorBotAdapter
from app.services.telegram.staff_bot import StaffBotAdapter
from app.services.telegram.manager import TelegramBotManager, get_telegram_bot_manager

__all__ = [
    "TelegramBotClient",
    "parse_operational_message",
    "parse_operational_response",
    "OperationalParseResult",
    "TelegramService",
    "TelegramPollingWorker",
    "VisitorBotAdapter",
    "StaffBotAdapter",
    "TelegramBotManager",
    "get_telegram_bot_manager",
]
