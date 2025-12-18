from pyrogram import filters
from pymongo import MongoClient
import bson
import os
from TEAMZYRO import app

# ─────────────────────────────
# CONFIG
# ─────────────────────────────

OWNER_ID = 1334658171

SOURCE_URI = os.getenv("MONGO_URI")
BACKUP_URI = os.getenv("BACKUP_MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "waifu_bot")


# ─────────────────────────────
# UTILS
# ─────────────────────────────

def calc_size(docs):
    return sum(len(bson.BSON.encode(d)) for d in docs)


def check_env():
    return all([SOURCE_URI, BACKUP_URI, DB_NAME])


# ─────────────────────────────
# BACKUP COMMAND
# ─────────────────────────────

@app.on_message(filters.command("backupdb") & filters.user(OWNER_ID))
async def backup_db(_, message):
    if not check_env():
        return await message.reply_text(
            "❌ ENV missing!\nSet `MONGO_URI`, `BACKUP_MONGO_URI`, `DB_NAME`"
        )

    try:
        await message.reply_text("⏳ Starting database backup...")

        src_client = MongoClient(SOURCE_URI)
        dst_client = MongoClient(BACKUP_URI)

        src_db = src_client[DB_NAME]
        dst_db = dst_client[DB_NAME]

        total_size = 0
        total_collections = 0

        for col_name in src_db.list_collection_names():
            src_col = src_db[col_name]
            dst_col = dst_db[col_name]

            docs = list(src_col.find())
            dst_col.delete_many({})

            if docs:
                dst_col.insert_many(docs)
                total_size += calc_size(docs)

            total_collections += 1

        src_client.close()
        dst_client.close()

        await message.reply_text(
            f"✅ **Backup Completed!**\n\n"
            f"📦 Collections: `{total_collections}`\n"
            f"💾 Size: `{total_size/1024:.2f} KB`"
        )

    except Exception as e:
        await message.reply_text(f"❌ Backup failed:\n`{e}`")


# ─────────────────────────────
# RESTORE COMMAND
# ─────────────────────────────

@app.on_message(filters.command("restoredb") & filters.user(OWNER_ID))
async def restore_db(_, message):
    if not check_env():
        return await message.reply_text(
            "❌ ENV missing!\nSet `MONGO_URI`, `BACKUP_MONGO_URI`, `DB_NAME`"
        )

    try:
        await message.reply_text("⏳ Restoring database from backup...")

        src_client = MongoClient(BACKUP_URI)
        dst_client = MongoClient(SOURCE_URI)

        src_db = src_client[DB_NAME]
        dst_db = dst_client[DB_NAME]

        for col_name in src_db.list_collection_names():
            src_col = src_db[col_name]
            dst_col = dst_db[col_name]

            docs = list(src_col.find())
            dst_col.delete_many({})

            if docs:
                dst_col.insert_many(docs)

        src_client.close()
        dst_client.close()

        await message.reply_text("✅ **Restore Completed Successfully!**")

    except Exception as e:
        await message.reply_text(f"❌ Restore failed:\n`{e}`")
