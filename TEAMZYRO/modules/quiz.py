import asyncio
import random
from pyrogram import filters
from TEAMZYRO import app, collection, user_collection

# ===== CONFIG =====
REWARD = 50
GUESS_TIME = 160  # seconds

RARITY_POOL = [
    "Low", "Medium", "High",
    "Special Edition", "Elite Edition",
    "Exclusive", "Valentine", "Halloween",
    "Winter", "Summer", "Royal", "Luxury Edition"
]

# group_id -> active game
ACTIVE_GAMES = {}


# ================= START GUESS =================

async def start_guess(chat_id):
    rarity = random.choice(RARITY_POOL)

    char = await collection.aggregate([
        {"$match": {"rarity": rarity, "img_url": {"$exists": True}}},
        {"$sample": {"size": 1}}
    ]).to_list(1)

    if not char:
        return None

    char = char[0]
    ACTIVE_GAMES[chat_id] = {
        "id": char["id"],
        "name": char["name"].lower(),
        "rarity": rarity
    }

    text = (
        f"🎯 **Current Guessing Game**\n\n"
        f"🏷 Rarity: `{rarity}`\n"
        f"💰 Reward: `{REWARD} Coins`\n"
        f"⏳ Time Left: `{GUESS_TIME}s`\n\n"
        f"✍️ Reply with character name!"
    )

    msg = await app.send_photo(chat_id, char["img_url"], caption=text)

    await asyncio.sleep(GUESS_TIME)

    # timeout
    if chat_id in ACTIVE_GAMES:
        await msg.reply_text(
            f"⏰ Time's up!\n"
            f"❌ Correct answer was: **{char['name']}**\n"
            f"🔁 Same character will appear again."
        )
        await start_guess(chat_id)


# ================= COMMAND =================

@app.on_message(filters.command("guess"))
async def guess_cmd(_, message):
    chat_id = message.chat.id

    if chat_id in ACTIVE_GAMES:
        return await message.reply_text("❗ A guessing game is already running!")

    await start_guess(chat_id)


# ================= ANSWER HANDLER =================

@app.on_message(filters.group & filters.text)
async def answer_handler(_, message):
    chat_id = message.chat.id

    if chat_id not in ACTIVE_GAMES:
        return

    game = ACTIVE_GAMES[chat_id]

    if message.text.lower().strip() == game["name"]:
        # WIN
        user_id = message.from_user.id

        await user_collection.update_one(
            {"id": user_id},
            {"$inc": {"balance": REWARD}},
            upsert=True
        )

        await message.reply_text(
            f"🎉 **Correct Guess!**\n\n"
            f"✨ `{game['name'].title()}` guessed correctly!\n"
            f"💰 +{REWARD} Coins awarded!"
        )

        del ACTIVE_GAMES[chat_id]

        # start new game
        await start_guess(chat_id)
