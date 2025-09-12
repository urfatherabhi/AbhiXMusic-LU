import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from AbhiXMusic import app
from config import SUDOERS
from AbhiXMusic.utils.database import add_served_chat, get_assistant


# ---------------- /repo COMMAND ---------------- #

@app.on_message(filters.command("repo"))
async def show_repo(client: Client, message: Message):
    await message.reply_photo(
        photo="https://graph.org/file/1e0af186d0575a7d6a650.jpg",
        caption="||Bʜᴀᴀɢ Bʜɪᴋᴀʀɪ Rᴇᴘᴏ Tᴏ Nᴀʜɪ Dᴜɴɢᴀ||",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🥀 Pᴀᴘᴀ Jɪ 🥀", url="https://t.me/imagine_iq")
                ]
            ]
        )
    )


# ---------------- /clone COMMAND ---------------- #

@app.on_message(filters.command("clone"))
async def clone_command(client: Client, message: Message):
    user_id = message.from_user.id

    if user_id not in SUDOERS:
        await message.reply_photo(
            photo="https://graph.org/file/1e0af186d0575a7d6a650.jpg",
            caption=(
                "**🙂 You Are Not Sudo User So You Are Not Allowed To Clone Me.**\n"
                "**😌 Click The Button Below To Host Manually Or Contact Owner.**"
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("🥀 Pᴀᴘᴀ Jɪ 🥀", url="https://t.me/imagine_iq")
                    ]
                ]
            )
        )
        return

    await message.reply_photo(
        photo="https://graph.org/file/1e0af186d0575a7d6a650.jpg",
        caption=(
            "**✅ You Are A Verified Sudo User!**\n\n"
            "**💻 Clone This Bot From The Repository Below:**\n"
            "`git clone https://github.com/urfatherabhi/AbhiXMusic`\n\n"
            "**⚙️ You Can Host It On Heroku, VPS, Railway, or Any Platform.**\n"
            "**🛠️ For Any Help, Contact Papa Ji.**"
        ),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🔗 GitHub Repo", url="https://github.com/urfatherabhi/AbhiXMusic"),
                    InlineKeyboardButton("🥀 Pᴀᴘᴀ Jɪ", url="https://t.me/imagine_iq")
                ]
            ]
        )
    )


# ---------------- /hi-type Auto-Tracker ---------------- #

@app.on_message(
    filters.command(
        ["hi", "hii", "hello", "hui", "good", "gm", "ok", "bye", "welcome", "thanks"],
        prefixes=["/", "!", "%", ",", "", ".", "@", "#"],
    ) & filters.group
)
async def bot_check(_, message):
    chat_id = message.chat.id
    await add_served_chat(chat_id)


# ---------------- /gadd COMMAND ---------------- #

@app.on_message(filters.command("gadd") & filters.user(SUDOERS))
async def add_allbot(client: Client, message: Message):
    command_parts = message.text.split(" ")
    if len(command_parts) != 2:
        await message.reply(
            "**⚠️ ɪɴᴠᴀʟɪᴅ ᴄᴏᴍᴍᴀɴᴅ ғᴏʀᴍᴀᴛ. ᴘʟᴇᴀsᴇ ᴜsᴇ ʟɪᴋᴇ »** `/gadd @botusername`"
        )
        return

    bot_username = command_parts[1]
    try:
        userbot = await get_assistant(message.chat.id)
        bot = await app.get_users(bot_username)
        app_id = bot.id
        done = 0
        failed = 0

        lol = await message.reply(f"🔄 **ᴀᴅᴅɪɴɢ `{bot_username}` ɪɴ ᴀʟʟ ᴄʜᴀᴛs...**")
        await userbot.send_message(bot_username, "/start")

        async for dialog in userbot.get_dialogs():
            if dialog.chat.id == -1001754457302:
                continue  # skip private/blacklisted group
            try:
                await userbot.add_chat_members(dialog.chat.id, app_id)
                done += 1
            except Exception:
                failed += 1

            await lol.edit(
                f"**🔁 ᴘʀᴏɢʀᴇss ᴏғ ᴀᴅᴅɪɴɢ `{bot_username}`**\n\n"
                f"✅ ᴀᴅᴅᴇᴅ: {done} ᴄʜᴀᴛs\n"
                f"❌ ғᴀɪʟᴇᴅ: {failed} ᴄʜᴀᴛs\n\n"
                f"➲ ᴀᴅᴅᴇᴅ ʙʏ » @{userbot.username}"
            )
            await asyncio.sleep(2.5)  # Respect rate limits

        await lol.edit(
            f"**🎉 `{bot_username}` sᴜᴄᴄᴇssғᴜʟʟʏ ᴀᴅᴅᴇᴅ!**\n\n"
            f"✅ ɪɴ {done} ᴄʜᴀᴛs\n❌ ғᴀɪʟᴇᴅ ɪɴ {failed}\n\n"
            f"🧑‍💻 ʙʏ: @{userbot.username}"
        )
    except Exception as e:
        await message.reply(f"❌ **Error:** `{str(e)}`")


# ---------------- HELP ---------------- #

__MODULE__ = "Sᴏᴜʀᴄᴇ"
__HELP__ = """
**Rᴇᴘᴏ & Uᴛɪʟɪᴛʏ Cᴏᴍᴍᴀɴᴅs**

/repo — Source code link  
/clone — Clone instructions (sudo only)  
/gadd @botusername — Add given bot to all groups (sudo only)
"""
