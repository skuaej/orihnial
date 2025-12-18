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


# ─────────────────────────────
# RARITY ROLL (DISPLAY ONLY)
# ─────────────────────────────

def roll_rarity():
    r = random.randint(1, 100)
    if r <= 40:
        return "Low"
    elif r <= 70:
        return "Medium"
    return "High"


def success_title(action: str, rarity: str) -> str:
    """
    🔔 sound emoji for all
    ✨ glow only for Medium & High
    """
    base = f"{action.upper()} SUCCESSFUL"
    if rarity in ("Medium", "High"):
        base = f"✨✨✨ {base} ✨✨✨"
    return f"🔔 {base}"


# ─────────────────────────────
# PREVIEW HANDLER
# ─────────────────────────────

async def send_preview(message, mode):
    user_id = message.from_user.id
    now = datetime.utcnow()

    user = await user_collection.find_one({"id": user_id})
    if not user:
        user = {
            "id": user_id,
            "characters": [],
            "harem": [],
            "last_smash_time": None,
            "last_propose_time": None
        }
        await user_collection.insert_one(user)

    last_time = user.get("last_smash_time" if mode == "smash" else "last_propose_time")
    cooldown = SMASH_COOLDOWN if mode == "smash" else PROPOSE_COOLDOWN

    if last_time and now - last_time < timedelta(minutes=cooldown):
        rem = timedelta(minutes=cooldown) - (now - last_time)
        m, s = divmod(int(rem.total_seconds()), 60)
        return await message.reply_text(
            f"⏳ Wait `{m}m {s}s` before using /{mode} again."
        )

    rolled_rarity = roll_rarity()

    character = await collection.aggregate([
        {"$match": {"img_url": {"$exists": True, "$ne": ""}}},
        {"$sample": {"size": 1}}
    ]).to_list(1)

    if not character:
        return await message.reply_text("❌ Character database is empty.")

    char = character[0]

    caption = (
        f"👤 **Name:** `{char.get('name','Unknown')}`\n"
        f"📺 **Anime:** `{char.get('anime','Unknown')}`\n"
        f"🆔 **ID:** `{char.get('id','N/A')}`\n"
        f"⭐ **Rarity:** `{rolled_rarity}`\n\n"
        f"❓ Do you want to **{mode.upper()}**?"
    )

    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(
                "✅ Yes",
                callback_data=f"confirm_{mode}_{char.get('id','0')}_{rolled_rarity}"
            ),
            InlineKeyboardButton(
                "❌ Cancel",
                callback_data="cancel_action"
            )
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
# CONFIRM CALLBACK
# ─────────────────────────────

@bot.on_callback_query(filters.regex("^confirm_"))
async def confirm_action(_, cq: CallbackQuery):
    _, mode, char_id, rarity = cq.data.split("_")
    user_id = cq.from_user.id
    now = datetime.utcnow()

    char = await collection.find_one({"id": int(char_id)}) or await collection.find_one({})
    if not char:
        return await cq.answer("Character not found.", show_alert=True)

    success = random.randint(1, 100) <= RARITY_SUCCESS.get(rarity, 50)

    # ❌ FAILURE
    if not success:
        if mode == "smash":
            fail_text = (
                "❌ **Smash Failed!**\n\n"
                "⚔️ The challenger resisted.\n"
                "💨 The opportunity slipped away…"
            )
        else:
            fail_text = (
                "💔 **Propose Failed!**\n\n"
                "✨ The character was not convinced.\n"
                "🍀 Better luck next time."
            )

        await cq.message.edit_caption(fail_text)
        await cq.answer()
        return

    # ✅ SUCCESS
    title = success_title(mode, rarity)

    if mode == "smash":
        update = {
            "$push": {"characters": char},
            "$set": {"last_smash_time": now}
        }
    else:
        update = {
            "$push": {"harem": char},
            "$set": {"last_propose_time": now}
        }

    caption = (
        f"{title}\n\n"
        f"👤 **Name:** `{char.get('name')}`\n"
        f"🆔 **ID:** `{char.get('id','N/A')}`\n"
        f"⭐ **Rarity:** `{rarity}`\n"
        f"📺 **Anime:** `{char.get('anime')}`"
    )

    if mode == "propose":
        caption += "\n\n✨ Added to your harem!"

    await user_collection.update_one({"id": user_id}, update, upsert=True)
    await cq.message.edit_caption(caption)
    await cq.answer("✅ Success!")


# ─────────────────────────────
# CANCEL CALLBACK
# ─────────────────────────────

@bot.on_callback_query(filters.regex("^cancel_action$"))
async def cancel_action(_, cq: CallbackQuery):
    await cq.message.edit_caption("❌ Action cancelled.")
    await cq.answer()
