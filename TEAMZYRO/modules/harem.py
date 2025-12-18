from TEAMZYRO import *
from pyrogram import filters, enums
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto,
)
from itertools import groupby
import math
import random
import asyncio
from html import escape


# ───────────────────────────────
# HELPER
# ───────────────────────────────
async def fetch_user_characters(user_id: int):
    user = await user_collection.find_one({"id": user_id})
    if not user or not user.get("characters"):
        return None, "You have not guessed any characters yet."

    chars = [c for c in user["characters"] if isinstance(c, dict) and "id" in c]
    if not chars:
        return None, "No valid characters found."

    return chars, None


# ───────────────────────────────
# /harem & /collection
# ───────────────────────────────
@app.on_message(filters.command(["harem", "collection"]))
async def harem_handler(client, message):
    user_id = message.from_user.id
    page = 0

    user = await user_collection.find_one({"id": user_id})
    filter_rarity = user.get("filter_rarity") if user else None

    sent = await display_harem(
        client=client,
        message=message,
        user_id=user_id,
        page=page,
        filter_rarity=filter_rarity,
        is_initial=True
    )

    if sent:
        await asyncio.sleep(180)
        await sent.delete()


# ───────────────────────────────
# MAIN DISPLAY
# ───────────────────────────────
async def display_harem(client, message, user_id, page, filter_rarity, is_initial, callback_query=None):
    try:
        characters, error = await fetch_user_characters(user_id)
        if error:
            return await message.reply_text(error)

        # 🔴 IMPORTANT FIX
        characters = sorted(characters, key=lambda x: x.get("id"))

        # FILTER
        if filter_rarity:
            characters = [c for c in characters if c.get("rarity") == filter_rarity]
            if not characters:
                kb = InlineKeyboardMarkup(
                    [[InlineKeyboardButton("❌ Remove Filter", callback_data=f"remove_filter:{user_id}")]]
                )
                return await message.reply_text(
                    f"No characters found for rarity **{filter_rarity}**",
                    reply_markup=kb
                )

        # GROUP COUNTS
        char_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x["id"])}
        unique_chars = list({c["id"]: c for c in characters}.values())

        total_pages = max(1, math.ceil(len(unique_chars) / 15))
        page = max(0, min(page, total_pages - 1))

        text = f"<b>{escape(message.from_user.first_name)}'s Harem</b> "
        text += f"<b>({page+1}/{total_pages})</b>\n"
        if filter_rarity:
            text += f"<b>Filtered:</b> {filter_rarity}\n"

        page_chars = unique_chars[page*15:(page+1)*15]

        for anime, chars in groupby(page_chars, key=lambda x: x.get("anime", "Unknown")):
            chars = list(chars)
            total = await collection.count_documents({"anime": anime})
            text += f"\n<b>{anime} {len(chars)}/{total}</b>\n"
            for c in chars:
                count = char_counts.get(c["id"], 1)
                emoji = rarity_map2.get(c.get("rarity"), "")
                text += f"◈⌠{emoji}⌡ {c['id']} {c['name']} ×{count}\n"

        # BUTTONS
        keyboard = [
            [
                InlineKeyboardButton("📦 Collection", switch_inline_query_current_chat=f"collection.{user_id}"),
                InlineKeyboardButton("💌 AMV", switch_inline_query_current_chat=f"collection.{user_id}.AMV"),
            ]
        ]

        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton("⬅️", callback_data=f"harem:{page-1}:{user_id}"))
        if page < total_pages - 1:
            nav.append(InlineKeyboardButton("➡️", callback_data=f"harem:{page+1}:{user_id}"))
        if nav:
            keyboard.append(nav)

        reply_markup = InlineKeyboardMarkup(keyboard)

        image_char = random.choice(characters)
        media = None

        if image_char.get("img_url"):
            media = image_char["img_url"]

        if is_initial:
            if media:
                return await message.reply_photo(
                    photo=media,
                    caption=text,
                    reply_markup=reply_markup,
                    parse_mode=enums.ParseMode.HTML
                )
            return await message.reply_text(text, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)
        else:
            return await callback_query.message.edit_text(
                text,
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            )

    except Exception as e:
        print("HAREM ERROR:", e)
        return await message.reply_text("An error occurred.")


# ───────────────────────────────
# PAGE CALLBACK
# ───────────────────────────────
@app.on_callback_query(filters.regex("^harem:"))
async def harem_callback(client, cq):
    _, page, user_id = cq.data.split(":")
    page = int(page)
    user_id = int(user_id)

    if cq.from_user.id != user_id:
        return await cq.answer("Not your harem!", show_alert=True)

    user = await user_collection.find_one({"id": user_id})
    filter_rarity = user.get("filter_rarity") if user else None

    await display_harem(
        client,
        cq.message,
        user_id,
        page,
        filter_rarity,
        is_initial=False,
        callback_query=cq
    )


# ───────────────────────────────
# /hmode
# ───────────────────────────────
@app.on_message(filters.command("hmode"))
async def hmode(client, message):
    user_id = message.from_user.id
    keyboard = []
    row = []

    for i, (rarity, emoji) in enumerate(rarity_map2.items(), 1):
        row.append(InlineKeyboardButton(emoji, callback_data=f"set_rarity:{user_id}:{rarity}"))
        if i % 4 == 0:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("All", callback_data=f"set_rarity:{user_id}:None")])

    await message.reply_text(
        "Select rarity filter:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ───────────────────────────────
# SET RARITY
# ───────────────────────────────
@app.on_callback_query(filters.regex("^set_rarity:"))
async def set_rarity(client, cq):
    _, user_id, rarity = cq.data.split(":")
    user_id = int(user_id)
    rarity = None if rarity == "None" else rarity

    if cq.from_user.id != user_id:
        return await cq.answer("Not yours!", show_alert=True)

    await user_collection.update_one(
        {"id": user_id},
        {"$set": {"filter_rarity": rarity}},
        upsert=True
    )

    await cq.answer("Filter updated ✅", show_alert=True)
    await cq.message.delete()


# ───────────────────────────────
# REMOVE FILTER
# ───────────────────────────────
@app.on_callback_query(filters.regex("^remove_filter:"))
async def remove_filter(client, cq):
    _, user_id = cq.data.split(":")
    user_id = int(user_id)

    if cq.from_user.id != user_id:
        return await cq.answer("Not yours!", show_alert=True)

    await user_collection.update_one(
        {"id": user_id},
        {"$set": {"filter_rarity": None}}
    )

    await cq.answer("Filter removed ✅", show_alert=True)
    await cq.message.delete()
