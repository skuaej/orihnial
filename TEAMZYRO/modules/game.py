import random
import time
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode

from TEAMZYRO import app, user_collection

# ─── GLOBAL CONFIG ─────────────────────────
SLOT_WIN_RATE = 0.60
SLOT_CD = 30

DICE_CD = 20
QUIZ_CD = 60

MIN_BET = 10
MAX_BET = 500

# cooldown memory (lightweight)
slot_cd = {}
dice_cd = {}
quiz_cd = {}

SLOT_EMOJIS = ["🍒", "🍋", "🍉", "🍇", "💎"]

QUIZ_QUESTIONS = [
    ("Capital of India?", "delhi"),
    ("2 + 2 = ?", "4"),
    ("Telegram owner?", "durov"),
]

# ─── ENSURE USER ───────────────────────────
async def ensure_user(user):
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
    if "balance" not in data:
        await user_collection.update_one(
            {"id": user.id},
            {"$set": {"balance": 0}}
        )
        data["balance"] = 0
    return data


# ─── SLOT GAME ─────────────────────────────
@app.on_message(filters.command("slot"))
async def slot_game(_, message: Message):
    user = message.from_user
    uid = user.id
    args = message.text.split()

    if len(args) != 2 or not args[1].isdigit():
        return await message.reply_text("❌ Usage: /slot <bet>")

    bet = int(args[1])
    if bet < MIN_BET or bet > MAX_BET:
        return await message.reply_text("❌ Invalid bet amount.")

    now = time.time()
    if uid in slot_cd and now - slot_cd[uid] < SLOT_CD:
        return await message.reply_text(
            f"⏳ Cooldown {int(SLOT_CD - (now - slot_cd[uid]))}s"
        )

    user_data = await ensure_user(user)
    if user_data["balance"] < bet:
        return await message.reply_text("❌ Insufficient balance.")

    slot_cd[uid] = now
    spin = [random.choice(SLOT_EMOJIS) for _ in range(3)]
    win = random.random() <= SLOT_WIN_RATE

    text = "🎰 SLOT MACHINE 🎰\n\n" + " | ".join(spin) + "\n\n"

    if win:
        reward = bet * 2
        await user_collection.update_one(
            {"id": uid},
            {"$inc": {"balance": reward}}
        )
        text += f"🎉 YOU WON +{reward} coins!"
    else:
        await user_collection.update_one(
            {"id": uid},
            {"$inc": {"balance": -bet}}
        )
        text += f"💀 YOU LOST -{bet} coins!"

    bal = (await user_collection.find_one({"id": uid}))["balance"]
    text += f"\n\n💰 Balance: {bal}"

    await message.reply_text(text)


# ─── DICE GAME ─────────────────────────────
@app.on_message(filters.command("dice"))
async def dice_game(_, message: Message):
    user = message.from_user
    uid = user.id
    args = message.text.split()

    if len(args) != 2 or not args[1].isdigit():
        return await message.reply_text("❌ Usage: /dice <bet>")

    bet = int(args[1])
    if bet < MIN_BET or bet > MAX_BET:
        return await message.reply_text("❌ Invalid bet.")

    now = time.time()
    if uid in dice_cd and now - dice_cd[uid] < DICE_CD:
        return await message.reply_text("⏳ Dice cooldown active.")

    user_data = await ensure_user(user)
    if user_data["balance"] < bet:
        return await message.reply_text("❌ Insufficient balance.")

    dice_cd[uid] = now
    roll = random.randint(1, 6)

    if roll >= 4:
        await user_collection.update_one(
            {"id": uid},
            {"$inc": {"balance": bet}}
        )
        result = f"🎲 Rolled {roll} → YOU WON +{bet}"
    else:
        await user_collection.update_one(
            {"id": uid},
            {"$inc": {"balance": -bet}}
        )
        result = f"🎲 Rolled {roll} → YOU LOST -{bet}"

    bal = (await user_collection.find_one({"id": uid}))["balance"]
    await message.reply_text(f"{result}\n💰 Balance: {bal}")


# ─── DUEL GAME ─────────────────────────────
@app.on_message(filters.command("duel"))
async def duel_game(_, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("❌ Reply to a user to duel.")

    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        return await message.reply_text("❌ Usage: /duel <bet>")

    bet = int(args[1])
    if bet < MIN_BET or bet > MAX_BET:
        return await message.reply_text("❌ Invalid bet.")

    u1 = message.from_user
    u2 = message.reply_to_message.from_user

    d1 = await ensure_user(u1)
    d2 = await ensure_user(u2)

    if d1["balance"] < bet or d2["balance"] < bet:
        return await message.reply_text("❌ One player has insufficient balance.")

    winner = random.choice([u1, u2])
    loser = u2 if winner.id == u1.id else u1

    await user_collection.update_one(
        {"id": winner.id},
        {"$inc": {"balance": bet}}
    )
    await user_collection.update_one(
        {"id": loser.id},
        {"$inc": {"balance": -bet}}
    )

    await message.reply_text(
        f"⚔️ DUEL RESULT\n\n"
        f"🏆 Winner: {winner.mention}\n"
        f"💀 Loser: {loser.mention}\n"
        f"💰 Bet: {bet}"
    )


# ─── QUIZ GAME ─────────────────────────────
@app.on_message(filters.command("quiz"))
async def quiz_game(_, message: Message):
    user = message.from_user
    uid = user.id

    now = time.time()
    if uid in quiz_cd and now - quiz_cd[uid] < QUIZ_CD:
        return await message.reply_text("⏳ Quiz cooldown active.")

    q, ans = random.choice(QUIZ_QUESTIONS)
    quiz_cd[uid] = now

    await message.reply_text(f"🧠 QUIZ\n\n{q}")

    try:
        reply = await app.listen(message.chat.id, timeout=15)
    except:
        return await message.reply_text("⏱ Time up!")

    if reply.text.lower().strip() == ans:
        reward = 100
        await user_collection.update_one(
            {"id": uid},
            {"$inc": {"balance": reward}}
        )
        await message.reply_text(f"✅ Correct! +{reward} coins")
    else:
        await message.reply_text("❌ Wrong answer!")


# ─── GAME LEADERBOARD ──────────────────────
@app.on_message(filters.command("gameleaderboard"))
async def game_leaderboard(_, message: Message):
    users = await user_collection.find().sort("balance", -1).limit(10).to_list(10)

    text = "🏆 GAME LEADERBOARD 🏆\n\n"
    for i, u in enumerate(users, 1):
        name = u.get("first_name", "Unknown")
        bal = u.get("balance", 0)
        text += f"{i}. {name} → 💰 {bal}\n"

    await message.reply_text(text)
