from pyrogram import filters
from pyrogram.types import Message
import html
from TEAMZYRO import app, user_collection

# ─── GET OR CREATE USER ─────────────────────────────
async def get_user(user):
    data = await user_collection.find_one({"id": user.id})

    if not data:
        data = {
            "id": user.id,
            "first_name": user.first_name,
            "username": user.username,
            "balance": 0,
            "tokens": 0,
            "characters": []
        }
        await user_collection.insert_one(data)

    # Auto-fix missing fields
    updates = {}
    if "balance" not in data:
        updates["balance"] = 0
    if "tokens" not in data:
        updates["tokens"] = 0

    if updates:
        await user_collection.update_one({"id": user.id}, {"$set": updates})
        data.update(updates)

    return data


# ─── BALANCE COMMAND ────────────────────────────────
@app.on_message(filters.command("balance"))
async def balance_cmd(_, message: Message):
    user = await get_user(message.from_user)

    await message.reply_text(
        f"💳 **{html.escape(message.from_user.first_name)}'s Balance**\n\n"
        f"🪙 Coins: `{user['balance']}`\n"
        f"🪙 Tokens: `{user['tokens']}`"
    )


# ─── PAY COMMAND ────────────────────────────────────
@app.on_message(filters.command("pay"))
async def pay_cmd(_, message: Message):
    sender = await get_user(message.from_user)
    args = message.command

    if len(args) < 2:
        return await message.reply_text(
            "❌ Usage:\n`/pay amount` (reply to user)\n`/pay amount user_id`"
        )

    try:
        amount = int(args[1])
        if amount <= 0:
            raise ValueError
    except ValueError:
        return await message.reply_text("❌ Amount must be a positive number.")

    # Get receiver
    if message.reply_to_message:
        receiver_id = message.reply_to_message.from_user.id
        receiver_name = message.reply_to_message.from_user.first_name
    elif len(args) >= 3:
        receiver_id = int(args[2])
        receiver_name = "User"
    else:
        return await message.reply_text("❌ Reply to a user or provide user ID.")

    if receiver_id == sender["id"]:
        return await message.reply_text("❌ You cannot pay yourself.")

    if sender["balance"] < amount:
        return await message.reply_text("❌ Insufficient balance.")

    # Transfer coins
    await user_collection.update_one(
        {"id": sender["id"]},
        {"$inc": {"balance": -amount}}
    )

    await user_collection.update_one(
        {"id": receiver_id},
        {
            "$inc": {"balance": amount},
            "$setOnInsert": {
                "id": receiver_id,
                "balance": 0,
                "tokens": 0,
                "characters": []
            }
        },
        upsert=True
    )

    await message.reply_text(
        f"✅ **Payment Successful**\n\n"
        f"💸 Sent `{amount}` coins to **{html.escape(receiver_name)}**\n"
        f"💰 Remaining Balance: `{sender['balance'] - amount}`"
    )

    await app.send_message(
        receiver_id,
        f"🎉 You received `{amount}` coins from **{html.escape(message.from_user.first_name)}**"
    )
