
import random
import time
import html

from pyrogram import filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from TEAMZYRO import app, user_collection

# ─────────────────────────────────
# CONFIG
# ─────────────────────────────────
COOLDOWN = 30
WIN_RATE = 0.40
DUEL_WIN_RATE = 0.50

MIN_BET = 10
MAX_BET = 500

cooldowns = {}
pending_duels = {}

SLOT_EMOJIS = ["🍒", "🍋", "🍉", "🍇", "💎"]


# ─────────────────────────────────
# HELPERS
# ─────────────────────────────────
def cd_left(uid):
    last = cooldowns.get(uid, 0)
    return max(0, COOLDOWN - int(time.time() - last))


def set_cd(uid):
    cooldowns[uid] = time.time()


async def ensure_user(user):
    data = await user_collection.find_one({"id": user.id})
    if not data:
        data = {
            "id": user.id,
            "first_name": user.first_name,
            "username": user.username,
            "balance": 0,
            "game_wins": 0,
            "win_streak": 0
        }
        await user_collection.insert_one(data)
    else:
        updates = {}
        for k in ["balance", "game_wins", "win_streak"]:
            if k not in data:
                updates[k] = 0
        if updates:
            await user_collection.update_one({"id": user.id}, {"$set": updates})
            data.update(updates)
    return data


# ─────────────────────────────────
# 🎰 SLOT GAME
# ─────────────────────────────────
@app.on_message(filters.command("slot"))
async def slot_cmd(_, message: Message):
    user = message.from_user
    data = await ensure_user(user)

    args = message.command
    if len(args) != 2 or not args[1].isdigit():
        return await message.reply_text("Usage: /slot <bet>")

    bet = int(args[1])
    if bet < MIN_BET or bet > MAX_BET or data["balance"] < bet:
        return await message.reply_text("❌ Invalid bet or insufficient balance")

    cd = cd_left(user.id)
    if cd:
        return await message.reply_text(f"⏳ Cooldown: {cd}s")

    set_cd(user.id)
    spin = [random.choice(SLOT_EMOJIS) for _ in range(3)]
    win = random.random() < WIN_RATE

    if win:
        await user_collection.update_one(
            {"id": user.id},
            {"$inc": {"balance": bet * 2, "game_wins": 1, "win_streak": 1}}
        )
        result = f"🎰 {' | '.join(spin)}\n\n🎉 YOU WON +{bet*2}"
    else:
        await user_collection.update_one(
            {"id": user.id},
            {"$inc": {"balance": -bet}, "$set": {"win_streak": 0}}
        )
        result = f"🎰 {' | '.join(spin)}\n\n💀 YOU LOST -{bet}"

    bal = (await user_collection.find_one({"id": user.id}))["balance"]
    await message.reply_text(f"{result}\n\n💰 Balance: {bal}")


# ─────────────────────────────────
# 🎲 DICE GAME
# ─────────────────────────────────
@app.on_message(filters.command("dice"))
async def dice_cmd(_, message: Message):
    user = message.from_user
    data = await ensure_user(user)

    args = message.command
    if len(args) != 2 or not args[1].isdigit():
        return await message.reply_text("Usage: /dice <bet>")

    bet = int(args[1])
    if bet < MIN_BET or bet > MAX_BET or data["balance"] < bet:
        return await message.reply_text("❌ Invalid bet or insufficient balance")

    cd = cd_left(user.id)
    if cd:
        return await message.reply_text(f"⏳ Cooldown: {cd}s")

    set_cd(user.id)
    roll = random.randint(1, 6)
    win = roll >= 4 and random.random() < WIN_RATE

    if win:
        await user_collection.update_one(
            {"id": user.id},
            {"$inc": {"balance": bet, "game_wins": 1, "win_streak": 1}}
        )
        text = f"🎲 Rolled {roll}\n🎉 YOU WON +{bet}"
    else:
        await user_collection.update_one(
            {"id": user.id},
            {"$inc": {"balance": -bet}, "$set": {"win_streak": 0}}
        )
        text = f"🎲 Rolled {roll}\n💀 YOU LOST -{bet}"

    bal = (await user_collection.find_one({"id": user.id}))["balance"]
    await message.reply_text(f"{text}\n\n💰 Balance: {bal}")


