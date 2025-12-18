import random
import time
from pyrogram import filters, enums
from pyrogram.types import Message

from TEAMZYRO import app, user_collection

# ─────────────────────────────────
# CONFIG
# ─────────────────────────────────
COOLDOWN = 30                 # seconds
BASE_WIN_RATE = 0.40          # 40%
STREAK_BONUS_PER_WIN = 10     # +10 coins per streak level
MAX_STREAK_BONUS = 100        # cap bonus

MIN_BET = 10
MAX_BET = 500

cooldowns = {}  # user_id -> last_time

SLOT_EMOJIS = ["🍒", "🍋", "🍉", "🍇", "💎"]


# ─────────────────────────────────
# HELPERS
# ─────────────────────────────────
def on_cooldown(uid):
    return time.time() - cooldowns.get(uid, 0) < COOLDOWN


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
            "tokens": 0,
            "game_wins": 0,
            "win_streak": 0
        }
        await user_collection.insert_one(data)

    updates = {}
    for k, v in {
        "balance": 0,
        "game_wins": 0,
        "win_streak": 0
    }.items():
        if k not in data:
            updates[k] = v

    if updates:
        await user_collection.update_one({"id": user.id}, {"$set": updates})
        data.update(updates)

    return data


def streak_bonus(streak):
    return min(streak * STREAK_BONUS_PER_WIN, MAX_STREAK_BONUS)


# ─────────────────────────────────
# 🎰 SLOT GAME
# ─────────────────────────────────
@app.on_message(filters.command("slot"))
async def slot_game(_, message: Message):
    user = message.from_user
    await ensure_user(user)

    if on_cooldown(user.id):
        return await message.reply_text("⏳ Cooldown 30s")

    if len(message.command) < 2 or not message.command[1].isdigit():
        return await message.reply_text("❌ Usage: /slot <bet>")

    bet = int(message.command[1])
    if bet < MIN_BET or bet > MAX_BET:
        return await message.reply_text("❌ Invalid bet amount")

    data = await user_collection.find_one({"id": user.id})
    if data["balance"] < bet:
        return await message.reply_text("❌ Insufficient balance")

    set_cd(user.id)

    spin = [random.choice(SLOT_EMOJIS) for _ in range(3)]
    win = random.random() < BASE_WIN_RATE

    if win:
        new_streak = data["win_streak"] + 1
        bonus = streak_bonus(new_streak)
        reward = bet + bonus

        await user_collection.update_one(
            {"id": user.id},
            {
                "$inc": {
                    "balance": reward,
                    "game_wins": 1
                },
                "$set": {"win_streak": new_streak}
            }
        )

        text = (
            "🎰 <b>SLOT WIN!</b>\n\n"
            f"{' | '.join(spin)}\n\n"
            f"🪙 Bet: {bet}\n"
            f"🔥 Streak: {new_streak}\n"
            f"🎁 Bonus: +{bonus}\n"
            f"💰 Won: +{reward}"
        )
    else:
        await user_collection.update_one(
            {"id": user.id},
            {
                "$inc": {"balance": -bet},
                "$set": {"win_streak": 0}
            }
        )

        text = (
            "💀 <b>SLOT LOST</b>\n\n"
            f"{' | '.join(spin)}\n\n"
            f"🪙 Lost: -{bet}\n"
            f"🔥 Streak reset"
        )

    bal = (await user_collection.find_one({"id": user.id}))["balance"]
    text += f"\n\n💰 Balance: <b>{bal}</b>"

    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)


# ─────────────────────────────────
# 🎲 DICE GAME
# ─────────────────────────────────
@app.on_message(filters.command("dice"))
async def dice_game(_, message: Message):
    user = message.from_user
    await ensure_user(user)

    if on_cooldown(user.id):
        return await message.reply_text("⏳ Cooldown 30s")

    if len(message.command) < 2 or not message.command[1].isdigit():
        return await message.reply_text("❌ Usage: /dice <bet>")

    bet = int(message.command[1])
    if bet < MIN_BET or bet > MAX_BET:
        return await message.reply_text("❌ Invalid bet")

    data = await user_collection.find_one({"id": user.id})
    if data["balance"] < bet:
        return await message.reply_text("❌ Insufficient balance")

    set_cd(user.id)

    roll = random.randint(1, 6)
    win = roll >= 4  # simple logic

    if win:
        new_streak = data["win_streak"] + 1
        bonus = streak_bonus(new_streak)
        reward = bet + bonus

        await user_collection.update_one(
            {"id": user.id},
            {
                "$inc": {"balance": reward, "game_wins": 1},
                "$set": {"win_streak": new_streak}
            }
        )

        text = (
            f"🎲 Rolled: <b>{roll}</b>\n"
            f"🔥 Streak: {new_streak}\n"
            f"🎁 Bonus: +{bonus}\n"
            f"💰 Won: +{reward}"
        )
    else:
        await user_collection.update_one(
            {"id": user.id},
            {
                "$inc": {"balance": -bet},
                "$set": {"win_streak": 0}
            }
        )

        text = (
            f"🎲 Rolled: <b>{roll}</b>\n"
            f"💀 Lost: -{bet}\n"
            f"🔥 Streak reset"
        )

    bal = (await user_collection.find_one({"id": user.id}))["balance"]
    text += f"\n\n💰 Balance: <b>{bal}</b>"

    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)


