import os
import time
import psutil

from pyrogram import filters
from pyrogram.types import Message
from TEAMZYRO import app

OWNER_ID = int(os.getenv("OWNER_ID", "7850114307"))

def system_details():
    proc = psutil.Process(os.getpid())

    cpu = psutil.cpu_percent(interval=0)
    ram_bot = proc.memory_info().rss / (1024 ** 2)
    ram_total = psutil.virtual_memory().total / (1024 ** 2)

    load = os.getloadavg()[0] if hasattr(os, "getloadavg") else 0
    uptime = int((time.time() - psutil.boot_time()) // 60)

    return (
        "⭐ **System Status**\n\n"
        f"⚙️ CPU: `{cpu}%`\n"
        f"🧠 RAM (Bot): `{ram_bot:.1f} MB`\n"
        f"🧠 RAM (Total): `{ram_total:.0f} MB`\n"
        f"📊 Load Avg: `{load:.2f}`\n"
        f"⏱ Uptime: `{uptime} min`"
    )

@app.on_message(filters.command("star") & filters.user(OWNER_ID))
async def star_cmd(_, message: Message):
    await message.reply_text(
        system_details(),
        parse_mode="markdown"
    )
