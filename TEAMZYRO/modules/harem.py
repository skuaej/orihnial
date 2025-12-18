# =========================
# IMPORTS
# =========================
import math
import random
import asyncio
import re
from html import escape
from itertools import groupby

from pyrogram import filters, enums
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto,
    InputMediaVideo
)

from TEAMZYRO import app, user_collection, collection
from TEAMZYRO.unit.zyro_rarity import rarity_map2


# =========================
# HELPERS
# =========================
async def fetch_user_characters(user_id: int):
    user = await user_collection.find_one({"id": user_id})
    if not user:
        return None, "You have no collection yet."

    chars = user.get("characters")
    if not isinstance(chars, list) or not chars:
        return None, "You have not collected any characters yet."

    chars = [c for c in chars if isinstance(c, dict) and "id" in c]
    if not chars:
        return None, "No valid characters found."

    return chars, None


# =========================
# /HAREM COMMAND
# =========================
@app.on_message(filters.command(["harem", "collection"]))
async def harem_handler(_, message: Message):
    user_id = message.from_user.id
    user = await user_collection.find_one({"id": user_id})
    filter_rarity = user.get("filter_rarity") if user else None

    msg = await show_harem(
        message=message,
        user_id=user_id,
        page=0,
        filter_rarity=filter_rarity,
        is_initial=True
    )

    if msg:
        await asyncio.sleep(180)
        await msg.delete()


# =========================
# HAREM DISPLAY
# =========================
async def show_harem(
    message: Message,
    user_id: int,
    page: int,
    filter_rarity=None,
    is_initial=False,
    callback=None
):
    try:
        characters, error = await fetch_user_characters(user_id)
        if error:
            return await message.reply_text(error)

        # filter rarity
        if filter_rarity:
            characters = [c for c in characters if c.get("rarity") == filter_rarity]
            if not characters:
                return await message.reply_text(
                    f"No characters with rarity {filter_rarity}"
                )

        characters.sort(key=lambda x: (x.get("anime", ""), x.get("id")))

        # count duplicates
        char_count = {}
        for c in characters:
            char_count[c["id"]] = char_count.get(c["id"], 0) + 1

        unique_chars = list({c["id"]: c for c in characters}.values())
        total_pages = max(1, math.ceil(len(unique_chars) / 15))
        page = max(0, min(page, total_pages - 1))

        page_chars = unique_chars[page * 15:(page + 1) * 15]

        text = f"<b>{escape(message.from_user.first_name)}'s Harem ({page+1}/{total_pages})</b>\n"
        if filter_rarity:
            text += f"<b>Filter:</b> {filter_rarity}\n"

        grouped = {}
        for c in page_chars:
            grouped.setdefault(c.get("anime", "Unknown"), []).append(c)

        for anime, chars in grouped.items():
            total = await collection.count_documents({"anime": anime})
            text += f"\n<b>{anime} {len(chars)}/{total}</b>\n"
            for c in chars:
                emoji = rarity_map2.get(c.get("rarity"), "")
                text += f"◈⌠{emoji}⌡ {c['id']} {c['name']} ×{char_count[c['id']]}\n"

        # buttons
        keyboard = [
            [
                InlineKeyboardButton(
                    "📦 Collection",
                    switch_inline_query_current_chat=f"collection.{user_id} "
                ),
                InlineKeyboardButton(
                    "❤️ AMV",
                    switch_inline_query_current_chat=f"collection.{user_id}.AMV "
                )
            ]
        ]

        nav = []
        if page > 0:
            nav.append(
                InlineKeyboardButton("⬅️", callback_data=f"harem:{page-1}:{user_id}:{filter_rarity}")
            )
        if page < total_pages - 1:
            nav.append(
                InlineKeyboardButton("➡️", callback_data=f"harem:{page+1}:{user_id}:{filter_rarity}")
            )
        if nav:
            keyboard.append(nav)

        markup = InlineKeyboardMarkup(keyboard)

        media_char = random.choice(characters)

        if is_initial:
            if media_char.get("vid_url"):
                return await message.reply_video(
                    media_char["vid_url"],
                    caption=text,
                    reply_markup=markup,
                    parse_mode=enums.ParseMode.HTML
                )
            return await message.reply_photo(
                media_char.get("img_url"),
                caption=text,
                reply_markup=markup,
                parse_mode=enums.ParseMode.HTML
            )
        else:
            media = (
                InputMediaVideo(media_char["vid_url"], caption=text)
                if media_char.get("vid_url")
                else InputMediaPhoto(media_char["img_url"], caption=text)
            )
            await callback.message.edit_media(media, reply_markup=markup)
    except Exception as e:
        print("HAREM ERROR:", e)
        return await message.reply_text("Something went wrong.")


# =========================
# CALLBACK PAGINATION
# =========================
@app.on_callback_query(filters.regex("^harem"))
async def harem_cb(_, cq):
    _, page, uid, rarity = cq.data.split(":")
    uid = int(uid)
    if cq.from_user.id != uid:
        return await cq.answer("Not your harem!", show_alert=True)

    await show_harem(
        message=cq.message,
        user_id=uid,
        page=int(page),
        filter_rarity=None if rarity == "None" else rarity,
        callback=cq
    )


# =========================
# /HMODE
# =========================
@app.on_message(filters.command("hmode"))
async def hmode(_, message: Message):
    uid = message.from_user.id
    kb, row = [], []

    for i, (rar, emo) in enumerate(rarity_map2.items(), 1):
        row.append(InlineKeyboardButton(emo, callback_data=f"setrar:{uid}:{rar}"))
        if i % 4 == 0:
            kb.append(row)
            row = []

    if row:
        kb.append(row)

    kb.append([InlineKeyboardButton("All", callback_data=f"setrar:{uid}:None")])
    await message.reply_text("Choose rarity:", reply_markup=InlineKeyboardMarkup(kb))


@app.on_callback_query(filters.regex("^setrar"))
async def setrar(_, cq):
    _, uid, rar = cq.data.split(":")
    uid = int(uid)

    if cq.from_user.id != uid:
        return await cq.answer("Not yours!", show_alert=True)

    await user_collection.update_one(
        {"id": uid},
        {"$set": {"filter_rarity": None if rar == "None" else rar}},
        upsert=True
    )
    await cq.message.edit_text("Rarity filter updated.")
    await cq.answer()
