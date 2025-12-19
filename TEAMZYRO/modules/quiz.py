import random
from pyrogram import filters
from TEAMZYRO import app, collection, user_collection

# ─────────────────────────────
# CONFIG
# ─────────────────────────────

REWARD_COINS = 50

RARITY_POOL = [
    "Low",
    "Medium",
    "High",
    "Special Edition",
    "Elite Edition",
    "Exclusive",
    "Valentine",
    "Halloween",
    "Winter",
    "Summer",
    "Royal",
    "Luxury Edition"
]

RARITY_EMOJI = {
    "Low": "⚪️",
    "Medium": "🟠",
    "High": "🔴",
    "Special Edition": "🎩",
    "Elite Edition": "🪽",
    "Exclusive": "🪐",
    "Valentine": "💞",
    "Halloween": "🎃",
    "Winter": "❄️",
    "Summer": "🏖",
    "Royal": "🎗",
    "Luxury Edition": "💸"
}

# ─────────────────────────────
# RANDOM CHARACTER FETCH
# ─────────────────────────────

async def get_random_character():
    rarity = random.choice(RARITY_POOL)

    char = await collection.aggregate([
        {"$match": {"rarity": rarity}},
        {"$sample": {"size": 1}}
    ]).to_list(1)

    if char:
        return char[0]

    # fallback (if rarity empty)
    fallback = await collection.aggregate([
        {"$sample": {"size": 1}}
    ]).to_list(1)

    return fallback[0] if fallback else None


# ─────────────────────────────
# /guess COMMAND
# ─────────────────────────────

@app.on_message(filters.command("guess"))
async def guess_cmd(_, message):
    user_id = message.from_user.id

    user = await user_collection.find_one({"id": user_id})
    if not user:
        user = {
            "id": user_id,
            "coins": 0,
            "active_guess": None
        }
        await user_collection.insert_one(user)

    # If already guessing, show same character
    if user.get("active_guess"):
        char = user["active_guess"]
    else:
        char = await get_random_character()
        if not char:
            return await message.reply_text("❌ No characters available.")

        await user_collection.update_one(
            {"id": user_id},
            {"$set": {"active_guess": char}}
        )

    rarity = char.get("rarity", "Unknown")
    emoji = RARITY_EMOJI.get(rarity, "❓")

    await message.reply_photo(
        char["img_url"],
        caption=(
            "🎯 **GUESS THE CHARACTER!**\n\n"
            f"{emoji} **Rarity:** `{rarity}`\n\n"
            "✍️ Type character name using:\n"
            "`/answer <name>`"
        )
    )


# ─────────────────────────────
# /answer COMMAND
# ─────────────────────────────

@app.on_message(filters.command("answer"))
async def answer_cmd(_, message):
    user_id = message.from_user.id
    args = message.command

    if len(args) < 2:
        return await message.reply_text("Usage: `/answer <character name>`")

    user_answer = " ".join(args[1:]).lower()

    user = await user_collection.find_one({"id": user_id})
    if not user or not user.get("active_guess"):
        return await message.reply_text("❌ No active guess. Use /guess first.")

    char = user["active_guess"]
    correct_name = char["name"].lower()

    # ❌ WRONG ANSWER
    if user_answer != correct_name:
        return await message.reply_text("❌ Wrong guess! Try again 😈")

    # ✅ CORRECT ANSWER
    new_coins = user.get("coins", 0) + REWARD_COINS

    await user_collection.update_one(
        {"id": user_id},
        {
            "$set": {"coins": new_coins, "active_guess": None}
        }
    )

    rarity = char.get("rarity", "Unknown")
    emoji = RARITY_EMOJI.get(rarity, "❓")

    await message.reply_text(
        "✨ **CORRECT GUESS!** ✨\n\n"
        f"👤 **{char['name']}**\n"
        f"{emoji} **Rarity:** `{rarity}`\n\n"
        f"💰 **+{REWARD_COINS} coins earned!**\n"
        f"🏦 Total Coins: `{new_coins}`\n\n"
        "➡️ Use /guess for next character!"
    )
