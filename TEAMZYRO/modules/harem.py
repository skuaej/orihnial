from TEAMZYRO import *
from pyrogram import filters, enums
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto
)
from itertools import groupby
import math
from html import escape
import random

# ─────────────────────────────────────────────
# Fetch user characters
# ─────────────────────────────────────────────
async def fetch_user_characters(user_id):
    user = await user_collection.find_one({"id": user_id})
    if not user or "characters" not in user:
        return None, "You have not guessed any characters yet."

    characters = [c for c in user["characters"] if "id" in c]
    if not characters:
        return None, "No valid characters found in your collection."

    return characters, None


# ─────────────────────────────────────────────
# HAREM / COLLECTION COMMAND
# ─────────────────────────────────────────────
@app.on_message(filters.command(["harem", "collection"]))
async def harem_handler(client, message):
    user_id = message.from_user.id
    page = 0

    user = await user_collection.find_one({"id": user_id})
    filter_rarity = user.get("filter_rarity") if user else None

    await display_harem(
        client,
        message,
        user_id,
        page,
        filter_rarity,
        is_initial=True
    )


# ─────────────────────────────────────────────
# DISPLAY HAREM
# ─────────────────────────────────────────────
async def display_harem(client, message, user_id, page, filter_rarity, is_initial=False, callback_query=None):
    try:
        characters, error = await fetch_user_characters(user_id)
        if error:
            return await message.reply_text(error)

        # Sort
        characters.sort(key=lambda x: (x.get("anime", ""), x.get("id", "")))

        # Filter by rarity
        if filter_rarity:
            characters = [c for c in characters if c.get("rarity") == filter_rarity]
            if not characters:
                return await message.reply_text(
                    f"No characters found with rarity: **{filter_rarity}**",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("Remove Filter", callback_data=f"remove_filter:{user_id}")]]
                    )
                )

        # Count duplicates
        character_counts = {}
        for c in characters:
            character_counts[c["id"]] = character_counts.get(c["id"], 0) + 1

        unique_characters = list({c["id"]: c for c in characters}.values())

        total_pages = max(1, math.ceil(len(unique_characters) / 15))
        page = max(0, min(page, total_pages - 1))

        # Message text
        harem_message = (
            f"<b>{escape(message.from_user.first_name)}'s Harem "
            f"- Page {page + 1}/{total_pages}</b>\n"
        )

        if filter_rarity:
            harem_message += f"<b>Filtered by: {filter_rarity}</b>\n"

        current_chars = unique_characters[page * 15:(page + 1) * 15]

        grouped = {}
        for c in current_chars:
            grouped.setdefault(c["anime"], []).append(c)

        for anime, chars in grouped.items():
            harem_message += f"\n<b>{anime}</b>\n"
            for char in chars:
                count = character_counts.get(char["id"], 1)
                emoji = rarity_map2.get(char.get("rarity"), "")
                harem_message += f"◈⌠{emoji}⌡ {char['id']} {char['name']} ×{count}\n"

        # Buttons
        keyboard = [
            [
                InlineKeyboardButton("Collection", switch_inline_query_current_chat=f"collection.{user_id}"),
                InlineKeyboardButton("💌 AMV", switch_inline_query_current_chat=f"collection.{user_id}.AMV")
            ]
        ]

        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton("⬅️", callback_data=f"harem:{page-1}:{user_id}:{filter_rarity or 'None'}"))
        if page < total_pages - 1:
            nav.append(InlineKeyboardButton("➡️", callback_data=f"harem:{page+1}:{user_id}:{filter_rarity or 'None'}"))
        if nav:
            keyboard.append(nav)

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Pick media
        image_character = random.choice(characters)

        # Initial send
        if is_initial:
            if "vid_url" in image_character:
                return await message.reply_video(
                    image_character["vid_url"],
                    caption=harem_message,
                    reply_markup=reply_markup,
                    parse_mode=enums.ParseMode.HTML
                )
            elif "img_url" in image_character:
                return await message.reply_photo(
                    image_character["img_url"],
                    caption=harem_message,
                    reply_markup=reply_markup,
                    parse_mode=enums.ParseMode.HTML
                )
            return await message.reply_text(
                harem_message,
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            )

        # Callback edit
        if "img_url" in image_character:
            await callback_query.message.edit_media(
                InputMediaPhoto(image_character["img_url"], caption=harem_message),
                reply_markup=reply_markup
            )
        else:
            await callback_query.message.edit_text(
                harem_message,
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            )

    except Exception as e:
        print("HAREM ERROR:", e)
        return await message.reply_text("❌ An error occurred.")


# ─────────────────────────────────────────────
# CALLBACKS
# ─────────────────────────────────────────────
@app.on_callback_query(filters.regex("^remove_filter"))
async def remove_filter_callback(_, cq):
    _, user_id = cq.data.split(":")
    user_id = int(user_id)

    if cq.from_user.id != user_id:
        return await cq.answer("Not your harem!", show_alert=True)

    await user_collection.update_one(
        {"id": user_id},
        {"$set": {"filter_rarity": None}},
        upsert=True
    )

    await cq.message.delete()
    await cq.answer("Filter removed", show_alert=True)


@app.on_callback_query(filters.regex("^harem"))
async def harem_callback(_, cq):
    _, page, user_id, rarity = cq.data.split(":")
    page = int(page)
    user_id = int(user_id)
    rarity = None if rarity == "None" else rarity

    if cq.from_user.id != user_id:
        return await cq.answer("Not your harem!", show_alert=True)

    await display_harem(_, cq.message, user_id, page, rarity, False, cq)
