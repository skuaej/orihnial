# ===============================
# HAREM / COLLECTION MODULE
# ===============================

from TEAMZYRO import app, user_collection, collection, rarity_map2
from pyrogram import filters, enums
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto,
    CallbackQuery,
    Message
)
from itertools import groupby
from html import escape
import math
import random
import asyncio


# ──────────────────────────────
# SAFE FETCH USER CHARACTERS
# ──────────────────────────────
async def fetch_user_characters(user_id: int):
    user = await user_collection.find_one({"id": user_id})

    if not user:
        return [], "You have not guessed any characters yet."

    chars = user.get("characters")

    # 🔥 MAIN FIX — characters must be list
    if not isinstance(chars, list):
        await user_collection.update_one(
            {"id": user_id},
            {"$set": {"characters": []}}
        )
        return [], "Your collection was corrupted and has been reset."

    characters = [c for c in chars if isinstance(c, dict) and "id" in c]

    if not characters:
        return [], "No valid characters found in your collection."

    return characters, None


# ──────────────────────────────
# /harem & /collection
# ──────────────────────────────
@app.on_message(filters.command(["harem", "collection"]))
async def harem_handler(_, message: Message):
    user_id = message.from_user.id
    user = await user_collection.find_one({"id": user_id})
    filter_rarity = user.get("filter_rarity") if user else None

    msg = await display_harem(
        message,
        user_id=user_id,
        page=0,
        filter_rarity=filter_rarity,
        is_initial=True
    )

    if msg:
        await asyncio.sleep(180)
        await msg.delete()


# ──────────────────────────────
# DISPLAY HAREM
# ──────────────────────────────
async def display_harem(
    message: Message,
    user_id: int,
    page: int,
    filter_rarity=None,
    is_initial=False,
    callback_query: CallbackQuery = None
):
    try:
        characters, error = await fetch_user_characters(user_id)
        if error:
            return await message.reply_text(error)

        # 🔥 SORT BEFORE GROUPBY
        characters = sorted(characters, key=lambda x: (x.get("anime", ""), x["id"]))

        # FILTER BY RARITY
        if filter_rarity:
            characters = [c for c in characters if c.get("rarity") == filter_rarity]
            if not characters:
                return await message.reply_text(
                    f"No characters found with rarity: {filter_rarity}"
                )

        # COUNT DUPLICATES
        characters_sorted = sorted(characters, key=lambda x: x["id"])
        character_counts = {
            k: len(list(v))
            for k, v in groupby(characters_sorted, key=lambda x: x["id"])
        }

        unique_characters = list(
            {c["id"]: c for c in characters_sorted}.values()
        )

        total_pages = max(1, math.ceil(len(unique_characters) / 15))
        page = max(0, min(page, total_pages - 1))

        # HEADER
        harem_text = (
            f"<b>{escape(message.from_user.first_name)}'s Harem</b>\n"
            f"Page {page+1}/{total_pages}\n"
        )

        if filter_rarity:
            harem_text += f"<b>Filter:</b> {filter_rarity}\n"

        # PAGE DATA
        page_chars = unique_characters[page*15:(page+1)*15]

        page_chars = sorted(page_chars, key=lambda x: x.get("anime", ""))

        for anime, group in groupby(page_chars, key=lambda x: x.get("anime", "Unknown")):
            anime_count = await collection.count_documents(
                {"anime": anime} if isinstance(anime, str) else {}
            )
            group = list(group)
            harem_text += f"\n<b>{anime} {len(group)}/{anime_count}</b>\n"

            for c in group:
                emoji = rarity_map2.get(c.get("rarity"), "")
                count = character_counts.get(c["id"], 1)
                harem_text += f"◈⌠{emoji}⌡ {c['id']} {c['name']} ×{count}\n"

        # KEYBOARD
        keyboard = [
            [
                InlineKeyboardButton(
                    "Collection",
                    switch_inline_query_current_chat=f"collection.{user_id}"
                ),
                InlineKeyboardButton(
                    "💌 AMV",
                    switch_inline_query_current_chat=f"collection.{user_id}.AMV"
                )
            ]
        ]

        nav = []
        if page > 0:
            nav.append(
                InlineKeyboardButton("⬅️", callback_data=f"harem:{page-1}:{user_id}:{filter_rarity or 'None'}")
            )
        if page < total_pages - 1:
            nav.append(
                InlineKeyboardButton("➡️", callback_data=f"harem:{page+1}:{user_id}:{filter_rarity or 'None'}")
            )
        if nav:
            keyboard.append(nav)

        markup = InlineKeyboardMarkup(keyboard)

        # IMAGE PICK
        image_character = random.choice(characters)

        if is_initial:
            if image_character.get("img_url"):
                return await message.reply_photo(
                    image_character["img_url"],
                    caption=harem_text,
                    reply_markup=markup,
                    parse_mode=enums.ParseMode.HTML
                )
            else:
                return await message.reply_text(
                    harem_text,
                    reply_markup=markup,
                    parse_mode=enums.ParseMode.HTML
                )
        else:
            await callback_query.message.edit_text(
                harem_text,
                reply_markup=markup,
                parse_mode=enums.ParseMode.HTML
            )

    except Exception as e:
        print("HAREM ERROR:", e)
        await message.reply_text("❌ An error occurred. Please try again later.")


# ──────────────────────────────
# CALLBACK NAVIGATION
# ──────────────────────────────
@app.on_callback_query(filters.regex("^harem:"))
async def harem_callback(_, cq: CallbackQuery):
    try:
        _, page, user_id, rarity = cq.data.split(":")
        page = int(page)
        user_id = int(user_id)
        rarity = None if rarity == "None" else rarity

        if cq.from_user.id != user_id:
            return await cq.answer("Not your harem!", show_alert=True)

        await display_harem(
            cq.message,
            user_id=user_id,
            page=page,
            filter_rarity=rarity,
            is_initial=False,
            callback_query=cq
        )
        await cq.answer()

    except Exception as e:
        print("CALLBACK ERROR:", e)
        await cq.answer("Error", show_alert=True)
