from pyrogram import filters, enums
from pyrogram.types import Message
import html

from TEAMZYRO import app, user_collection

# 🔒 ONLY THIS USER CAN ADD BALANCE
BALANCE_GIVER_ID = 1334658171


# ─────────────────────────────────────────────
# 🔧 GET OR CREATE USER (AUTO FIX)
# ─────────────────────────────────────────────
async def get_user(user):
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
    if "first_name" not in data:
        updates["first_name"] = user.first_name

    if updates:
        await user_collection.update_one({"id": user.id}, {"$set": updates})
        data.update(updates)

    return data


# ─────────────────────────────────────────────
# 💰 BALANCE
# ─────────────────────────────────────────────
@app.on_message(filters.command("balance"))
async def balance_cmd(_, message: Message):
    user = await get_user(message.from_user)

    await message.reply_text(
        f"👤 <b>{html.escape(user['first_name'])}</b>\n\n"
        f"💰 Coins: <b>{user['balance']}</b>\n"
        f"🪙 Tokens: <b>{user['tokens']}</b>",
        parse_mode=enums.ParseMode.HTML
    )


# ─────────────────────────────────────────────
# ➕ ADD BALANCE (ONLY SPECIFIC USER)
# Usage:
# /addbal 500 (reply)
# /addbal 500 @username
# /addbal 500 user_id
# ─────────────────────────────────────────────
@app.on_message(filters.command("addbal"))
async def add_balance_cmd(client, message: Message):
    if message.from_user.id != BALANCE_GIVER_ID:
        return await message.reply_text("❌ You are not allowed to use this command.")

    args = message.command
    if len(args) < 2:
        return await message.reply_text("❌ Usage: /addbal <amount> (reply / @user / id)")

    try:
        amount = int(args[1])
        if amount <= 0:
            raise ValueError
    except ValueError:
        return await message.reply_text("❌ Invalid amount.")

    receiver = None

    if message.reply_to_message:
        receiver = await get_user(message.reply_to_message.from_user)

    elif len(args) >= 3:
        target = args[2]

        if target.startswith("@"):
            receiver = await user_collection.find_one({"username": target[1:]})
        else:
            try:
                receiver = await user_collection.find_one({"id": int(target)})
            except ValueError:
                pass

    if not receiver:
        return await message.reply_text("❌ User not found.")

    await user_collection.update_one(
        {"id": receiver["id"]},
        {"$inc": {"balance": amount}}
    )

    await message.reply_text(
        f"✅ Added <b>{amount}</b> coins to <b>{html.escape(receiver.get('first_name','User'))}</b>",
        parse_mode=enums.ParseMode.HTML
    )


# ─────────────────────────────────────────────
# 💸 PAY
# ─────────────────────────────────────────────
@app.on_message(filters.command("pay"))
async def pay_cmd(client, message: Message):
    sender = await get_user(message.from_user)
    args = message.command

    if len(args) < 2:
        return await message.reply_text("❌ Usage: /pay <amount> (reply / @user)")

    try:
        amount = int(args[1])
        if amount <= 0:
            raise ValueError
    except ValueError:
        return await message.reply_text("❌ Invalid amount.")

    receiver = None

    if message.reply_to_message:
        receiver = await get_user(message.reply_to_message.from_user)

    elif len(args) >= 3:
        target = args[2]

        if target.startswith("@"):
            receiver = await user_collection.find_one({"username": target[1:]})
        else:
            try:
                receiver = await user_collection.find_one({"id": int(target)})
            except ValueError:
                pass

    if not receiver:
        return await message.reply_text("❌ User not found.")

    if receiver["id"] == sender["id"]:
        return await message.reply_text("❌ You cannot pay yourself.")

    if sender["balance"] < amount:
        return await message.reply_text(
            f"❌ Insufficient balance.\nYour balance: {sender['balance']}"
        )

    await user_collection.update_one(
        {"id": sender["id"]},
        {"$inc": {"balance": -amount}}
    )
    await user_collection.update_one(
        {"id": receiver["id"]},
        {"$inc": {"balance": amount}}
    )

    await message.reply_text(
        f"✅ Sent <b>{amount}</b> coins to <b>{html.escape(receiver.get('first_name','User'))}</b>\n"
        f"💰 New Balance: <b>{sender['balance'] - amount}</b>",
        parse_mode=enums.ParseMode.HTML
    )

    await client.send_message(
        receiver["id"],
        f"🎉 You received <b>{amount}</b> coins from <b>{html.escape(sender['first_name'])}</b>",
        parse_mode=enums.ParseMode.HTML
    )
