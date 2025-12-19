# TEAMZYRO/modules/guess.py

import asyncio
import random
import time
from pyrogram import filters
from pyrogram.types import Message

from TEAMZYRO import app, collection, user_collection

# ================= CONFIG =================

REWARD_COINS = 50
GUESS_TIME = 180  # seconds

RARITY_POOL = {
    1: "⚪️ Low",
    2: "🟠 Medium",
    3: "🔴 High",
    4: "🎩 Special Edition",
    5: "🪽 Elite Edition",
    6: "🪐 Exclusive",
    7: "💞 Valentine",
    8: "🎃 Halloween",
    9: "❄️ Winter",
    10: "🏖 Summer",
    11: "🎗 Royal",
    12: "💸 Luxury Edition"
}

# Active guess per chat
ACTIVE_GUESS = {}

# ================= HELPERS =================

async def get_random_character():
    rarity_name = random.choice(list(RARITY_POOL.values()))
    char = await collection.aggregate([
        {"$match": {"rarity": rarity_name}},
        {"$sample": {"size": 1}}
    ]).to_list(1)

    return char[0] if char else None


async def ensure_user(user_id, name):
    user = await user_collection.find_one({"id": user_id})
    if not user:
        await user_collection.insert_one({
            "id": user_id,
            "first_name": name,
            "coins": 0,
            "characters": []
        })

# ================= /guess =================

@app.on_message(filters.command("guess") & filters.group)
async def start_guess(_, message: Message):
    chat_id = message.chat.id

    if chat_id in ACTIVE_GUESS:
        await message.reply_text("🎮 Guess game already running!")
        return

    char = await get_random_character()
    if not char:
        await message.reply_text("❌ No characters available.")
        return

    ACTIVE_GUESS[chat_id] = {
        "char": char,
        "end": time.time() + GUESS_TIME
    }

    caption = (
        "🎯 **Current Guessing Game**\n\n"
        f"💰 Reward: **{REWARD_COINS} Coins**\n"
        f"⏳ Time Left: **{GUESS_TIME}s**\n\n"
        "✍️ Reply with **character name**!"
    )

    await message.reply_photo(char["img_url"], caption=caption)

    # Auto timeout
    await asyncio.sleep(GUESS_TIME)
    if chat_id in ACTIVE_GUESS:
        del ACTIVE_GUESS[chat_id]
        await message.reply_text("⏱ Guess timed out! Use /guess again.")

# ================= ANSWER HANDLER =================

@app.on_message(filters.text & filters.group)
async def guess_answer(_, message: Message):
    chat_id = message.chat.id

    if chat_id not in ACTIVE_GUESS:
        return

    data = ACTIVE_GUESS[chat_id]
    char = data["char"]

    if time.time() > data["end"]:
        del ACTIVE_GUESS[chat_id]
        return

    if message.text.lower().strip() == char["name"].lower():
        user_id = message.from_user.id
        name = message.from_user.first_name

        await ensure_user(user_id, name)

        await user_collection.update_one(
            {"id": user_id},
            {
                "$inc": {"coins": REWARD_COINS},
                "$push": {"characters": char}
            }
        )

        await message.reply_text(
            f"🎉 **Correct Guess!**\n\n"
            f"✨ You earned **{REWARD_COINS} coins**\n"
            f"🌸 Character: **{char['name']}**\n"
            f"⭐ Rarity: **{char['rarity']}**"
        )

        # New character
        new_char = await get_random_character()
        if new_char:
            ACTIVE_GUESS[chat_id] = {
                "char": new_char,
                "end": time.time() + GUESS_TIME
            }

            await message.reply_photo(
                new_char["img_url"],
                caption=(
                    "🔄 **New Guess Started!**\n\n"
                    f"💰 Reward: **{REWARD_COINS} Coins**\n"
                    f"⏳ Time Left: **{GUESS_TIME}s**\n\n"
                    "✍️ Guess the character!"
                )
            )
        else:
            del ACTIVE_GUESS[chat_id]
