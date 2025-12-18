
# rank.py

from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import html, asyncio, random
from TEAMZYRO import app, user_collection, top_global_groups_collection

PHOTO_URL = ["https://files.catbox.moe/9j8e6b.jpg"]


@app.on_message(filters.command("rank"))
async def rank(_, message):
    cursor = user_collection.find(
        {}, {"id": 1, "first_name": 1, "characters": 1}
    )

    users = await cursor.to_list(None)
    users.sort(key=lambda x: len(x.get("characters", [])), reverse=True)
    users = users[:10]

    text = "<b>🏆 TOP 10 USERS BY CHARACTERS</b>\n\n"
    for i, u in enumerate(users, 1):
        text += (
            f"{i}. <a href='tg://user?id={u['id']}'>"
            f"<b>{html.escape(u.get('first_name','User'))}</b></a> "
            f"➜ {len(u.get('characters', []))}\n"
        )

    buttons = [
        [
            InlineKeyboardButton("🏆 Characters", callback_data="top"),
            InlineKeyboardButton("💰 Coins", callback_data="mtop")
        ],
        [
            InlineKeyboardButton("🪙 Tokens", callback_data="tokens")
        ]
    ]

    await message.reply_photo(
        photo=random.choice(PHOTO_URL),
        caption=text,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@app.on_callback_query(filters.regex("^mtop$"))
async def coin_top(_, cq):
    users = await user_collection.find(
        {"coins": {"$exists": True}}
    ).sort("coins", -1).limit(10).to_list(10)

    text = "<b>💰 TOP 10 USERS BY COINS</b>\n\n"
    for i, u in enumerate(users, 1):
        text += (
            f"{i}. <a href='tg://user?id={u['id']}'>"
            f"<b>{html.escape(u.get('first_name','User'))}</b></a> "
            f"➜ {u.get('coins',0)} coins\n"
        )

    await cq.edit_message_caption(
        caption=text,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=cq.message.reply_markup
    )


@app.on_callback_query(filters.regex("^tokens$"))
async def token_top(_, cq):
    users = await user_collection.find(
        {"tokens": {"$exists": True}}
    ).sort("tokens", -1).limit(10).to_list(10)

    text = "<b>🪙 TOP 10 USERS BY TOKENS</b>\n\n"
    for i, u in enumerate(users, 1):
        text += (
            f"{i}. <a href='tg://user?id={u['id']}'>"
            f"<b>{html.escape(u.get('first_name','User'))}</b></a> "
            f"➜ {u.get('tokens',0)} tokens\n"
        )

    await cq.edit_message_caption(
        caption=text,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=cq.message.reply_markup
    )
