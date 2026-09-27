"""
Telegram Bot Administration & Webhook Setup CLI.
Usage:
  python -m app.services.telegram.setup status
  python -m app.services.telegram.setup get-webhook
  python -m app.services.telegram.setup set-webhook <https://url/path> [secret]
  python -m app.services.telegram.setup delete-webhook
"""

import sys
import asyncio
import json

from app.core.config import settings
from app.services.telegram.client import TelegramBotClient


async def main():
    args = sys.argv[1:]
    action = args[0].lower() if args else "status"

    client = TelegramBotClient()

    print("=" * 60)
    print(" EVENTOS TELEGRAM BOT SETUP UTILITY")
    print("=" * 60)

    if not client.is_configured:
        print("[!] ERROR: TELEGRAM_BOT_TOKEN is not configured in .env or environment.")
        print("    Add TELEGRAM_BOT_TOKEN=... to your backend/.env file.")
        sys.exit(1)

    if action in ["status", "info"]:
        print("[*] Checking Bot Identity...")
        me = await client.get_me()
        print(f"    Bot API Response: {json.dumps(me, indent=2)}")
        print("\n[*] Checking Webhook Status...")
        wh = await client.get_webhook_info()
        print(f"    Webhook Info: {json.dumps(wh, indent=2)}")

    elif action in ["get-webhook", "get", "webhook-info"]:
        print("[*] Querying getWebhookInfo...")
        wh = await client.get_webhook_info()
        print(json.dumps(wh, indent=2))

    elif action in ["set-webhook", "set"]:
        if len(args) < 2:
            print("[!] Usage: python -m app.services.telegram.setup set-webhook <URL> [SECRET]")
            sys.exit(1)
        url = args[1]
        secret = args[2] if len(args) > 2 else settings.telegram_webhook_secret
        print(f"[*] Setting Webhook to: {url}")
        res = await client.set_webhook(url=url, secret_token=secret)
        print(f"    Result: {json.dumps(res, indent=2)}")

    elif action in ["delete-webhook", "delete", "del"]:
        print("[*] Deleting Webhook (switching bot to Polling mode)...")
        res = await client.delete_webhook()
        print(f"    Result: {json.dumps(res, indent=2)}")

    else:
        print(f"[!] Unknown command '{action}'. Available commands:")
        print("    status          - Check bot identity and webhook state")
        print("    get-webhook     - Query getWebhookInfo")
        print("    set-webhook URL - Set public HTTPS webhook URL")
        print("    delete-webhook  - Delete webhook to enable polling")


if __name__ == "__main__":
    asyncio.run(main())
