from pyrogram import filters
from pymongo import MongoClient
import bson
import os
from TEAMZYRO import app

# ─────────────────────────────
# CONFIG (CHANGE ONLY THESE)
# ─────────────────────────────

OWNER_ID = 1334658171  # only this user can run commands

# Source = ORIGINAL DB (current bot database)
SOURCE_URI = "mongodb+srv://sk5400552:shjjkytdcghhudd@cluster0g.kbllv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0g"

# Backup = BACKUP DB (safe copy)
BACKUP_URI = "mongodb+srv://shek272881oujo.mongodb.net/?retryWrites=true&w=majority&appName=Waifudb"

DB_NAME = "waifu_bot"   # database name (same in both)

# ─────────────────────────────
# UTILS
# ─────────────────────────────

def calc_size(docs):
    return sum(len(bson.BSON.encode(d)) for d in docs)

# ─────────────────────────────
# BACKUP COMMAND
# ─────────────────────────────

@app.on_message(filters.command("backupdb") & filters.user(OWNER_ID))
async def backup_db(_, message):
    try:
        await message.reply_text("⏳ **Starting database backup...**")

        src_db = MongoClient(SOURCE_URI)[DB_NAME]
        dst_db = MongoClient(BACKUP_URI)[DB_NAME]

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

        await message.reply_text(
            f"✅ **Backup Completed!**\n\n"
            f"📦 Collections: `{total_collections}`\n"
            f"💾 Size: `{total_size / 1024:.2f} KB`"
        )

    except Exception as e:
        await message.reply_text(f"❌ **Backup failed**\n`{e}`")

# ─────────────────────────────
# RESTORE COMMAND
# ─────────────────────────────

@app.on_message(filters.command("restoredb") & filters.user(OWNER_ID))
async def restore_db(_, message):
    try:
        await message.reply_text("⏳ **Restoring database from backup...**")

        src_db = MongoClient(BACKUP_URI)[DB_NAME]
        dst_db = MongoClient(SOURCE_URI)[DB_NAME]

        total_collections = 0

        for col_name in src_db.list_collection_names():
            src_col = src_db[col_name]
            dst_col = dst_db[col_name]

            docs = list(src_col.find())
            dst_col.delete_many({})

            if docs:
                dst_col.insert_many(docs)

            total_collections += 1

        await message.reply_text(
            f"✅ **Restore Completed!**\n\n"
            f"📦 Collections Restored: `{total_collections}`"
        )

    except Exception as e:
        await message.reply_text(f"❌ **Restore failed**\n`{e}`")
