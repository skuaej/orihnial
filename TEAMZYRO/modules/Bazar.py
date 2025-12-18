
import random
from datetime import datetime

from pyrogram import filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    InputMediaPhoto
)

from TEAMZYRO import ZYRO as bot
from TEAMZYRO import user_collection, collection


# ─────────────────────────────
# CONFIG
# ─────────────────────────────

PRICES = {
    "Low": 500,
    "Medium": 1500,
    "High": 3000
}

DAILY_LIMIT = 15


# ─────────────────────────────
# UTILS
# ─────────────────────────────

def today_str():
    return datetime.utcnow().strftime("%Y-%m-%d")


async def ensure_user(user_id):
    user = await user_collection.find_one({"id": user_id})

    if not user:
        user = {
            "id": user_id,
            "balance": 0,
            "characters": [],
            "bazar_count": 0,
            "bazar_date": today_str()
        }
        await user_collection.insert_one(user)

    # 🔄 DAILY RESET
    if user.get("bazar_date") != today_str():
        await user_collection.update_one(
            {"id": user_id},
            {
                "$set": {
                    "bazar_count": 0,
                    "bazar_date": today_str()
                }
            }
        )
        user["bazar_count"] = 0
        user["bazar_date"] = today_str()

    return user


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
# /bazar COMMAND
# ─────────────────────────────

@bot.on_message(filters.command("bazar"))
async def bazar_cmd(_, message):
    await show_character(message.from_user.id, message, edit=False)


# ─────────────────────────────
# SHOW CHARACTER (SEND / EDIT)
# ─────────────────────────────

async def show_character(user_id, ctx, edit=False):
    user = await ensure_user(user_id)

    if user["bazar_count"] >= DAILY_LIMIT:
        text = (
            "🛑 **Daily limit reached**\n"
            "🛒 Purchases today: **15 / 15**"
        )
        if edit:
            return await ctx.message.edit_text(text)
        return await ctx.reply_text(text)

    rarity = roll_rarity()
    price = PRICES[rarity]

    # ✅ Always fetch from DB (duplicates allowed to show)
    character = await collection.aggregate([
        {
            "$match": {
                "rarity": {"$regex": rarity, "$options": "i"}
            }
        },
        {"$sample": {"size": 1}}
    ]).to_list(1)

    if not character:
        msg = "❌ Character database is empty."
        if edit:
            return await ctx.message.edit_text(msg)
        return await ctx.reply_text(msg)

    char = character[0]
    owned = char["id"] in user["characters"]

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "❌ OWNED" if owned else "🛒 BUY",
                    callback_data="owned"
                    if owned
                    else f"bazar_buy_{char['id']}_{rarity}"
                ),
                InlineKeyboardButton(
                    "➡️ NEXT",
                    callback_data="bazar_next"
                )
            ]
        ]
    )

    caption = (
        "🐟 **Ohayou! Check out this character**\n\n"
        f"👤 **Name:** `{char['name']}`\n"
        f"📺 **Anime:** `{char['anime']}`\n"
        f"🆔 **ID:** `{char['id']}`\n"
        f"⭐ **Rarity:** `{rarity}`\n"
        f"💰 **Price:** `{price} coins`\n\n"
        f"🛒 **Purchases today:** `{user['bazar_count']} / {DAILY_LIMIT}`"
    )

    if edit:
        await ctx.message.edit_media(
            media=InputMediaPhoto(
                media=char["img_url"],
                caption=caption
            ),
            reply_markup=keyboard
        )
    else:
        await ctx.reply_photo(
            photo=char["img_url"],
            caption=caption,
            reply_markup=keyboard
        )


# ─────────────────────────────
# NEXT BUTTON (SILENT, EDIT SAME MESSAGE)
# ─────────────────────────────

@bot.on_callback_query(filters.regex("^bazar_next$"))
async def bazar_next(_, cq: CallbackQuery):
    await cq.answer()  # ✅ silent (no top bar message)
    await show_character(cq.from_user.id, cq, edit=True)


# ─────────────────────────────
# BUY BUTTON
# ─────────────────────────────

@bot.on_callback_query(filters.regex("^bazar_buy_"))
async def bazar_buy(_, cq: CallbackQuery):
    _, _, char_id, rarity = cq.data.split("_")
    char_id = int(char_id)

    user = await ensure_user(cq.from_user.id)
    price = PRICES[rarity]

    if user["balance"] < price:
        return await cq.answer("❌ Not enough coins!", show_alert=True)

    if char_id in user["characters"]:
        return await cq.answer(
            "⚠️ You already own this character!",
            show_alert=True
        )

    if user["bazar_count"] >= DAILY_LIMIT:
        return await cq.answer("🛑 Daily limit reached!", show_alert=True)

    await user_collection.update_one(
        {"id": cq.from_user.id},
        {
            "$inc": {
                "balance": -price,
                "bazar_count": 1
            },
            "$push": {
                "characters": char_id
            }
        }
    )

    await cq.answer("✅ Character purchased!", show_alert=True)


# ─────────────────────────────
# OWNED BUTTON
# ─────────────────────────────

@bot.on_callback_query(filters.regex("^owned$"))
async def owned_cb(_, cq: CallbackQuery):
    await cq.answer("You already own this character.", show_alert=True)
