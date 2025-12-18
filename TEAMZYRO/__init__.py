# ------------------------------ IMPORTS ---------------------------------
import logging
import os
import asyncio

from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import Client
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

# ---------------------------- ENV CONFIG --------------------------------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
TOKEN = os.getenv("TOKEN")
MONGO_URL = os.getenv("MONGO_URL")

PORT = int(os.getenv("PORT", 8000))

SUDO = [int(x) for x in os.getenv("SUDO", "").split(",") if x.strip().isdigit()]
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# ---------------------------- PYROGRAM ----------------------------------
ZYRO = Client(
    name="ZYRO",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=TOKEN,
)

# -------------------------- DATABASE SETUP ------------------------------
mongo = AsyncIOMotorClient(MONGO_URL)
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

    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    LOGGER("WEB").info(f"HTTP server running on port {PORT}")

# ----------------------------- MAIN ------------------------------------
async def main():
    await start_web()
    await ZYRO.start()
    LOGGER("BOT").info("Bot started successfully")
    await asyncio.Event().wait()  # keep process alive forever

if __name__ == "__main__":
    asyncio.run(main())
