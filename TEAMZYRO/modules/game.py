import random
from datetime import datetime, timedelta
from pyrogram import filters
from pyrogram.types import Message

from TEAMZYRO import app, user_collection

# ─── CONFIG ─────────────────────────────
WIN_CHANCE = 0.7          # 70%
WIN_REWARD = 30           # coins
LOSE_PENALTY = 50         # coins
COOLDOWN = timedelta(seconds=30)


# ─── ENSURE USER (FIX OLD USERS) ─────────
async def ensure_user(user):
    data = await user_collection.find_one({"id": user.id})

    if not data:
        data = {
            "id": user.id,
            "first_name": user.first_name,
            "username": user.username,
            "balance": 0,
            "last_game": None
        }
        await user_collection.insert_one(data)
        return data

    updates = {}
    if "balance" not in data:
        updates["balance"] = 0
    if "last_game" not in data:
        updates["last_game"] = None

    if updates:
        await user_collection.update_one(
            {"id": user.id},
            {"$set": updates}
        )
        data.update(updates)

    return data


# ─── GAME COMMAND ────────────────────────
@app.on_message(filters.command("play"))
async def play_game(_, message: Message):
    user = await ensure_user(message.from_user)
    now = datetime.utcnow()

    last = user.get("last_game")
    if last and now - last < COOLDOWN:
        remaining = COOLDOWN - (now - last)
        return await message.reply_text(
            f"⏳ Cooldown active!\nTry again in **{int(remaining.total_seconds())}s**"
        )

    # 🎲 GAME LOGIC (70% WIN)
    win = random.random() < WIN_CHANCE

    if win:
        await user_collection.update_one(
            {"id": user["id"]},
            {
                "$inc": {"balance": WIN_REWARD},
                "$set": {"last_game": now}
            }
        )
        await message.reply_text(
            f"🎉 **YOU WON!**\n\n"
            f"🪙 +{WIN_REWARD} coins\n"
            f"💰 New Balance: `{user['balance'] + WIN_REWARD}`"
        )
    else:
        await user_collection.update_one(
            {"id": user["id"]},
            {
                "$inc": {"balance": -LOSE_PENALTY},
                "$set": {"last_game": now}
            }
        )
        await message.reply_text(
            f"💀 **YOU LOST!**\n\n"
            f"🪙 -{LOSE_PENALTY} coins\n"
            f"💰 New Balance: `{max(0, user['balance'] - LOSE_PENALTY)}`"
        )
