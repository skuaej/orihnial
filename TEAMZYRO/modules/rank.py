from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import random
import asyncio
import html

from TEAMZYRO import app
from TEAMZYRO import user_collection, top_global_groups_collection

PHOTO_URL = ["https://files.catbox.moe/9j8e6b.jpg"]


# ─── /rank COMMAND ──────────────────────────────────
@app.on_message(filters.command("rank"))
async def rank(client, message):
    cursor = user_collection.find(
        {}, {"_id": 0, "id": 1, "first_name": 1, "characters": 1}
    )
    users = await cursor.to_list(length=None)

    users.sort(key=lambda x: len(x.get("characters", [])), reverse=True)
    users = users[:10]

    caption = "<b>🏆 TOP 10 USERS WITH MOST CHARACTERS</b>\n\n"
    for i, user in enumerate(users, start=1):
        uid = user.get("id")
        name = html.escape(user.get("first_name", "Unknown"))[:15]
        count = len(user.get("characters", []))
        caption += f"{i}. <a href='tg://user?id={uid}'><b>{name}</b></a> ➾ {count}\n"

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🏆 TOP", callback_data="top"),
                InlineKeyboardButton("👥 TOP GROUP", callback_data="top_group"),
            ],
            [
                InlineKeyboardButton("💰 COINS", callback_data="mtop"),
                InlineKeyboardButton("🪙 TOKENS", callback_data="tokens"),
            ],
        ]
    )

    await message.reply_photo(
        photo=random.choice(PHOTO_URL),
        caption=caption,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=buttons
    )


# ─── HELPER TO UPDATE CAPTION ───────────────────────
async def update_caption(callback_query, caption):
    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🏆 TOP", callback_data="top"),
                InlineKeyboardButton("👥 TOP GROUP", callback_data="top_group"),
            ],
            [
                InlineKeyboardButton("💰 COINS", callback_data="mtop"),
                InlineKeyboardButton("🪙 TOKENS", callback_data="tokens"),
            ],
        ]
    )

    await callback_query.edit_message_caption(
        caption=caption,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=buttons
    )


# ─── TOP CHARACTERS ─────────────────────────────────
@app.on_callback_query(filters.regex("^top$"))
async def top_callback(client, callback_query):
    await asyncio.sleep(1)

    users = await user_collection.find().to_list(None)
    users.sort(key=lambda x: len(x.get("characters", [])), reverse=True)
    users = users[:10]

    caption = "<b>🏆 TOP 10 USERS WITH MOST CHARACTERS</b>\n\n"
    for i, u in enumerate(users, start=1):
        caption += (
            f"{i}. <a href='tg://user?id={u['id']}'>"
            f"<b>{html.escape(u.get('first_name','Unknown'))}</b></a>"
            f" ➾ {len(u.get('characters', []))}\n"
        )

    await update_caption(callback_query, caption)


# ─── TOP GROUPS ─────────────────────────────────────
@app.on_callback_query(filters.regex("^top_group$"))
async def top_group_callback(client, callback_query):
    await asyncio.sleep(1)

    cursor = top_global_groups_collection.aggregate([
        {"$project": {"group_name": 1, "count": 1}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ])
    groups = await cursor.to_list(10)

    caption = "<b>👥 TOP 10 GROUPS WITH MOST GUESSES</b>\n\n"
    for i, g in enumerate(groups, start=1):
        caption += f"{i}. <b>{html.escape(g['group_name'])}</b> ➾ {g['count']}\n"

    await update_caption(callback_query, caption)


# ─── COINS LEADERBOARD (FIXED) ──────────────────────
@app.on_callback_query(filters.regex("^mtop$"))
async def mtop_callback(client, callback_query):
    await asyncio.sleep(1)

    users = await user_collection.find(
        {"coins": {"$exists": True}}
    ).sort("coins", -1).limit(10).to_list(10)

    caption = "<b>💰 TOP 10 USERS BY COINS</b>\n\n"
    for i, u in enumerate(users, start=1):
        caption += (
            f"{i}. <a href='tg://user?id={u['id']}'>"
            f"<b>{html.escape(u.get('first_name','Unknown'))}</b></a>"
            f" ➾ 💸 {u.get('coins', 0)}\n"
        )

    await update_caption(callback_query, caption)


# ─── TOKENS LEADERBOARD ─────────────────────────────
@app.on_callback_query(filters.regex("^tokens$"))
async def tokens_callback(client, callback_query):
    await asyncio.sleep(1)

    users = await user_collection.find(
        {"tokens": {"$exists": True}}
    ).sort("tokens", -1).limit(10).to_list(10)

    caption = "<b>🪙 TOP 10 USERS BY TOKENS</b>\n\n"
    for i, u in enumerate(users, start=1):
        caption += (
            f"{i}. <a href='tg://user?id={u['id']}'>"
            f"<b>{html.escape(u.get('first_name','Unknown'))}</b></a>"
            f" ➾ 🪙 {u.get('tokens', 0)}\n"
        )

    await update_caption(callback_query, caption)
