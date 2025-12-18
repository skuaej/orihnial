import random
from datetime import datetime, timedelta

from pyrogram import filters, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from TEAMZYRO import ZYRO as bot
from TEAMZYRO import user_collection, collection


# ─────────────────────────────
# CONFIG
# ─────────────────────────────

SUPPORT_CHAT_ID = -1003555329185  # ✅ YOUR PRIVATE GROUP ID

RARITY_PROBABILITY = {
    "Low": 50,
    "Medium": 30,
    "High": 20
}

claim_lock = {}


# ─────────────────────────────
# HELPERS
# ─────────────────────────────

def roll_rarity():
    roll = random.randint(1, 100)
    upto = 0
    for rarity, chance in RARITY_PROBABILITY.items():
        upto += chance
        if roll <= upto:
            return rarity
    return "Low"


def format_time(delta):
    seconds = int(delta.total_seconds())
    h, r = divmod(seconds, 3600)
    m, s = divmod(r, 60)
    return f"{h}h {m}m {s}s"


async def get_unique_character(user_id, rarity):
    user = await user_collection.find_one(
        {"id": user_id},
        {"characters.id": 1}
    )
    claimed_ids = [c["id"] for c in user.get("characters", [])] if user else []

    char = await collection.aggregate([
        {
            "$match": {
                "rarity": {"$regex": f"^{rarity}$", "$options": "i"},
                "id": {"$nin": claimed_ids},
                "img_url": {"$exists": True, "$ne": ""}
            }
        },
        {"$sample": {"size": 1}}
    ]).to_list(1)

    return char[0] if char else None


# ─────────────────────────────
# CLAIM COMMAND
# ─────────────────────────────

@bot.on_message(filters.command(["hclaim", "claim"]))
async def claim_cmd(_, message: t.Message):
    user_id = message.from_user.id
    mention = message.from_user.mention

    # 🔒 MUST BE USED INSIDE PRIVATE GROUP
    if message.chat.id != SUPPORT_CHAT_ID:
        btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton(
                "🔔 Go to Claim Group",
                url="https://t.me/cute_character_support"
            )]]
        )
        return await message.reply_text(
            "🔒 **Daily claim is only available inside the support group.**",
            reply_markup=btn
        )

    if user_id in claim_lock:
        return await message.reply_text("⏳ Please wait, processing your claim...")

    claim_lock[user_id] = True

    try:
        # Get / create user
        user = await user_collection.find_one({"id": user_id})
        if not user:
            user = {
                "id": user_id,
                "username": message.from_user.username,
                "characters": [],
                "last_daily_reward": None
            }
            await user_collection.insert_one(user)

        # Daily cooldown
        last = user.get("last_daily_reward")
        if last and datetime.utcnow() - last < timedelta(days=1):
            remain = timedelta(days=1) - (datetime.utcnow() - last)
            return await message.reply_text(
                f"⏳ **Already claimed today!**\n"
                f"Next claim in `{format_time(remain)}`"
            )

        # Roll rarity
        rarity = roll_rarity()

        # Fetch unique character
        char = await get_unique_character(user_id, rarity)

        # Fallback if rarity exhausted
        if not char:
            char = await collection.aggregate([
                {"$match": {"img_url": {"$exists": True, "$ne": ""}}},
                {"$sample": {"size": 1}}
            ]).to_list(1)
            char = char[0] if char else None

        if not char:
            return await message.reply_text("❌ No characters available.")

        # Update user
        await user_collection.update_one(
            {"id": user_id},
            {
                "$push": {"characters": char},
                "$set": {"last_daily_reward": datetime.utcnow()}
            }
        )

        # Send reward
        await message.reply_photo(
            photo=char["img_url"],
            caption=(
                f"🎊 **CONGRATULATIONS {mention}!** 🎉\n\n"
                f"👤 **Name:** `{char['name']}`\n"
                f"🆔 **ID:** `{char.get('id','N/A')}`\n"
                f"⭐ **Rarity:** `{char['rarity']}`\n"
                f"📺 **Anime:** `{char['anime']}`\n\n"
                f"⏰ Come back tomorrow for another claim!"
            )
        )

    finally:
        claim_lock.pop(user_id, None)
