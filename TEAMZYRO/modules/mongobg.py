
from pyrogram import filters
from pymongo import MongoClient
import bson
from TEAMZYRO import app, SUDO
import os

SOURCE_URI = os.getenv("MONGO_URI")          # main db
BACKUP_URI = os.getenv("BACKUP_MONGO_URI")  # backup db
DB_NAME = os.getenv("DB_NAME", "waifu_bot")


def calc_size(docs):
    return sum(len(bson.BSON.encode(d)) for d in docs)


@app.on_message(filters.command("backupdb") & filters.user(SUDO))
async def backup_db(_, message):
    try:
        await message.reply_text("⏳ Starting MongoDB backup...")

        src = MongoClient(SOURCE_URI)[DB_NAME]
        dst = MongoClient(BACKUP_URI)[DB_NAME]

        total = 0
        for col in src.list_collection_names():
            docs = list(src[col].find())
            dst[col].delete_many({})
            if docs:
                dst[col].insert_many(docs)
                total += calc_size(docs)

        await message.reply_text(
            f"✅ Backup completed!\n📦 Size: `{total/1024:.2f} KB`"
        )

    except Exception as e:
        await message.reply_text(f"❌ Backup failed:\n`{e}`")
