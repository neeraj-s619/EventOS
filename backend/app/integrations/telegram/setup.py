"""
CLI setup entrypoint alias for app.services.telegram.setup.
"""
from app.services.telegram.setup import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
