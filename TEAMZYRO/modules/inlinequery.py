import re
import time
from html import escape
from cachetools import TTLCache
from telegram import Update, InlineQueryResultPhoto, InlineQueryResultVideo
from telegram.ext import InlineQueryHandler, CallbackContext

from TEAMZYRO import application, collection, user_collection
from TEAMZYRO.unit.zyro_inline import (
    search_characters,
    get_all_characters,
    get_user_collection,
    refresh_character_caches
)

# ─────────────────────────────────────────
# CACHES
# ─────────────────────────────────────────
all_characters_cache = TTLCache(maxsize=10000, ttl=300)
user_collection_cache = TTLCache(maxsize=10000, ttl=30)

# ─────────────────────────────────────────
# NORMALIZE USER CHARACTERS
# (int / str → full character dict)
# ─────────────────────────────────────────
async def normalize_user_characters(raw_chars):
    fixed = []

    for c in raw_chars:
        # already full character dict
        if isinstance(c, dict):
            fixed.append(c)

        # only ID stored (int / str)
        elif isinstance(c, (int, str)):
            char = await collection.find_one({"id": str(c)})
            if char:
                fixed.append(char)

    return fixed

# ─────────────────────────────────────────
# INLINE QUERY HANDLER
# ─────────────────────────────────────────
async def inlinequery(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query.strip()
    offset = int(update.inline_query.offset) if update.inline_query.offset else 0

    force_refresh = "!refresh" in query
    if force_refresh:
        query = query.replace("!refresh", "").strip()
        await refresh_character_caches()

    try:
        # ─────────────────────────────
        # USER COLLECTION QUERY
        # ─────────────────────────────
        if query.startswith("collection."):
            parts = query.split(" ")
            user_id = parts[0].split(".")[1]
            search_terms = " ".join(parts[1:]) if len(parts) > 1 else ""

            if user_id.isdigit():
                user = await get_user_collection(user_id)
                if not user:
                    all_characters = []
                else:
                    raw_chars = user.get("characters", [])
                    all_characters = await normalize_user_characters(raw_chars)

                    if search_terms:
                        regex = re.compile(search_terms, re.IGNORECASE)
                        all_characters = [
                            c for c in all_characters
                            if regex.search(c.get("name", "")) or
                               regex.search(c.get("anime", ""))
                        ]
            else:
                all_characters = []

        # ─────────────────────────────
        # GLOBAL SEARCH
        # ─────────────────────────────
        else:
            if query:
                all_characters = await search_characters(query, force_refresh)
            else:
                all_characters = await get_all_characters(force_refresh)

        # ─────────────────────────────
        # MEDIA FILTER
        # ─────────────────────────────
        if ".AMV" in query:
            all_characters = [c for c in all_characters if isinstance(c, dict) and c.get("vid_url")]
        else:
            all_characters = [c for c in all_characters if isinstance(c, dict) and c.get("img_url")]

        # ─────────────────────────────
        # PAGINATION
        # ─────────────────────────────
        characters = all_characters[offset: offset + 50]
        next_offset = str(offset + len(characters)) if len(characters) == 50 else None

        # ─────────────────────────────
        # BUILD INLINE RESULTS
        # ─────────────────────────────
        results = []

        for character in characters:
            if not isinstance(character, dict):
                continue

            if not all(k in character for k in ("id", "name", "anime", "rarity")):
                continue

            caption = (
                f"<b>🌸 {escape(character['name'])}</b>\n"
                f"<b>🏖️ From:</b> {escape(character['anime'])}\n"
                f"<b>🔮 Rarity:</b> {escape(character['rarity'])}\n"
                f"<b>🆔</b> <code>{escape(str(character['id']))}</code>"
            )

            # VIDEO
            if character.get("vid_url"):
                results.append(
                    InlineQueryResultVideo(
                        id=f"{character['id']}_{time.time()}",
                        video_url=character["vid_url"],
                        mime_type="video/mp4",
                        thumbnail_url=character.get(
                            "thum_url",
                            character.get("img_url", "")
                        ),
                        title=character["name"],
                        description=f"{character['anime']} | {character['rarity']}",
                        caption=caption,
                        parse_mode="HTML"
                    )
                )

            # IMAGE
            elif character.get("img_url"):
                results.append(
                    InlineQueryResultPhoto(
                        id=f"{character['id']}_{time.time()}",
                        photo_url=character["img_url"],
                        thumbnail_url=character["img_url"],
                        caption=caption,
                        parse_mode="HTML"
                    )
                )

        await update.inline_query.answer(
            results,
            next_offset=next_offset,
            cache_time=1
        )

    except Exception as e:
        print(f"[INLINE ERROR] {e}")
        await update.inline_query.answer([], cache_time=1)

# ─────────────────────────────────────────
# REGISTER HANDLER
# ─────────────────────────────────────────
application.add_handler(
    InlineQueryHandler(inlinequery, block=False)
)
