import asyncio
import random
from datetime import datetime, timedelta

from pyrogram import filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

from TEAMZYRO import ZYRO as bot
from TEAMZYRO import user_collection, collection


# ─────────────────────────────
# CONFIG
# ─────────────────────────────

SMASH_COOLDOWN = 10  # minutes
PROPOSE_COOLDOWN = 15  # minutes


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
# COMMON PREVIEW HANDLER
# ─────────────────────────────

async def send_preview(message, mode: str):
    user = message.from_user
    user_id = user.id

    # get / create user
    user_data = await user_collection.find_one({"id": user_id})
    if not user_data:
        await user_collection.insert_one({
            "id": user_id,
            "characters": [],
            "harem": [],
            "last_smash_time": None,
            "last_propose_time": None
        })

    # cooldown check
    now = datetime.utcnow()
    if mode == "smash":
        last = user_data.get("last_smash_time")
        cooldown = SMASH_COOLDOWN
    else:
        last = user_data.get("last_propose_time")
        cooldown = PROPOSE_COOLDOWN

    if last and now - last < timedelta(minutes=cooldown):
        remain = timedelta(minutes=cooldown) - (now - last)
        m, s = divmod(int(remain.total_seconds()), 60)
        return await message.reply_text(
            f"⏳ Wait `{m}m {s}s` before using /{mode} again."
        )

    # dice animation
    await bot.send_dice(message.chat.id, "🎲")
    await asyncio.sleep(2)

    # roll rarity
    rarity = roll_rarity()

    # fetch character
    character = await collection.aggregate([
        {
            "$match": {
                "rarity": {"$regex": f"^{rarity}$", "$options": "i"},
                "img_url": {"$exists": True, "$ne": ""}
            }
        },
        {"$sample": {"size": 1}}
    ]).to_list(1)

    if not character:
        return await message.reply_text("❌ No characters available.")

    char = character[0]

    # preview caption
    caption = (
        f"👤 **Name:** `{char['name']}`\n"
        f"📺 **Anime:** `{char['anime']}`\n"
        f"🆔 **ID:** `{char.get('id', 'N/A')}`\n"
        f"⭐ **Rarity:** `{char['rarity']}`\n\n"
        f"❓ Do you want to **{mode.upper()}**?"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Yes",
                    callback_data=f"confirm_{mode}_{char.get('id')}"
                ),
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="cancel_action"
                )
            ]
        ]
    )

    await message.reply_photo(
        photo=char["img_url"],
        caption=caption,
        reply_markup=keyboard
    )


# ─────────────────────────────
# COMMANDS
# ─────────────────────────────

@bot.on_message(filters.command("smash"))
async def smash_cmd(_, message):
    await send_preview(message, "smash")


@bot.on_message(filters.command("propose"))
async def propose_cmd(_, message):
    await send_preview(message, "propose")


# ─────────────────────────────
# CONFIRM CALLBACK
# ─────────────────────────────

@bot.on_callback_query(filters.regex("^confirm_"))
async def confirm_action(_, cq: CallbackQuery):
    _, mode, char_id = cq.data.split("_")
    char_id = int(char_id)
    user_id = cq.from_user.id
    now = datetime.utcnow()

    char = await collection.find_one({"id": char_id})
    if not char:
        return await cq.answer("Character not found.", show_alert=True)

    if mode == "smash":
        update = {
            "$push": {"characters": char},
            "$set": {"last_smash_time": now}
        }
        caption = (
            f"✨ **SMASH SUCCESSFUL!** ✨\n\n"
            f"👤 **Name:** `{char['name']}`\n"
            f"🆔 **ID:** `{char['id']}`\n"
            f"⭐ **Rarity:** `{char['rarity']}`\n"
            f"📺 **Anime:** `{char['anime']}`"
        )
    else:
        update = {
            "$push": {"harem": char},
            "$set": {"last_propose_time": now}
        }
        caption = (
            f"💖 **Proposal Accepted!** 💖\n\n"
            f"👤 **Name:** `{char['name']}`\n"
            f"🆔 **ID:** `{char['id']}`\n"
            f"⭐ **Rarity:** `{char['rarity']}`\n"
            f"📺 **Anime:** `{char['anime']}`\n\n"
            f"✨ Added to your harem!"
        )

    await user_collection.update_one({"id": user_id}, update, upsert=True)

    await cq.message.edit_caption(caption)
    await cq.answer()


# ─────────────────────────────
# CANCEL CALLBACK
# ─────────────────────────────

@bot.on_callback_query(filters.regex("^cancel_action$"))
async def cancel_action(_, cq: CallbackQuery):
    await cq.message.edit_caption("❌ Action cancelled.")
    await cq.answer()
