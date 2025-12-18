from datetime import datetime
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from TEAMZYRO import ZYRO as bot
from TEAMZYRO import user_collection, collection

# ─────────────────────────────
# CONFIG
# ─────────────────────────────

PRICES = {
    "low": 500,
    "medium": 1500,
    "high": 3000
}

DAILY_LIMIT = 3 


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

    # 🔁 DAILY RESET
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
# /bazar
# ─────────────────────────────

@bot.on_message(filters.command("bazar"))
async def bazar_cmd(_, message):
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🟢 Low (500)", callback_data="bazar_low")],
            [InlineKeyboardButton("🟠 Medium (1500)", callback_data="bazar_medium")],
            [InlineKeyboardButton("🔴 High (3000)", callback_data="bazar_high")]
        ]
    )

    await message.reply_text(
        "🛒 **Welcome to the Bazar**\n\n"
        "Choose a category:",
        reply_markup=keyboard
    )


# ─────────────────────────────
# SHOW CHARACTER
# ─────────────────────────────

@bot.on_callback_query(filters.regex("^bazar_(low|medium|high)$"))
async def bazar_show(_, cq: CallbackQuery):
    user_id = cq.from_user.id
    rarity_key = cq.data.split("_")[1]
    price = PRICES[rarity_key]

    user = await ensure_user(user_id)

    # 🛑 DAILY LIMIT
    if user["bazar_count"] >= DAILY_LIMIT:
        return await cq.answer(
            "🛑 Daily limit reached!\n15 / 15 purchases",
            show_alert=True
        )

    rarity_map = {
        "low": "Low",
        "medium": "Medium",
        "high": "High"
    }

    # ❌ PREVENT DUPLICATES
    character = await collection.aggregate([
        {
            "$match": {
                "rarity": {"$regex": rarity_map[rarity_key], "$options": "i"},
                "id": {"$nin": user["characters"]},
                "img_url": {"$exists": True, "$ne": ""}
            }
        },
        {"$sample": {"size": 1}}
    ]).to_list(1)

    if not character:
        return await cq.answer(
            "❌ No new characters available.",
            show_alert=True
        )

    char = character[0]

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🛒 BUY",
                    callback_data=f"bazar_buy_{rarity_key}_{char['id']}"
                ),
                InlineKeyboardButton(
                    "➡️ NEXT",
                    callback_data=f"bazar_{rarity_key}"
                )
            ]
        ]
    )

    caption = (
        "🐟 **Ohayou! Check out this character**\n\n"
        f"👤 **Name:** `{char['name']}`\n"
        f"📺 **Anime:** `{char['anime']}`\n"
        f"🆔 **ID:** `{char['id']}`\n"
        f"⭐ **RARITY:** `{char['rarity']}`\n"
        f"💰 **Price:** `{price} coins`\n\n"
        f"🛒 **Purchases today:** `{user['bazar_count']} / {DAILY_LIMIT}`"
    )

    await cq.message.reply_photo(
        photo=char["img_url"],
        caption=caption,
        reply_markup=keyboard
    )

    await cq.answer()


# ─────────────────────────────
# BUY CHARACTER
# ─────────────────────────────

@bot.on_callback_query(filters.regex("^bazar_buy_"))
async def bazar_buy(_, cq: CallbackQuery):
    user_id = cq.from_user.id
    _, _, rarity_key, char_id = cq.data.split("_")
    char_id = int(char_id)

    user = await ensure_user(user_id)
    price = PRICES[rarity_key]

    if user["balance"] < price:
        return await cq.answer(
            "❌ Not enough coins!",
            show_alert=True
        )

    if char_id in user["characters"]:
        return await cq.answer(
            "⚠️ You already own this character!",
            show_alert=True
        )

    await user_collection.update_one(
        {"id": user_id},
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
