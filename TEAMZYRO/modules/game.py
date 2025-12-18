import time
import random
from pyrogram import filters
from pyrogram.types import Message

from TEAMZYRO import app, user_collection

# ─── CONFIG ─────────────────────────────
WIN_RATE = 0.40

COOLDOWNS = {
    "slot": 30,
    "dice": 20,
    "alien": 30,
    "duel": 30
}

cooldowns = {}

# ─── HELPERS ────────────────────────────
def check_cooldown(user_id, cmd):
    now = time.time()
    key = f"{user_id}:{cmd}"

    if key in cooldowns:
        remaining = COOLDOWNS[cmd] - (now - cooldowns[key])
        if remaining > 0:
            return int(remaining)

    cooldowns[key] = now
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


async def change_balance(uid, amount):
    await user_collection.update_one(
        {"id": uid},
        {"$inc": {"balance": amount}},
        upsert=True
    )

# ─── 🎰 SLOT ────────────────────────────
@app.on_message(filters.command("slot"))
async def slot(_, message: Message):
    cd = check_cooldown(message.from_user.id, "slot")
    if cd:
        return await message.reply_text(f"⏳ Cooldown: {cd}s")

    if len(message.command) < 2:
        return await message.reply_text("Usage: /slot <bet>")

    bet = int(message.command[1])
    user = await get_user(message.from_user)

    if user["balance"] < bet:
        return await message.reply_text("❌ Insufficient balance")

    await message.reply_dice("🎰")

    if random.random() <= WIN_RATE:
        await change_balance(user["id"], bet)
        await message.reply_text(f"🎉 You WON +{bet} coins")
    else:
        await change_balance(user["id"], -bet)
        await message.reply_text(f"💥 You LOST -{bet} coins")

# ─── 🎲 DICE ────────────────────────────
@app.on_message(filters.command("dice"))
async def dice(_, message: Message):
    cd = check_cooldown(message.from_user.id, "dice")
    if cd:
        return await message.reply_text(f"⏳ Cooldown: {cd}s")

    bet = int(message.command[1])
    user = await get_user(message.from_user)

    if user["balance"] < bet:
        return await message.reply_text("❌ Insufficient balance")

    await message.reply_dice("🎲")

    if random.random() <= WIN_RATE:
        await change_balance(user["id"], bet)
        await message.reply_text(f"🎲 You won {bet} coins")
    else:
        await change_balance(user["id"], -bet)
        await message.reply_text(f"🎲 You lost {bet} coins")

# ─── 👽 ALIEN ───────────────────────────
@app.on_message(filters.command("alien"))
async def alien(_, message: Message):
    cd = check_cooldown(message.from_user.id, "alien")
    if cd:
        return await message.reply_text(f"⏳ Cooldown: {cd}s")

    bet = int(message.command[1])
    user = await get_user(message.from_user)

    if user["balance"] < bet:
        return await message.reply_text("❌ Insufficient balance")

    await message.reply_dice("🎯")

    if random.random() <= WIN_RATE:
        await change_balance(user["id"], bet)
        await message.reply_text(f"👽 Alien spared you! +{bet}")
    else:
        await change_balance(user["id"], -bet)
        await message.reply_text(f"👽 Alien destroyed you! -{bet}")

# ─── ⚔ DUEL ─────────────────────────────
@app.on_message(filters.command("duel"))
async def duel(_, message: Message):
    cd = check_cooldown(message.from_user.id, "duel")
    if cd:
        return await message.reply_text(f"⏳ Cooldown: {cd}s")

    if not message.reply_to_message:
        return await message.reply_text("Reply to a user to duel")

    bet = int(message.command[1])

    p1 = await get_user(message.from_user)
    p2 = await get_user(message.reply_to_message.from_user)

    if p1["balance"] < bet or p2["balance"] < bet:
        return await message.reply_text("❌ One player has insufficient balance")

    r1 = random.randint(1, 6)
    r2 = random.randint(1, 6)

    if r1 == r2:
        return await message.reply_text("⚔ Duel draw!")

    winner = p1 if r1 > r2 else p2
    loser = p2 if winner == p1 else p1

    await change_balance(winner["id"], bet)
    await change_balance(loser["id"], -bet)

    await message.reply_text(
        f"⚔ Duel Result\n"
        f"{p1['first_name']} rolled {r1}\n"
        f"{p2['first_name']} rolled {r2}\n\n"
        f"🏆 Winner: {winner['first_name']} +{bet}"
    )
