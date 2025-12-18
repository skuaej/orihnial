from pyrogram import filters
from TEAMZYRO import app, user_collection


@app.on_message(filters.command("account"))
async def account_cmd(client, message):
    target_user = None

    # 1️⃣ Reply case
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user

    # 2️⃣ Username / UserID case
    elif len(message.command) > 1:
        try:
            target_user = await client.get_users(message.command[1])
        except:
            await message.reply_text("❌ User not found.")
            return

    # 3️⃣ Self case
    else:
        target_user = message.from_user

    # Fetch user from DB
    user = await user_collection.find_one({"id": target_user.id})

    coins = user.get("balance", 0) if user else 0

    text = (
        f"💰 **Account Info**\n\n"
        f"👤 User: {target_user.mention}\n"
        f"🆔 ID: `{target_user.id}`\n"
        f"💵 Coins: `{coins}`"
    )

    await message.reply_text(text)
