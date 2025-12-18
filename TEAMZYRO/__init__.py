# ------------------------------ IMPORTS ---------------------------------
import logging
import os
import asyncio

from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import Client, filters as f
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# --------------------------- LOGGING SETUP ------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)

logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)

# ---------------------------- CONSTANTS ---------------------------------
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
TOKEN = os.getenv("TOKEN")

mongo_url = os.getenv("MONGO_URL")

SUDO = [int(x) for x in os.getenv("SUDO", "").split(",") if x.strip().isdigit()]
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# ---------------------------- PYROGRAM ----------------------------------
ZYRO = Client(
    name="ZYRO",
    api_id=api_id,
    api_hash=api_hash,
    bot_token=TOKEN,
)

# -------------------------- DATABASE SETUP ------------------------------
mongo = AsyncIOMotorClient(mongo_url)
db = mongo["hinata_waifu"]

user_collection = db["gaming_user_collection"]
collection = db["gaming_anime_characters"]

# -------------------------- GLOBAL STATE --------------------------------
locks = {}
message_counts = {}
user_cooldowns = {}

# -------------------------- LOAD MODULES --------------------------------
from TEAMZYRO.unit.zyro_ban import *
from TEAMZYRO.unit.zyro_sudo import *
from TEAMZYRO.unit.zyro_react import *
from TEAMZYRO.unit.zyro_log import *
from TEAMZYRO.unit.zyro_send_img import *
from TEAMZYRO.unit.zyro_rarity import *

# ---------------------- KOYEB HTTP KEEP-ALIVE ---------------------------
async def health(request):
    return web.Response(text="OK")

async def start_web():
    app = web.Application()
    app.router.add_get("/", health)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", 8000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    LOGGER("WEB").info(f"HTTP server running on port {port}")

# ----------------------------- START -----------------------------------
async def main():
    await start_web()
    await ZYRO.start()
    LOGGER("BOT").info("Bot started successfully")
    await asyncio.Event().wait()  # keep alive forever

if __name__ == "__main__":
    asyncio.run(main())from TEAMZYRO.unit.zyro_rarity import *
# ------------------------------------------------------------------------

async def PLOG(text: str):
    await app.send_message(
       chat_id=GLOG,
       text=text
   )

# ---------------------------- END OF CODE ------------------------------
