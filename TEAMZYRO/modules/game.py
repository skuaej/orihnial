
import random
import time
from pyrogram import filters
from pyrogram.types import Message

from TEAMZYRO import app, user_collection

# ─── CONFIG ───────────────────────────────
MIN_BET = 10
MAX_BET = 500
DUEL_COOLDOWN = 20  # seconds

duel_cd = {}  # in-memory cooldown (lightweight)


# ─── ENSURE USER (AUTO FIX) ───────────────
async def ensure_user(user):
    data = await user_collection.find_one({"id": user.id})

    if not data:
        data = {
            "id": user.id,
            "first_name": user.first_name,
            "username": user.username,
            "balance": 0,
            "duel_streak": 0
        }
        await user_collection.insert_one(data)
        return data

    updates = {}

    if "balance" not in data:
        updates["balance"] = 0
    if "duel_streak" not in data:
        updates["duel_streak"] = 0
    if "first_name" not in data:
        updates["first_name"] = user.first_name
    if "username" not in data:
        updates["username"] = user.username

    if updates:
        await user_collection.update_one(
            {"id": user.id},
            {"$set": updates}
        )
        data.update(updates)

    return data


# ─── DUEL GAME ────────────────────────────
@app.on_message(filters.command("duel"))
async def duel_game(_, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("❌ Reply to a user to start a duel.")

    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        return await message.reply_text("❌ Usage: /duel <bet>")

    bet = int(args[1])
    if bet < MIN_BET or bet > MAX_BET:
        return await message.reply_text(
            f"❌ Bet must be between {MIN_BET} and {MAX_BET} coins."
        )

    user1 = message.from_user
    user2 = message.reply_to_message.from_user

    if user1.id == user2.id:
        return await message.reply_text("❌ You cannot duel yourself.")

    now = time.time()
    if user1.id in duel_cd and now - duel_cd[user1.id] < DUEL_COOLDOWN:
        return await message.reply_text("⏳ Duel cooldown active.")

    duel_cd[user1.id] = now

    u1 = await ensure_user(user1)
    u2 = await ensure_user(user2)

    if u1["balance"] < bet or u2["balance"] < bet:
        return await message.reply_text("❌ One player has insufficient balance.")

    # 🎯 PICK WINNER (40% win chance for challenger)
    winner = user1 if random.random() <= 0.4 else user2
    loser = user2 if winner.id == user1.id else user1

    # Update balances
    await user_collection.update_one(
        {"id": winner.id},
        {"$inc": {"balance": bet, "duel_streak": 1}}
    )
    await user_collection.update_one(
        {"id": loser.id},
        {"$inc": {"balance": -bet}, "$set": {"duel_streak": 0}}
    )

    # Fetch updated streak
    winner_data = await user_collection.find_one({"id": winner.id})
    streak = winner_data.get("duel_streak", 0)

    # Names
    winner_name = f"@{winner.username}" if winner.username else winner.first_name
    loser_name = f"@{loser.username}" if loser.username else loser.first_name

    await message.reply_text(
        f"⚔️ **DUEL RESULT**\n\n"
        f"🏆 **Winner:** {winner_name}\n"
        f"💀 **Loser:** {loser_name}\n"
        f"💰 **Won:** {bet} coins\n"
        f"🔥 **Win Streak:** {streak}",
        parse_mode="markdown"
    )


# ─── DUEL LEADERBOARD ─────────────────────
@app.on_message(filters.command("duelboard"))
async def duel_leaderboard(_, message: Message):
    users = await user_collection.find().sort("duel_streak", -1).limit(10).to_list(10)

    text = "🏆 **DUEL STREAK LEADERBOARD**\n\n"

    for i, u in enumerate(users, 1):
        name = (
            f"@{u['username']}" if u.get("username")
            else u.get("first_name", "Unknown")
        )
        streak = u.get("duel_streak", 0)
        text += f"{i}. {name} → 🔥 {streak}\n"

    await message.reply_text(text, parse_mode="markdown")