# ─────────────────────────────────
# 🪙 FLIP GAME
# ─────────────────────────────────
@app.on_message(filters.command("flip"))
async def flip_cmd(_, message: Message):
    user = message.from_user
    data = await ensure_user(user)

    args = message.command
    if len(args) != 2 or not args[1].isdigit():
        return await message.reply_text("Usage: /flip <bet>")

    bet = int(args[1])
    if bet < MIN_BET or data["balance"] < bet:
        return await message.reply_text("❌ Invalid bet")

    cd = cd_left(user.id)
    if cd:
        return await message.reply_text(f"⏳ Cooldown: {cd}s")

    set_cd(user.id)
    win = random.random() < WIN_RATE

    if win:
        await user_collection.update_one(
            {"id": user.id},
            {"$inc": {"balance": bet, "game_wins": 1, "win_streak": 1}}
        )
        text = f"🪙 YOU WON +{bet}"
    else:
        await user_collection.update_one(
            {"id": user.id},
            {"$inc": {"balance": -bet}, "$set": {"win_streak": 0}}
        )
        text = f"💀 YOU LOST -{bet}"

    bal = (await user_collection.find_one({"id": user.id}))["balance"]
    await message.reply_text(f"{text}\n\n💰 Balance: {bal}")


# ─────────────────────────────────
# ⚔️ DUEL GAME
# ─────────────────────────────────
@app.on_message(filters.command("duel"))
async def duel_cmd(_, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to a user to duel")

    challenger = message.from_user
    opponent = message.reply_to_message.from_user

    await ensure_user(challenger)
    await ensure_user(opponent)

    args = message.command
    if len(args) != 2 or not args[1].isdigit():
        return await message.reply_text("Usage: /duel <bet>")

    bet = int(args[1])

    c = await user_collection.find_one({"id": challenger.id})
    o = await user_collection.find_one({"id": opponent.id})

    if c["balance"] < bet or o["balance"] < bet:
        return await message.reply_text("❌ Insufficient balance")

    duel_id = f"{challenger.id}_{opponent.id}_{int(time.time())}"
    pending_duels[duel_id] = {"c": challenger.id, "o": opponent.id, "bet": bet}

    kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("⚔️ Accept Duel", callback_data=f"accept_duel:{duel_id}")]]
    )

    await message.reply_text(
        f"⚔️ DUEL REQUEST\n\n{challenger.first_name} vs {opponent.first_name}\n💰 Bet: {bet}",
        reply_markup=kb
    )


@app.on_callback_query(filters.regex("^accept_duel:"))
async def accept_duel(_, cq):
    duel_id = cq.data.split(":")[1]
    duel = pending_duels.get(duel_id)
    if not duel:
        return await cq.answer("Expired", show_alert=True)

    if cq.from_user.id != duel["o"]:
        return await cq.answer("Not your duel", show_alert=True)

    winner = duel["c"] if random.random() < DUEL_WIN_RATE else duel["o"]
    loser = duel["o"] if winner == duel["c"] else duel["c"]

    await user_collection.update_one(
        {"id": winner},
        {"$inc": {"balance": duel["bet"], "game_wins": 1, "win_streak": 1}}
    )
    await user_collection.update_one(
        {"id": loser},
        {"$inc": {"balance": -duel["bet"]}, "$set": {"win_streak": 0}}
    )

    w = await user_collection.find_one({"id": winner})
    del pending_duels[duel_id]

    await cq.message.edit_text(
        f"🏆 DUEL RESULT\n\nWinner: {html.escape(w['first_name'])}\n💰 Won: {duel['bet']}"
    )


# ─────────────────────────────────
# 🏆 LEADERBOARD
# ─────────────────────────────────
@app.on_message(filters.command("gameboard"))
async def gameboard(_, message: Message):
    users = await user_collection.find().sort("game_wins", -1).limit(10).to_list(10)

    text = "🎮 GAME LEADERBOARD\n\n"
    for i, u in enumerate(users, 1):
        text += f"{i}. {u['first_name']} → 🏆 {u['game_wins']} | 🔥 {u['win_streak']}\n"

    await message.reply_text(text)
