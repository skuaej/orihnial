import asyncio
import random
from datetime import datetime, timedelta

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from TEAMZYRO import ZYRO as bot
from TEAMZYRO import user_collection, collection


# ─────────────────────────────
# CONFIG
# ─────────────────────────────

SMASH_COOLDOWN = 10       # minutes
PROPOSE_COOLDOWN = 15     # minutes

RARITY_SUCCESS = {
    "Low": 80,
    "Medium": 60,
    "High": 40
}


def roll_rarity():
    r = random.randint(1, 100)
    if r <= 40:
        return "Low"
    elif r <= 70:
        return "Medium"
    return "High"


# ─────────────────────────────
# PREVIEW HANDLER
# ─────────────────────────────

async def send_preview(message, mode):
    user_id = message.from_user.id
    now = datetime.utcnow()

    user = await user_collection.find_one({"id": user_id}) or {}

    # 🔒 MODE-WISE PENDING CHECK
    if mode == "smash" and user.get("pending_smash"):
        return await message.reply_text(
            "❌ You already have a **SMASH** pending.\n"
            "➡️ First cancel ❌ or confirm ✅ it."
        )

    if mode == "propose" and user.get("pending_propose"):
        return await message.reply_text(
            "❌ You already have a **PROPOSE** pending.\n"
            "➡️ First cancel ❌ or confirm ✅ it."
        )

    last_time = user.get("last_smash_time" if mode == "smash" else "last_propose_time")
    cooldown = SMASH_COOLDOWN if mode == "smash" else PROPOSE_COOLDOWN

    if last_time and now - last_time < timedelta(minutes=cooldown):
        rem = timedelta(minutes=cooldown) - (now - last_time)
        m, s = divmod(int(rem.total_seconds()), 60)
        return await message.reply_text(
            f"⏳ Wait `{m}m {s}s` before using /{mode} again."
        )

    await bot.send_dice(message.chat.id, "🎲")
    await asyncio.sleep(2)

    rarity = roll_rarity()

    char = await collection.aggregate([
        {"$match": {"img_url": {"$exists": True, "$ne": ""}}},
        {"$sample": {"size": 1}}
    ]).to_list(1)

    if not char:
        return await message.reply_text("❌ Character database empty.")

    char = char[0]

    # ✅ SAVE FULL CHARACTER (NO ID LOOKUP LATER)
    field = "pending_smash" if mode == "smash" else "pending_propose"
    await user_collection.update_one(
        {"id": user_id},
        {"$set": {field: {
            "char": char,
            "rarity": rarity,
            "time": now
        }}},
        upsert=True
    )

    caption = (
        f"👤 **Name:** `{char.get('name')}`\n"
        f"📺 **Anime:** `{char.get('anime')}`\n"
        f"🆔 **ID:** `{char.get('id')}`\n"
        f"⭐ **Rarity:** `{rarity}`\n\n"
        f"❓ Do you want to **{mode.upper()}**?"
    )

    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("✅ Yes", callback_data=f"confirm_{mode}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{mode}")
        ]]
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
# CONFIRM
# ─────────────────────────────

@bot.on_callback_query(filters.regex("^confirm_"))
async def confirm_action(_, cq: CallbackQuery):
    mode = cq.data.split("_")[1]
    user_id = cq.from_user.id
    now = datetime.utcnow()

    field = "pending_smash" if mode == "smash" else "pending_propose"
    user = await user_collection.find_one({"id": user_id})

    data = user.get(field)
    if not data:
        return await cq.answer("No pending action.", show_alert=True)

    char = data["char"]
    rarity = data["rarity"]

    success = random.randint(1, 100) <= RARITY_SUCCESS.get(rarity, 50)

    if not success:
        await cq.message.edit_caption("❌ **Failed!** Better luck next time.")
    else:
        if mode == "smash":
            await user_collection.update_one(
                {"id": user_id},
                {
                    "$push": {"characters": char},
                    "$set": {"last_smash_time": now}
                }
            )
            await cq.message.edit_caption(f"🔥 **SMASH SUCCESS!**\n`{char['name']}` added.")
        else:
            await user_collection.update_one(
                {"id": user_id},
                {
                    "$push": {"harem": char},
                    "$set": {"last_propose_time": now}
                }
            )
            await cq.message.edit_caption(f"💖 **PROPOSAL ACCEPTED!**\n`{char['name']}` joined your harem.")

    await user_collection.update_one(
        {"id": user_id},
        {"$unset": {field: ""}}
    )

    await cq.answer("Done ✅")


# ─────────────────────────────
# CANCEL
# ─────────────────────────────

@bot.on_callback_query(filters.regex("^cancel_"))
async def cancel_action(_, cq: CallbackQuery):
    mode = cq.data.split("_")[1]
    user_id = cq.from_user.id

    field = "pending_smash" if mode == "smash" else "pending_propose"

    await user_collection.update_one(
        {"id": user_id},
        {"$unset": {field: ""}}
    )

    await cq.message.edit_caption("❌ Action cancelled.")
    await cq.answer("Cancelled ❌")
