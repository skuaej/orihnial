# economy.py

from datetime import datetime, timedelta
from pyrogram import filters
from TEAMZYRO import app, user_collection

# ─── CONFIG ─────────────────────────────────────────
HOURLY_COINS = 100
DAILY_COINS = 500

HOURLY_CD = timedelta(hours=1)
DAILY_CD = timedelta(hours=24)

# 🔒 PERMANENT ADMIN
ADMIN_IDS = [1334658171]


# ─── GET OR CREATE USER (SAFE) ──────────────────────
async def get_user(user):
    data = await user_collection.find_one({"id": user.id})

    if not data:
        data = {
            "id": user.id,
            "first_name": user.first_name,
            "username": user.username,
            "coins": 0,
            "tokens": 0,
            "last_hourly": None,
            "last_daily": None,
            "daily_streak": 0,
            "vip": False,
            "characters": []
        }
        await user_collection.insert_one(data)
        return data

    # Auto-fix missing fields
    updates = {}
    defaults = {
        "coins": 0,
        "tokens": 0,
        "last_hourly": None,
        "last_daily": None,
        "daily_streak": 0,
        "vip": False,
        "characters": []
    }

    for k, v in defaults.items():
        if k not in data:
            updates[k] = v

    if updates:
        await user_collection.update_one({"id": user.id}, {"$set": updates})
        data.update(updates)

    return data


# ─── BALANCE ─────────────────────────────────────────
@app.on_message(filters.command("balance"))
async def balance_cmd(_, message):
    user = await get_user(message.from_user)

    await message.reply_text(
        f"💳 **{message.from_user.first_name}'s Balance**\n\n"
        f"💰 Coins: `{user.get('coins', 0)}`\n"
        f"🪙 Tokens: `{user.get('tokens', 0)}`"
    )


# ─── HOURLY ──────────────────────────────────────────
@app.on_message(filters.command("hourly"))
async def hourly_cmd(_, message):
    user = await get_user(message.from_user)
    now = datetime.utcnow()

    if user["last_hourly"]:
        remaining = HOURLY_CD - (now - user["last_hourly"])
        if remaining.total_seconds() > 0:
            m, s = divmod(int(remaining.total_seconds()), 60)
            return await message.reply_text(f"⏳ Try again in `{m}m {s}s`")

    reward = HOURLY_COINS * (2 if user["vip"] else 1)

    await user_collection.update_one(
        {"id": user["id"]},
        {"$inc": {"coins": reward}, "$set": {"last_hourly": now}}
    )

    await message.reply_text(f"🪙 You received **{reward} coins**")


# ─── DAILY ──────────────────────────────────────────
@app.on_message(filters.command("daily"))
async def daily_cmd(_, message):
    user = await get_user(message.from_user)
    now = datetime.utcnow()

    if user["last_daily"]:
        diff = now - user["last_daily"]
        if diff < DAILY_CD:
            h = int((DAILY_CD - diff).total_seconds() // 3600)
            return await message.reply_text(f"⏳ Come back in `{h}h`")

        streak = 1 if diff > timedelta(hours=48) else user["daily_streak"] + 1
    else:
        streak = 1

    bonus = min(streak * 50, 500)
    reward = DAILY_COINS + bonus
    if user["vip"]:
        reward *= 2

    await user_collection.update_one(
        {"id": user["id"]},
        {
            "$set": {"last_daily": now, "daily_streak": streak},
            "$inc": {"coins": reward}
        }
    )

    await message.reply_text(
        f"🌞 **Daily Claimed!**\n"
        f"🪙 Coins: `{reward}`\n"
        f"🔥 Streak: `{streak}`"
    )


# ─── ADMIN COMMANDS ─────────────────────────────────
@app.on_message(filters.command("addcoins") & filters.user(ADMIN_IDS))
async def addcoins(_, message):
    uid = int(message.command[1])
    amt = int(message.command[2])

    await user_collection.update_one(
        {"id": uid},
        {"$inc": {"coins": amt}},
        upsert=True
    )

    await message.reply_text(f"✅ Added `{amt}` coins to `{uid}`")


@app.on_message(filters.command("removecoins") & filters.user(ADMIN_IDS))
async def removecoins(_, message):
    uid = int(message.command[1])
    amt = int(message.command[2])

    await user_collection.update_one(
        {"id": uid},
        {"$inc": {"coins": -amt}}
    )

    await message.reply_text(f"❌ Removed `{amt}` coins from `{uid}`")
