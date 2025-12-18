import random
from datetime import datetime

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from TEAMZYRO import ZYRO as bot
from TEAMZYRO import user_collection, collection


# ─────────────────────────────
# CONFIG
# ─────────────────────────────

PRICES = {
    "Low": 500,
    "Medium": 1500,   # Rare
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
        return "Medium"   # Rare
    else:
        return "High"


# ─────────────────────────────
# /bazar COMMAND
# ─────────────────────────────

@bot.on_message(filters.command("bazar"))
async def bazar_cmd(_, message):
    await show_character(message.from_user.id, message)


# ─────────────────────────────
# SHOW CHARACTER
# ─────────────────────────────

async def show_character(user_id, ctx):
    user = await ensure_user(user_id)

    if user["bazar_count"] >= DAILY_LIMIT:
        return await ctx.reply_text(
            "🛑 **Daily limit reached**\n"
            "🛒 Purchases today: **15 / 15**"
        )

    rarity = roll_rarity()
    price = PRICES[rarity]

    # ❌ PREVENT DUPLICATES
    character = await collection.aggregate([
        {
            "$match": {
                "rarity": {"$regex": f"^{rarity}$", "$options": "i"},
                "id": {"$nin": user["characters"]},
                "img_url": {"$exists": True, "$ne": ""}
            }
        },
        {"$sample": {"size": 1}}
    ]).to_list(1)

    # 🔁 FAILSAFE (TRY OTHER RARITIES)
    if not character:
        for alt in ["Low", "Medium", "High"]:
            if alt == rarity:
                continue

            character = await collection.aggregate([
                {
                    "$match": {
                        "rarity": {"$regex": f"^{alt}$", "$options": "i"},
                        "id": {"$nin": user["characters"]},
                        "img_url": {"$exists": True, "$ne": ""}
                    }
                },
                {"$sample": {"size": 1}}
            ]).to_list(1)

            if character:
                rarity = alt
                price = PRICES[rarity]
                break

    if not character:
        return await ctx.reply_text("❌ No new characters available.")

    char = character[0]

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🛒 BUY",
                    callback_data=f"bazar_buy_{char['id']}_{rarity}"
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

    if hasattr(ctx, "message"):
        await ctx.message.reply_photo(
            photo=char["img_url"],
            caption=caption,
            reply_markup=keyboard
        )
    else:
        await ctx.reply_photo(
            photo=char["img_url"],
            caption=caption,
            reply_markup=keyboard
        )


# ─────────────────────────────
# NEXT BUTTON
# ─────────────────────────────

@bot.on_callback_query(filters.regex("^bazar_next$"))
async def bazar_next(_, cq: CallbackQuery):
    await cq.answer()
    await show_character(cq.from_user.id, cq)


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
        return await cq.answer("⚠️ You already own this character!", show_alert=True)

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
