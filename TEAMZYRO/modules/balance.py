from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
import html

from TEAMZYRO import app, user_collection

# 🔐 ONLY THIS USER CAN ADD BALANCE
BALANCE_GIVER_ID = 1334658171


# ─────────────────────────────────
# ENSURE USER (AUTO FIX)
# ─────────────────────────────────
async def ensure_user(user):
    data = await user_collection.find_one({"id": user.id})

    if not data:
        data = {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "balance": 0,
            "tokens": 0,
            "characters": []
        }
        await user_collection.insert_one(data)
        return data

    updates = {}
    if "balance" not in data:
        updates["balance"] = 0
    if "tokens" not in data:
        updates["tokens"] = 0
    if "characters" not in data:
        updates["characters"] = []

    if updates:
        await user_collection.update_one(
            {"id": user.id},
            {"$set": updates}
        )
        data.update(updates)

    return data


# ─────────────────────────────────
# /balance
# ─────────────────────────────────
@app.on_message(filters.command("balance"))
async def balance_cmd(_, message: Message):
    user = await ensure_user(message.from_user)

    await message.reply_text(
        f"💰 <b>{html.escape(message.from_user.first_name)}'s Balance</b>\n\n"
        f"🪙 Coins: <b>{user['balance']}</b>\n"
        f"🎟 Tokens: <b>{user['tokens']}</b>",
        parse_mode=ParseMode.HTML
    )


# ─────────────────────────────────
# /addbal (ONLY SPECIFIC USER)
# ─────────────────────────────────
@app.on_message(filters.command("addbal"))
async def addbal_cmd(_, message: Message):
    if message.from_user.id != BALANCE_GIVER_ID:
        return await message.reply_text("❌ You are not allowed.")

    parts = message.text.split()
    amount = None
    target_id = None

    for p in parts:
        if p.isdigit():
            amount = int(p)
        elif p.startswith("@"):
            u = await user_collection.find_one({"username": p[1:]})
            if u:
                target_id = u["id"]

    if not amount or not target_id:
        return await message.reply_text(
            "❌ Usage:\n/addbal <amount> @username\n/addbal @username <amount>"
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


# ─────────────────────────────────
# /pay
# ─────────────────────────────────
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
                u = await user_collection.find_one({"username": p[1:]})
                if u:
                    receiver_id = u["id"]

    if not amount or not receiver_id:
        return await message.reply_text(
            "❌ Usage:\n/pay <amount> @username\n/pay @username <amount>"
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
