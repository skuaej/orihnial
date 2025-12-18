
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from datetime import datetime, timedelta
import html

from TEAMZYRO import app, user_collection

# ==========================
# CONFIG
# ==========================
BALANCE_GIVER_ID = 1334658171  # only this user can add balance

DAILY_REWARD = 250
HOURLY_REWARD = 80

DAILY_COOLDOWN = timedelta(hours=24)
HOURLY_COOLDOWN = timedelta(hours=1)

# ==========================
# ENSURE USER (CRITICAL)
# ==========================
async def ensure_user(user):
    data = await user_collection.find_one({"id": user.id})

    if not data:
        data = {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "balance": 0,
            "tokens": 0,
            "characters": [],
            "last_daily": None,
            "last_hourly": None
        }
        await user_collection.insert_one(data)
        return data

    updates = {}
    defaults = {
        "balance": 0,
        "tokens": 0,
        "characters": [],
        "last_daily": None,
        "last_hourly": None,
        "first_name": user.first_name,
        "username": user.username
    }

    for k, v in defaults.items():
        if k not in data:
            updates[k] = v

    if updates:
        await user_collection.update_one(
            {"id": user.id},
            {"$set": updates}
        )
        data.update(updates)

    return data

# ==========================
# BALANCE
# ==========================
@app.on_message(filters.command("balance"))
async def balance_cmd(_, message: Message):
    user = await ensure_user(message.from_user)

    await message.reply_text(
        f"💰 <b>{html.escape(message.from_user.first_name)}'s Balance</b>\n\n"
        f"🪙 Coins: <b>{user['balance']}</b>\n"
        f"🎟 Tokens: <b>{user['tokens']}</b>",
        parse_mode=ParseMode.HTML
    )

# ==========================
# ADD BALANCE (SPECIFIC USER)
# ==========================
@app.on_message(filters.command("addbal"))
async def add_balance(_, message: Message):
    if message.from_user.id != BALANCE_GIVER_ID:
        return await message.reply_text("❌ You are not allowed.")

    parts = message.text.split()
    amount = None
    target_id = None

    for p in parts:
        if p.isdigit():
            amount = int(p)
        elif p.startswith("@"):
            user = await user_collection.find_one({"username": p[1:]})
            if user:
                target_id = user["id"]

    if not amount or not target_id:
        return await message.reply_text(
            "❌ Usage:\n/addbal <amount> @username"
        )

    await user_collection.update_one(
        {"id": target_id},
        {"$inc": {"balance": amount}},
        upsert=True
    )

    await message.reply_text(
        f"✅ Added <b>{amount}</b> coins successfully.",
        parse_mode=ParseMode.HTML
    )

# ==========================
# PAY
# ==========================
@app.on_message(filters.command("pay"))
async def pay_cmd(_, message: Message):
    sender = await ensure_user(message.from_user)
    parts = message.text.split()

    amount = None
    receiver_id = None

    if message.reply_to_message:
        receiver_id = message.reply_to_message.from_user.id
        for p in parts:
            if p.isdigit():
                amount = int(p)
    else:
        for p in parts:
            if p.isdigit():
                amount = int(p)
            elif p.startswith("@"):
                user = await user_collection.find_one({"username": p[1:]})
                if user:
                    receiver_id = user["id"]

    if not amount or not receiver_id:
        return await message.reply_text(
            "❌ Usage:\n/pay <amount> @username\n/pay <amount> (reply)"
        )

    if sender["balance"] < amount:
        return await message.reply_text("❌ Insufficient balance.")

    await user_collection.update_one(
        {"id": sender["id"]},
        {"$inc": {"balance": -amount}}
    )

    await user_collection.update_one(
        {"id": receiver_id},
        {"$inc": {"balance": amount}},
        upsert=True
    )

    await message.reply_text(
        f"✅ Paid <b>{amount}</b> coins successfully.",
        parse_mode=ParseMode.HTML
    )

# ==========================
# DAILY
# ==========================
@app.on_message(filters.command("daily"))
async def daily_cmd(_, message: Message):
    user = await ensure_user(message.from_user)
    now = datetime.utcnow()

    if user["last_daily"] and now - user["last_daily"] < DAILY_COOLDOWN:
        remaining = DAILY_COOLDOWN - (now - user["last_daily"])
        return await message.reply_text(
            f"⏳ Come back in {remaining.seconds//3600}h"
        )

    await user_collection.update_one(
        {"id": user["id"]},
        {
            "$inc": {"balance": DAILY_REWARD},
            "$set": {"last_daily": now}
        }
    )

    await message.reply_text(
        f"🎁 You received <b>{DAILY_REWARD}</b> coins!",
        parse_mode=ParseMode.HTML
    )

# ==========================
# HOURLY
# ==========================
@app.on_message(filters.command("hourly"))
async def hourly_cmd(_, message: Message):
    user = await ensure_user(message.from_user)
    now = datetime.utcnow()

    if user["last_hourly"] and now - user["last_hourly"] < HOURLY_COOLDOWN:
        remaining = HOURLY_COOLDOWN - (now - user["last_hourly"])
        return await message.reply_text(
            f"⏳ Come back in {remaining.seconds//60} minutes"
        )

    await user_collection.update_one(
        {"id": user["id"]},
        {
            "$inc": {"balance": HOURLY_REWARD},
            "$set": {"last_hourly": now}
        }
    )

    await message.reply_text(
        f"⏰ You received <b>{HOURLY_REWARD}</b> coins!",
        parse_mode=ParseMode.HTML
            )
