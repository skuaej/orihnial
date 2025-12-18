import time
import random
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import DiceEmoji

from TEAMZYRO import app, user_collection

# ─── CONFIG ─────────────────────────────
WIN_RATE = 0.40  # 40%
COOLDOWNS = {
    "slot": 30,
    "dice": 20,
    "alien": 30,
    "duel": 30
}

cooldown_cache = {}

# ─── HELPERS ────────────────────────────
def in_cooldown(user_id, cmd):
    now = time.time()
    key = f"{user_id}:{cmd}"

    if key in cooldown_cache:
        left = COOLDOWNS[cmd] - (now - cooldown_cache[key])
        if left > 0:
            return int(left)

    cooldown_cache[key] = now
    return 0


async def get_user(user):
    data = await user_collection.find_one({"id": user.id})
    if not data:
        data = {
            "id": user.id,
            "first_name": user.first_name,
            "balance": 0
        }
        await user_collection.insert_one(data)
    return data


async def update_balance(user_id, amount):
    await user_collection.update_one(
        {"id": user_id},
        {"$inc": {"balance": amount}},
        upsert=True
    )

# ─── 🎰 SLOT GAME ───────────────────────
@app.on_message(filters.command("slot"))
async def slot_game(_, message: Message):
    cd = in_cooldown(message.from_user.id, "slot")
    if cd:
        return await message.reply_text(f"⏳ Cooldown: {cd}s")

    if len(message.command) < 2:
        return await message.reply_text("Usage: `/slot <bet>`")

    bet = int(message.command[1])
    user = await get_user(message.from_user)

    if user["balance"] < bet:
        return await message.reply_text("❌ Insufficient balance")

    dice = await message.reply_dice(DiceEmoji.SLOT_MACHINE)
    win = random.random() <= WIN_RATE

    if win:
        await update_balance(user["id"], bet)
        await message.reply_text(f"🎉 **You WON!** +{bet} coins")
    else:
        await update_balance(user["id"], -bet)
        await message.reply_text(f"💥 **You LOST!** -{bet} coins")


# ─── 🎲 DICE GAME ───────────────────────
@app.on_message(filters.command("dice"))
async def dice_game(_, message: Message):
    cd = in_cooldown(message.from_user.id, "dice")
    if cd:
        return await message.reply_text(f"⏳ Cooldown: {cd}s")

    if len(message.command) < 2:
        return await message.reply_text("Usage: `/dice <bet>`")

    bet = int(message.command[1])
    user = await get_user(message.from_user)

    if user["balance"] < bet:
        return await message.reply_text("❌ Insufficient balance")

    dice = await message.reply_dice(DiceEmoji.DICE)
    win = random.random() <= WIN_RATE

    if win:
        await update_balance(user["id"], bet)
        await message.reply_text(f"🎲 You won **{bet} coins**!")
    else:
        await update_balance(user["id"], -bet)
        await message.reply_text(f"🎲 You lost **{bet} coins**")


# ─── 👽 ALIEN GAME ──────────────────────
@app.on_message(filters.command("alien"))
async def alien_game(_, message: Message):
    cd = in_cooldown(message.from_user.id, "alien")
    if cd:
        return await message.reply_text(f"⏳ Cooldown: {cd}s")

    if len(message.command) < 2:
        return await message.reply_text("Usage: `/alien <bet>`")

    bet = int(message.command[1])
    user = await get_user(message.from_user)

    if user["balance"] < bet:
        return await message.reply_text("❌ Insufficient balance")

    dice = await message.reply_dice(DiceEmoji.DART)
    win = random.random() <= WIN_RATE

    if win:
        await update_balance(user["id"], bet)
        await message.reply_text(f"👽 Alien spared you! +{bet}")
    else:
        await update_balance(user["id"], -bet)
        await message.reply_text(f"👽 Alien destroyed you! -{bet}")


# ─── ⚔ DUEL GAME ────────────────────────
@app.on_message(filters.command("duel"))
async def duel_game(_, message: Message):
    cd = in_cooldown(message.from_user.id, "duel")
    if cd:
        return await message.reply_text(f"⏳ Cooldown: {cd}s")

    if not message.reply_to_message:
        return await message.reply_text("Reply to a user to duel")

    bet = int(message.command[1])
    p1 = await get_user(message.from_user)
    p2 = await get_user(message.reply_to_message.from_user)

    if p1["balance"] < bet or p2["balance"] < bet:
        return await message.reply_text("❌ One player has insufficient balance")

    d1 = random.randint(1, 6)
    d2 = random.randint(1, 6)

    if d1 == d2:
        return await message.reply_text("⚔ Duel Draw!")

    winner = p1 if d1 > d2 else p2
    loser = p2 if winner == p1 else p1

    await update_balance(winner["id"], bet)
    await update_balance(loser["id"], -bet)

    await message.reply_text(
        f"⚔ **Duel Result**\n"
        f"🎲 {p1['first_name']} rolled {d1}\n"
        f"🎲 {p2['first_name']} rolled {d2}\n\n"
        f"🏆 Winner: {winner['first_name']} +{bet}"
    )
