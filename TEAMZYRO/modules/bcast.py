import random
import time
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from TEAMZYRO import app, user_collection

# ─────────────────────────────────
# CONFIG
# ─────────────────────────────────
COOLDOWN = 30  # seconds
WIN_RATE = 0.40  # 40% win chance
DUEL_WIN_RATE = 0.50  # fair duel

cooldowns = {}        # user_id → last_time
pending_duels = {}    # duel_id → duel data


# ─────────────────────────────────
# HELPERS
# ─────────────────────────────────
def on_cooldown(user_id):
    last = cooldowns.get(user_id, 0)
    return time.time() - last < COOLDOWN


def set_cd(user_id):
    cooldowns[user_id] = time.time()


async def ensure_user(user):
    data = await user_collection.find_one({"id": user.id})
    if not data:
        data = {
            "id": user.id,
            "first_name": user.first_name,
            "username": user.username,
            "balance": 0,
            "tokens": 0,
            "game_wins": 0
        }
        await user_collection.insert_one(data)
    return data


# ─────────────────────────────────
# 🎯 FUN GAME — COIN FLIP
# ─────────────────────────────────
@app.on_message(filters.command("flip"))
async def coin_flip(_, message):
    user = message.from_user
    await ensure_user(user)

    if on_cooldown(user.id):
        return await message.reply_text("⏳ Cooldown 30s")

    args = message.command
    if len(args) < 2 or not args[1].isdigit():
        return await message.reply_text("Usage: /flip <bet>")

    bet = int(args[1])
    data = await user_collection.find_one({"id": user.id})

    if bet <= 0 or data["balance"] < bet:
        return await message.reply_text("❌ Invalid bet or insufficient balance")

    win = random.random() < WIN_RATE
    set_cd(user.id)

    if win:
        await user_collection.update_one(
            {"id": user.id},
            {"$inc": {"balance": bet, "game_wins": 1}}
        )
        await message.reply_text(f"🪙 **YOU WON!** +{bet} coins")
    else:
        await user_collection.update_one(
            {"id": user.id},
            {"$inc": {"balance": -bet}}
        )
        await message.reply_text(f"💀 **YOU LOST!** -{bet} coins")


# ─────────────────────────────────
# ⚔️ DUEL GAME
# ─────────────────────────────────
@app.on_message(filters.command("duel"))
async def duel(_, message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to a user to duel")

    challenger = message.from_user
    opponent = message.reply_to_message.from_user

    await ensure_user(challenger)
    await ensure_user(opponent)

    if challenger.id == opponent.id:
        return await message.reply_text("❌ You can't duel yourself")

    args = message.command
    if len(args) < 2 or not args[1].isdigit():
        return await message.reply_text("Usage: /duel <bet> (reply to user)")

    bet = int(args[1])
    c_data = await user_collection.find_one({"id": challenger.id})
    o_data = await user_collection.find_one({"id": opponent.id})

    if c_data["balance"] < bet or o_data["balance"] < bet:
        return await message.reply_text("❌ One player has insufficient balance")

    duel_id = f"{challenger.id}_{opponent.id}_{int(time.time())}"

    pending_duels[duel_id] = {
        "c": challenger.id,
        "o": opponent.id,
        "bet": bet
    }

    kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("⚔️ Accept Duel", callback_data=f"accept_duel:{duel_id}")]]
    )

    await message.reply_text(
        f"⚔️ **DUEL REQUEST**\n\n"
        f"{challenger.first_name} vs {opponent.first_name}\n"
        f"💰 Bet: {bet} coins",
        reply_markup=kb,
        parse_mode=enums.ParseMode.MARKDOWN
    )


@app.on_callback_query(filters.regex("^accept_duel:"))
async def accept_duel(_, cq):
    duel_id = cq.data.split(":")[1]
    duel = pending_duels.get(duel_id)

    if not duel:
        return await cq.answer("❌ Duel expired", show_alert=True)

    if cq.from_user.id != duel["o"]:
        return await cq.answer("Not your duel", show_alert=True)

    c_id = duel["c"]
    o_id = duel["o"]
    bet = duel["bet"]

    winner = c_id if random.random() < DUEL_WIN_RATE else o_id
    loser = o_id if winner == c_id else c_id

    await user_collection.update_one(
        {"id": winner},
        {"$inc": {"balance": bet, "game_wins": 1}}
    )
    await user_collection.update_one(
        {"id": loser},
        {"$inc": {"balance": -bet}}
    )

    del pending_duels[duel_id]

    await cq.message.edit_text(
        f"🏆 **DUEL RESULT**\n\n"
        f"Winner: <a href='tg://user?id={winner}'>User</a>\n"
        f"💰 Won: {bet} coins",
        parse_mode=enums.ParseMode.HTML
    )


# ─────────────────────────────────
# 🏆 GAME LEADERBOARD
# ─────────────────────────────────
@app.on_message(filters.command("gameboard"))
async def game_leaderboard(_, message):
    users = await user_collection.find().sort("game_wins", -1).limit(10).to_list(10)

    text = "<b>🎮 GAME LEADERBOARD</b>\n\n"
    for i, u in enumerate(users, 1):
        text += f"{i}. {u.get('first_name','?')} → 🏆 {u.get('game_wins',0)} wins\n"

    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)
