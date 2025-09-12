import time
import asyncio
from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from youtubesearchpython.__future__ import VideosSearch

import config
from AbhiXMusic import app
from AbhiXMusic.misc import _boot_
from AbhiXMusic.plugins.sudo.sudoers import sudoers_list
from AbhiXMusic.utils.database import (
    add_served_chat,
    add_served_user,
    blacklisted_chats,
    get_lang,
    is_banned_user,
    is_on_off,
)
from AbhiXMusic.utils.decorators.language import LanguageStart
from AbhiXMusic.utils.formatters import get_readable_time
from AbhiXMusic.utils.inline import help_pannel, private_panel, start_panel
from config import BANNED_USERS
from strings import get_string

@app.on_message(filters.command(["start"]) & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_pm(client, message: Message, _):
    await add_served_user(message.from_user.id)
    await message.react("❤️")

    if len(message.text.split()) > 1:
        name = message.text.split(None, 1)[1]
        if name[0:4] == "help":
            keyboard = help_pannel(_)
            await message.reply_sticker("CAACAgUAAxkBAAEQI1RlTLnRAy4h9lOS6jgS5FYsQoruOAAC1gMAAg6ryVcldUr_lhPexzME")
            return await message.reply_photo(
                photo=config.START_IMG_URL,
                caption=_["help_1"].format(config.SUPPORT_CHAT),
                reply_markup=keyboard,
            )
        if name[0:3] == "sud":
            await sudoers_list(client=client, message=message, _=_)
            if await is_on_off(2):
                return await app.send_message(
                    chat_id=config.LOGGER_ID,
                    text=f"{message.from_user.mention} Jᴜsᴛ Sᴛᴀʀᴛᴇᴅ Tʜᴇ Bᴏᴛ Tᴏ Cʜᴇᴄᴋ <b>sᴜᴅᴏʟɪsᴛ</b>.\n\n<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>\n<b>ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.from_user.username}",
                )
            return
        if name[0:3] == "inf":
            m = await message.reply_text("🔎")
            query = (str(name)).replace("info_", "", 1)
            query = f"https://www.youtube.com/watch?v={query}"
            results = VideosSearch(query, limit=1)
            for result in (await results.next())["result"]:
                title = result["title"]
                duration = result["duration"]
                views = result["viewCount"]["short"]
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
                channellink = result["channel"]["link"]
                channel = result["channel"]["name"]
                link = result["link"]
                published = result["publishedTime"]
            searched_text = _["start_6"].format(
                title, duration, views, published, channellink, channel, app.mention
            )
            key = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text=_["S_B_8"], url=link),
                        InlineKeyboardButton(text=_["S_B_9"], url=config.SUPPORT_CHAT),
                    ],
                ]
            )
            await m.delete()
            await app.send_photo(
                chat_id=message.chat.id,
                photo=thumbnail,
                caption=searched_text,
                reply_markup=key,
            )
            if await is_on_off(2):
                return await app.send_message(
                    chat_id=config.LOGGER_ID,
                    text=f"{message.from_user.mention} Jᴜsᴛ Sᴛᴀʀᴛᴇᴅ Tʜᴇ Bᴏᴛ Tᴏ Cʜᴇᴄᴋ <b>Tʀᴀᴄᴋ Iɴғᴏʀᴍᴀᴛɪᴏɴ</b>.\n\n<b>Usᴇʀ Iᴅ :</b> <code>{message.from_user.id}</code>\n<b>Usᴇʀɴᴀᴍᴇ :</b> @{message.from_user.username}",
                )
    else:
        try:
            out = private_panel(_)
            # Initial welcome animation (ab sirf 2 baar change hoga aur turant delete)
            lol = await message.reply_text(f"💕 Wᴇʟᴄᴏᴍᴇ Bᴀʙʏ {message.from_user.mention} 💕 ❣️")
            await asyncio.sleep(0.1) # Thoda sa delay pehle change ke liye
            await lol.edit_text(f"🌸 Wᴇʟᴄᴏᴍᴇ Bᴀʙʏ {message.from_user.mention} 🌸 🥳")
            await asyncio.sleep(0.1) # Thoda sa delay dusre change ke liye
            await lol.edit_text(f"💖 Wᴇʟᴄᴏᴍᴇ Bᴀʙʏ {message.from_user.mention}💖 💥")
            await lol.delete() # Turant delete

            # Static welcome message
            welcome = await message.reply_text(f"🌟 Wᴇʟᴄᴏᴍᴇ {message.from_user.mention} to {app.mention}! 🌟 Gᴇᴛ Rᴇᴀᴅʏ Fᴏʀ Aᴡᴇꜱᴏᴍᴇ Mᴜꜱɪᴄ! 🎶")
            await asyncio.sleep(1)
            await welcome.delete()

            # Father is coming animation (standard characters)
            father = await message.reply_text("⚡")
            await asyncio.sleep(0.07)
            await father.edit_text("⚡ W")
            await asyncio.sleep(0.07)
            await father.edit_text("✨ Wᴀ")
            await asyncio.sleep(0.07)
            await father.edit_text("🔥 Wᴀɪ")
            await asyncio.sleep(0.07)
            await father.edit_text("⚡ Wᴀɪᴛ")
            await asyncio.sleep(0.07)
            await father.edit_text("✨ Wᴀɪᴛ...")
            await asyncio.sleep(0.07)
            await father.edit_text("🔥 Wᴀɪᴛ... F")
            await asyncio.sleep(0.07)
            await father.edit_text("⚡ Wᴀɪᴛ... Fᴀ")
            await asyncio.sleep(0.07)
            await father.edit_text("✨ Wᴀɪᴛ... Fᴀᴛ")
            await asyncio.sleep(0.07)
            await father.edit_text("🔥 Wᴀɪᴛ... Fᴀᴛʜ")
            await asyncio.sleep(0.07)
            await father.edit_text("⚡ Wᴀɪᴛ... Fᴀᴛʜᴇ")
            await asyncio.sleep(0.07)
            await father.edit_text("✨ Wᴀɪᴛ... Fᴀᴛʜᴇʀ")
            await asyncio.sleep(0.07)
            await father.edit_text("🔥 Wᴀɪᴛ... Fᴀᴛʜᴇʀ I")
            await asyncio.sleep(0.07)
            await father.edit_text("⚡ Wᴀɪᴛ... Fᴀᴛʜᴇʀ Iꜱ")
            await asyncio.sleep(0.07)
            await father.edit_text("✨ Wᴀɪᴛ... Fᴀᴛʜᴇʀ Iꜱ C")
            await asyncio.sleep(0.07)
            await father.edit_text("🔥 Wᴀɪᴛ... Fᴀᴛʜᴇʀ Iꜱ Cᴏ")
            await asyncio.sleep(0.07)
            await father.edit_text("⚡ Wᴀɪᴛ... Fᴀᴛʜᴇʀ Iꜱ Cᴏᴍ")
            await asyncio.sleep(0.07)
            await father.edit_text("✨ Wᴀɪᴛ... Fᴀᴛʜᴇʀ Iꜱ Cᴏᴍᴍɪ")
            await asyncio.sleep(0.07)
            await father.edit_text("🔥 Wᴀɪᴛ... Fᴀᴛʜᴇʀ Iꜱ Cᴏᴍᴍɪɴ")
            await asyncio.sleep(0.07)
            await father.edit_text("⚡ Wᴀɪᴛ... Fᴀᴛʜᴇʀ Iꜱ Cᴏᴍᴍɪɴɢ")
            await asyncio.sleep(0.07)
            await father.edit_text("✨ Wᴀɪᴛ... Fᴀᴛʜᴇʀ Iꜱ Cᴏᴍᴍɪɴɢ 🔥")
            await asyncio.sleep(0.07)
            await father.edit_text("🔥 Wᴀɪᴛ... Fᴀᴛʜᴇʀ Iꜱ Cᴏᴍᴍɪɴɢ ⚡")
            await asyncio.sleep(0.07)
            await father.edit_text("⚡ Wᴀɪᴛ... Fᴀᴛʜᴇʀ Iꜱ Cᴏᴍᴍɪɴɢ ✨")
            await asyncio.sleep(0.07)

            # Father arrived animation
            await father.edit_text("✨ Fᴀᴛʜᴇʀ Aʀʀɪᴠᴇᴅ ✨")
            await asyncio.sleep(0.5)
            await father.edit_text("🔥 Fᴀᴛʜᴇʀ Aʀʀɪᴠᴇᴅ 🔥")
            await asyncio.sleep(0.5)
            await father.edit_text("⚡ Fᴀᴛʜᴇʀ Aʀʀɪᴠᴇᴅ ⚡")
            await asyncio.sleep(0.5)
            await father.edit_text("✨ Fᴀᴛʜᴇʀ Aʀʀɪᴠᴇᴅ ✨")
            await asyncio.sleep(0.5)
            await father.delete()

            # Sticker with proper deletion
            sticker = await message.reply_sticker("CAACAgUAAxkBAAEQI1RlTLnRAy4h9lOS6jgS5FYsQoruOAAC1gMAAg6ryVcldUr_lhPexzME")
            await asyncio.sleep(0.5)
            await sticker.delete()

            # Restored caption with photo
            await message.reply_photo(
                photo=config.START_IMG_URL,
                caption=(
                    f"<b>Hєу</b> {message.from_user.mention}, 🥀\n\n"
                    f"<b>➻ Tʜɪꜱ Iꜱ</b> <a href='https://t.me/{app.username}?start'>{app.mention}</a> !\n\n"
                    f"➻ A Fᴀsᴛ & Pᴏᴡᴇʀғᴜʟ Tᴇʟᴇɢʀᴀᴍ Mᴜsɪᴄ Pʟᴀʏᴇʀ Bᴏᴛ Wɪᴛʜ Sᴏᴍᴇ Aᴡᴇsᴏᴍᴇ Fᴇᴀᴛᴜʀᴇs.\n\n"
                    f"<b>Sᴜᴘᴘᴏʀᴛᴇᴅ Pʟᴀᴛғᴏʀᴍs</b> : Yᴏᴜᴛᴜʙᴇ, Sᴘᴏᴛɪғʏ, Rᴇssᴏ, Aᴘᴘʟᴇ Mᴜsɪᴄ Aɴᴅ Sᴏᴜɴᴅᴄʟᴏᴜᴅ.\n"
                    f"──────────────────\n"
                    f"➻ Bᴀʙʏ... <b>Fᴀᴛʜᴇʀ</b> Hᴀꜱ Aʟʀᴇᴀᴅʏ Aʀʀɪᴠᴇᴅ ✨\n"
                    f"<b>๏ Cʟɪᴄᴋ Oɴ Tʜᴇ Hᴇʟᴩ Bᴜᴛᴛᴏɴ Tᴏ Gᴇᴛ Iɴғᴏʀᴍᴀᴛɪᴏɴ Aʙᴏᴜᴛ Mʏ Mᴏᴅᴜʟᴇs Aɴᴅ Cᴏᴍᴍᴀɴᴅs.</b>"
                ),
                reply_markup=InlineKeyboardMarkup(out),
            )

            if await is_on_off(2):
                return await app.send_message(
                    chat_id=config.LOGGER_ID,
                    text=f"{message.from_user.mention} Hᴀs Sᴛᴀʀᴛᴇᴅ Tʜᴇ Bᴏᴛ.\n\n<b>Usᴇʀ Iᴅ :</b> <code>{message.from_user.id}</code>\n<b>Usᴇʀɴᴀᴍᴇ :</b> @{message.from_user.username}",
                )
        except Exception as e:
            print(e)
            await message.reply_text(_["start_7"].format(app.mention))
            return
