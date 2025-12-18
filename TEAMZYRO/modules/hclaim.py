import asyncio
import random
from datetime import datetime, timedelta

from pyrogram import filters, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from TEAMZYRO import ZYRO as bot
from TEAMZYRO import user_collection, collection

# ─────────────────────────────
# CONFIG
# ─────────────────────────────

SUPPORT_CHANNEL = "cute_character_support"  # without @

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


def format_time_delta(delta):
    seconds = int(delta.total_seconds())
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"


async def user_joined_channel(user_id):
    try:
        member = await bot.get_chat_member(f"@{SUPPORT_CHANNEL}", user_id)
        return member.status in ("member", "administrator", "creator")
    except:
        return False


async def get_unique_character(user_id, rarity):
    user_data = await user_collection.find_one(
        {"id": user_id},
        {"characters.id": 1}
    )
    claimed_ids = [c["id"] for c in user_data.get("characters", [])] if user_data else []

    character = await collection.aggregate([
        {
            "$match": {
                "rarity": {"$regex": f"^{rarity}$", "$options": "i"},
                "id": {"$nin": claimed_ids},
                "img_url": {"$exists": True, "$ne": ""}
            }
        },
        {"$sample": {"size": 1}}
    ]).to_list(1)

    return character[0] if character else None


# ─────────────────────────────
# CLAIM COMMAND
# ─────────────────────────────

@bot.on_message(filters.command(["hclaim", "claim"]))
async def claim_cmd(_, message: t.Message):
    user_id = message.from_user.id
    mention = message.from_user.mention

    if user_id in claim_lock:
        return await message.reply_text("⏳ Please wait, your claim is being processed.")

    claim_lock[user_id] = True

    try:
        # ─── Channel join check ───────────────────────────
        if not await user_joined_channel(user_id):
            join_btn = InlineKeyboardMarkup(
                [[InlineKeyboardButton(
                    "🔔 Join Channel",
                    url=f"https://t.me/{SUPPORT_CHANNEL}"
                )]]
            )
            return await message.reply_text(
                "🔒 **You must join the support channel to claim your daily character.**",
                reply_markup=join_btn
            )

        # ─── Get / create user ────────────────────────────
        user = await user_collection.find_one({"id": user_id})
        if not user:
            user = {
                "id": user_id,
                "username": message.from_user.username,
                "characters": [],
                "last_daily_reward": None
            }
            await user_collection.insert_one(user)

        # ─── Daily cooldown (24h) ─────────────────────────
        last = user.get("last_daily_reward")
        if last and datetime.utcnow() - last < timedelta(days=1):
            remaining = timedelta(days=1) - (datetime.utcnow() - last)
            return await message.reply_text(
                f"⏳ **You've already claimed today!**\n"
                f"Next claim in: `{format_time_delta(remaining)}`"
            )

        # ─── Roll rarity ──────────────────────────────────
        rarity = roll_rarity()

        # ─── Fetch character ──────────────────────────────
        char = await get_unique_character(user_id, rarity)

        # Fallback if rarity pool empty
        if not char:
            char = await collection.aggregate([
                {"$match": {"img_url": {"$exists": True, "$ne": ""}}},
                {"$sample": {"size": 1}}
            ]).to_list(1)
            char = char[0] if char else None

        if not char:
            return await message.reply_text("❌ No characters available right now.")

        # ─── Update user ──────────────────────────────────
        await user_collection.update_one(
            {"id": user_id},
            {
                "$push": {"characters": char},
                "$set": {"last_daily_reward": datetime.utcnow()}
            }
        )

        # ─── Send reward ──────────────────────────────────
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

    except Exception as e:
        print("CLAIM ERROR:", e)
        await message.reply_text("❌ An unexpected error occurred.")

    finally:
        claim_lock.pop(user_id, None)o