# ─────────────────────────────────
# 🏆 GAME LEADERBOARD
# ─────────────────────────────────
@app.on_message(filters.command("gameboard"))
async def gameboard(_, message: Message):
    users = await user_collection.find().sort("game_wins", -1).limit(10).to_list(10)

    text = "<b>🎮 GAME LEADERBOARD</b>\n\n"
    for i, u in enumerate(users, 1):
        text += f"{i}. {u.get('first_name','?')} → 🏆 {u.get('game_wins',0)} wins\n"

    await message.reply_text(text, parse_mode=enums.ParseMode.HTML)
    

# ─────────────────────────────────
# ⚔️ DUEL GAME
# ─────────────────────────────────

pending_duels = {}  # duel_id -> data


@app.on_message(filters.command("duel"))
async def duel_cmd(_, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("❌ Reply to a user to duel")

    challenger = message.from_user
    opponent = message.reply_to_message.from_user

    if challenger.id == opponent.id:
        return await message.reply_text("❌ You cannot duel yourself")

    if len(message.command) < 2 or not message.command[1].isdigit():
        return await message.reply_text("❌ Usage: /duel <bet>")

    bet = int(message.command[1])
    if bet < MIN_BET or bet > MAX_BET:
        return await message.reply_text("❌ Invalid bet amount")

    c_data = await ensure_user(challenger)
    o_data = await ensure_user(opponent)

    if c_data["balance"] < bet or o_data["balance"] < bet:
        return await message.reply_text("❌ One player has insufficient balance")

    duel_id = f"{challenger.id}_{opponent.id}_{int(time.time())}"

    pending_duels[duel_id] = {
        "challenger": challenger.id,
        "opponent": opponent.id,
        "bet": bet
    }

    kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("⚔️ Accept Duel", callback_data=f"accept_duel:{duel_id}")]]
    )

    await message.reply_text(
        f"⚔️ <b>DUEL REQUEST</b>\n\n"
        f"👤 {challenger.mention} vs {opponent.mention}\n"
        f"💰 Bet: <b>{bet}</b> coins",
        reply_markup=kb,
        parse_mode=enums.ParseMode.HTML
    )


@app.on_callback_query(filters.regex("^accept_duel:"))
async def accept_duel(_, cq):
    duel_id = cq.data.split(":")[1]
    duel = pending_duels.get(duel_id)

    if not duel:
        return await cq.answer("❌ Duel expired", show_alert=True)

    if cq.from_user.id != duel["opponent"]:
        return await cq.answer("❌ This duel is not for you", show_alert=True)

    bet = duel["bet"]
    c_id = duel["challenger"]
    o_id = duel["opponent"]

    c_data = await user_collection.find_one({"id": c_id})
    o_data = await user_collection.find_one({"id": o_id})

    if not c_data or not o_data:
        return await cq.message.edit_text("❌ Duel cancelled (user missing)")

    # Decide winner
    winner_id = c_id if random.random() < DUEL_WIN_RATE else o_id
    loser_id = o_id if winner_id == c_id else c_id

    winner = await user_collection.find_one({"id": winner_id})
    loser = await user_collection.find_one({"id": loser_id})

    # streak & bonus
    new_streak = winner.get("win_streak", 0) + 1
    bonus = min(new_streak * STREAK_BONUS_PER_WIN, MAX_STREAK_BONUS)
    reward = bet + bonus

    await user_collection.update_one(
        {"id": winner_id},
        {
            "$inc": {
                "balance": reward,
                "game_wins": 1
            },
            "$set": {"win_streak": new_streak}
        }
    )

    await user_collection.update_one(
        {"id": loser_id},
        {
            "$inc": {"balance": -bet},
            "$set": {"win_streak": 0}
        }
    )

    del pending_duels[duel_id]

    winner_name = html.escape(winner.get("first_name", "User"))

    await cq.message.edit_text(
        f"🏆 <b>DUEL RESULT</b>\n\n"
        f"👑 Winner: <a href='tg://user?id={winner_id}'>{winner_name}</a>\n"
        f"🔥 Streak: {new_streak}\n"
        f"🎁 Bonus: +{bonus}\n"
        f"💰 Won: +{reward} coins",
        parse_mode=enums.ParseMode.HTML
    )
