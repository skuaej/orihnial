import time
from datetime import datetime
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode

from TEAMZYRO import app, user_collection

# ─────────────────────────────
# CONFIG
# ─────────────────────────────
DAILY_REWARD = 200
WEEKLY_REWARD = 1000

DAILY_CD = 24 * 60 * 60
WEEKLY_CD = 7 * 24 * 60 * 60


# ─────────────────────────────
# ENSURE USER (AUTO-FIX OLD DATA)
# ─────────────────────────────
async def ensure_user(user):
    data = await user_collection.find_one({"id": user.id})

    if not data:
        data = {
            "id": user.id,
            "first_name": user.first_name,
            "username": user.username,
            "balance": 0,
            "tokens": 0,
            "last_daily": 0,
            "last_weekly": 0
        }
        await user_collection.insert_one(data)
        return data

    updates = {}

    # balance
    if "balance" not in data:
        updates["balance"] = 0

    # tokens
    if "tokens" not in data:
        updates["tokens"] = 0

    # FIX last_daily
    if "last_daily" not in data:
        updates["last_daily"] = 0
    elif isinstance(data["last_daily"], datetime):
        updates["last_daily"] = int(data["last_daily"].timestamp())

    # FIX last_weekly
    if "last_weekly" not in data:
        updates["last_weekly"] = 0
    elif isinstance(data["last_weekly"], datetime):
        updates["last_weekly"] = int(data["last_weekly"].timestamp())

    if updates:
        await user_collection.update_one(
            {"id": user.id},
            {"$set": updates}
        )
        data.update(updates)

    return data


# ─────────────────────────────
# DAILY COMMAND
# ─────────────────────────────
@app.on_message(filters.command("daily"))
async def daily_cmd(_, message: Message):
    user = message.from_user
    data = await ensure_user(user)

    now = int(time.time())
    last = int(data.get("last_daily", 0))

    if now - last < DAILY_CD:
        remaining = DAILY_CD - (now - last)
        h = remaining // 3600
        m = (remaining % 3600) // 60
        return await message.reply_text(
            f"⏳ Daily already claimed\n"
            f"Try again in {h}h {m}m"
        )

    await user_collection.update_one(
        {"id": user.id},
        {
            "$inc": {"balance": DAILY_REWARD},
            "$set": {"last_daily": now}
        }
    )

    await message.reply_text(
        f"🎁 <b>Daily Reward Claimed!</b>\n\n"
        f"💰 +{DAILY_REWARD} coins",
        parse_mode=ParseMode.HTML
    )


# ─────────────────────────────
# WEEKLY COMMAND
# ─────────────────────────────
@app.on_message(filters.command("weekly"))
async def weekly_cmd(_, message: Message):
    user = message.from_user
    data = await ensure_user(user)

    now = int(time.time())
    last = int(data.get("last_weekly", 0))

    if now - last < WEEKLY_CD:
        remaining = WEEKLY_CD - (now - last)
        d = remaining // 86400
        h = (remaining % 86400) // 3600
        return await message.reply_text(
            f"⏳ Weekly already claimed\n"
            f"Try again in {d}d {h}h"
        )

    await user_collection.update_one(
        {"id": user.id},
        {
            "$inc": {"balance": WEEKLY_REWARD},
            "$set": {"last_weekly": now}
        }
    )

    await message.reply_text(
        f"🎉 <b>Weekly Reward Claimed!</b>\n\n"
        f"💰 +{WEEKLY_REWARD} coins",
        parse_mode=ParseMode.HTML
    )
