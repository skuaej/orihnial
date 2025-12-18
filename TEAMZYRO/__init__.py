
from TEAMZYRO.modules.star import *

# ============================== IMPORTS ==============================
import os
import asyncio
import logging

from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import Client, filters
from pyrogram.types import Message
from aiohttp import web

# ============================== LOGGING ===============================
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
)
LOGGER = logging.getLogger("TEAMZYRO")

# ============================== ENV ==================================
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("TOKEN")
MONGO_URL = os.getenv("MONGO_URL")
PORT = int(os.getenv("PORT", 8000))

SUDO = [int(x) for x in os.getenv("SUDO", "").split(",") if x.isdigit()]
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# ============================== PYROGRAM ==============================
app = Client(
    "TEAMZYRO",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

# ============================== DATABASE ==============================
mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo["hinata_waifu"]

user_collection = db["gaming_user_collection"]
char_collection = db["gaming_anime_characters"]

# ============================== GLOBALS ===============================
locks = {}
user_cooldowns = {}

# ============================== BASIC TEST ============================
@app.on_message(filters.command("ping"))
async def ping(_, message: Message):
    await message.reply_text("🏓 Pong!", parse_mode=None)

# ============================== SAFE START ============================
@app.on_message(filters.command("start"))
async def start(_, message: Message):
    await message.reply_text(
        "✅ Bot is running successfully.",
        parse_mode=None
    )

# ============================== LOAD YOUR MODULES =====================
from TEAMZYRO.unit.zyro_ban import *
from TEAMZYRO.unit.zyro_sudo import *
from TEAMZYRO.unit.zyro_react import *
from TEAMZYRO.unit.zyro_log import *
from TEAMZYRO.unit.zyro_send_img import *
from TEAMZYRO.unit.zyro_rarity import *
from TEAMZYRO.modules.check import *
from TEAMZYRO.modules.start import *
from TEAMZYRO.modules.harem import *
from TEAMZYRO.modules.guess import *
from TEAMZYRO.modules.balance import *
from TEAMZYRO.modules.stats import *
from TEAMZYRO.modules.shop import *
from TEAMZYRO.modules.transfer import *

# ============================== KOYEB HTTP ============================
async def health(request):
    return web.Response(text="OK")

async def start_web():
    web_app = web.Application()
    web_app.router.add_get("/", health)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    LOGGER.info(f"🌐 HTTP server running on port {PORT}")

# ============================== MAIN =================================
async def main():
    await start_web()
    await app.start()
    LOGGER.info("🤖 Bot started successfully")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
