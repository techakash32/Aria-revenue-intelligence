"""Manual smoke test for the WhatsApp alert integration.

Not part of the pytest suite (hits a real external API). Run directly:
    python scripts/manual_whatsapp_test.py
"""
import asyncio

from dotenv import load_dotenv

load_dotenv()  # must run before importing modules that read env vars at import time

from tools.whatsapp_tool import send_whatsapp_alert


async def test() -> None:
    result = await send_whatsapp_alert("Hello from ARIA test")
    print(result)


if __name__ == "__main__":
    asyncio.run(test())
