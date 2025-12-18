import asyncio
import random
from datetime import datetime, timedelta

from pyrogram import filters, types as t
from TEAMZYRO import ZYRO as bot
from TEAMZYRO import user_collection, collection


# ─────────────────────────────
# RARITY ROLL (40 / 30 / 30)
# ─────────────────────────────

def roll_rarity():
    roll = random.randint(1, 100)
    if roll <= 40:
        return "Low"
    elif roll <= 70:
        return "Medium"
    else:
        return "High"


# ─────────────────────────────
# /smash COMMAND
# ─────────────────────────────

@bot.on_message(filters.command("smash"))
async def smash_cmd(_, message: t.Message):
    user = message.from_user
    user_id = user.id
    mention = user.mention

    try:
        # ─── Get or create user ─────────────────────────────
        user_data = await user_collection.find_one({"id": user_id})
        if not user_data:
            user_data = {
                "id": user_id,
                "username": user.username,
                "characters": [],
                "last_smash_time": None
            }
            await user_collection.insert_one(user_data)

        # ─── Cooldown (10 minutes) ──────────────────────────
        last_smash = user_data.get("last_smash_time")
        if last_smash:
            elapsed = datetime.utcnow() - last_smash
            if elapsed < timedelta(minutes=10):
                remaining = timedelta(minutes=10) - elapsed
                mins = int(remaining.total_seconds() // 60)
                secs = int(remaining.total_seconds() % 60)
                return await message.reply_text(
                    f"⏳ **Wait `{mins}m {secs}s` before using /smash again.**"
                )

        # ─── Dice animation ─────────────────────────────────
        dice_msg = await bot.send_dice(
            chat_id=message.chat.id,
            emoji="🎲"
        )
        await asyncio.sleep(2)

        # ─── Roll rarity (BACKEND) ─────────────────────────
        rarity = roll_rarity()

        # ─── Fetch character FROM DB by rarity ─────────────
        character = await collection.aggregate([
            {
                "$match": {
                    "rarity": {"$regex": f"^{rarity}$", "$options": "i"},
                    "img_url": {"$exists": True, "$ne": ""},
                    "name": {"$exists": True},
                    "anime": {"$exists": True}
                }
            },
            {"$sample": {"size": 1}}
        ]).to_list(length=1)

        # ─── Fallback if rarity pool empty ─────────────────
        if not character:
            character = await collection.aggregate([
                {"$sample": {"size": 1}}
            ]).to_list(length=1)

        if not character:
            return await message.reply_text(
                "❌ No characters available in database."
            )

        char = character[0]

        # ─── Store character to user ───────────────────────
        await user_collection.update_one(
            {"id": user_id},
            {
                "$push": {"characters": char},
                "$set": {"last_smash_time": datetime.utcnow()}
            },
            upsert=True
        )

        # ─── Send result ───────────────────────────────────
        caption = (
            f"✨ **SMASH SUCCESSFUL!** ✨\n\n"
            f"👤 **User:** {mention}\n"
            f"💃 **Name:** `{char['name']}`\n"
            f"⭐ **Rarity:** `{char['rarity']}`\n"
            f"📺 **Anime:** `{char['anime']}`"
        )

        await message.reply_photo(
            photo=char["img_url"],
            caption=caption
        )

    except Exception as e:
        print("SMASH ERROR:", e)
        await message.reply_text("❌ Something went wrong in /smash.")
