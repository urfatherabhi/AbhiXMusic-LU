import asyncio
import time
import datetime
from contextlib import suppress
from string import ascii_lowercase
from typing import Union

from config import BANNED_USERS, OWNER_ID, SUDOERS
from pyrogram import filters
from pyrogram.enums import ChatMembersFilter, ChatMemberStatus, ChatType
from pyrogram.errors import UserNotParticipant, PeerIdInvalid, RPCError
from pyrogram.types import (
    CallbackQuery,
    ChatPermissions,
    ChatPrivileges,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from AbhiXMusic import app
from AbhiXMusic.core.mongo import mongodb

warnsdb = mongodb.warns

FOOTER_TEXT = "\n\n➠ Nᴏᴡ Sᴀʏ Pᴀᴘᴀ Tᴏ ➠ ||😎 @URFather_ABHI 🔥||"

async def extract_user_and_reason_or_title(message: Message, sender_chat=False, index_for_text_start: int = 2):
    args = message.text.strip().split()
    user_id = None
    text_content = None
    
    if message.reply_to_message:
        reply = message.reply_to_message
        if reply.from_user:
            user_id = reply.from_user.id
        elif reply.sender_chat and reply.sender_chat.id != message.chat.id and sender_chat:
            user_id = reply.sender_chat.id
        
        text_content = " ".join(args[1:]) if len(args) > 1 else None
        
    elif len(args) > 1:
        # Try to extract user by @username or ID first
        if args[1].startswith("@"):
            try:
                user = await app.get_users(args[1])
                user_id = user.id
                text_content = " ".join(args[index_for_text_start:]) if len(args) > index_for_text_start else None
            except Exception:
                pass # Continue to try by name if @username lookup fails
        elif args[1].isdigit():
            try:
                potential_user_id = int(args[1])
                user = await app.get_users(potential_user_id)
                user_id = user.id
                text_content = " ".join(args[index_for_text_start:]) if len(args) > index_for_text_start else None
            except Exception:
                pass # Continue to try by name if ID lookup fails
        
        # If user_id is still None, try to find by name
        if user_id is None:
            full_name_query_parts = []
            found_user = None
            for i in range(1, len(args)):
                full_name_query_parts.append(args[i])
                potential_name = " ".join(full_name_query_parts)
                
                # Check for first name match or full name match
                async for member in app.get_chat_members(message.chat.id):
                    if member.user:
                        user_full_name = ((member.user.first_name or "") + " " + (member.user.last_name or "")).strip()
                        if potential_name.lower() == user_full_name.lower() or \
                           potential_name.lower() == (member.user.first_name or "").lower(): # <--- सुधार यहाँ किया गया है
                            found_user = member.user
                            # Set index for text content based on where the name ended
                            index_for_text_start = i + 1 
                            break
                if found_user:
                    user_id = found_user.id
                    text_content = " ".join(args[index_for_text_start:]) if len(args) > index_for_text_start else None
                    break
            
            # If no user found by name either, the whole input after command is text_content
            if user_id is None:
                text_content = " ".join(args[1:])


    return user_id, text_content

async def time_converter(message: Message, time_value: str) -> int:
    unit = time_value[-1].lower()
    value_str = time_value[:-1]
    
    if not value_str.isdigit():
        await message.reply_text(f"Iɴᴠᴀʟɪᴅ ᴛɪᴍᴇ ꜰᴏʀᴍᴀᴛ. Uꜱᴇ s, ᴍ, h, ᴏr d (ᴇ.g., 5s, 5m, 2h, 3d). {FOOTER_TEXT}")
        raise ValueError("Iɴᴠᴀʟɪᴅ ᴛɪᴍᴇ ꜰᴏʀᴍᴀᴛ")

    value = int(value_str)
    
    current_time = int(time.time())
    if unit == "s":
        return current_time + value
    elif unit == "m":
        return current_time + (value * 60)
    elif unit == "h":
        return current_time + (value * 3600)
    elif unit == "d":
        return current_time + (value * 86400)
    else:
        await message.reply_text(f"Iɴᴠᴀʟɪᴅ ᴛɪᴍᴇ ꜰᴏʀᴍᴀᴛ. Uꜱᴇ s, ᴍ, h, ᴏr d (ᴇ.g., 5s, 5m, 2h, 3d). {FOOTER_TEXT}")
        raise ValueError("Iɴᴠᴀʟɪᴅ ᴛɪᴍᴇ ꜰᴏʀᴍᴀᴛ")

def ikb(data: dict) -> InlineKeyboardMarkup:
    keyboard = []
    for key, value in data.items():
        keyboard.append([InlineKeyboardButton(text=key, callback_data=value)])
    return InlineKeyboardMarkup(keyboard)

__MODULE__ = "Bᴀɴ"
__HELP__ = """
/ban - Ban A User
/sban - Delete All Messages Of User That Sended In Group And Ban The User
/tban [time] [reason] - Ban A User For Specific Time (e.g., 1h spamming)
/unban - Unban A User
/warn - Warn A User
/swarn - Delete All The Message Sended In Group And Warn The User
/rmwarns - Remove All Warning Of A User
/warns - Show Warning Of A User
/kick - Kick A User
/skick - Delete The Replied Message Kicking Its Sender
/kickme - Kick yourself from the group (allows rejoining) - *everyone can use*
/purge - Purge Messages
/purge [n] - Purge "n" Number Of Messages From Replied Message
/del - Delete Replied Message
/promote [title] - Promote A Member (e.g., /promote @user Admin)
/fullpromote [title] - Promote A Member With All Rights (e.g., /fullpromote @user Super Admin)
/demote - Demote A Member
/pin - Pin A Message
/unpin - Unpin A Message
/unpinall - Unpinall Messages
/mute - Mute A User
/tmute [time] [reason] - Mute A User For Specific Time (e.g., 30m chatting)
/unmute - Unmute A User
/zombies - Ban Deleted Accounts
/report | @admins | @admin - Report A Message To Admins.
/link - Send In Group/SuperGroup Invite Link.
"""

async def int_to_alpha(user_id: int) -> str:
    alphabet = list(ascii_lowercase)[:10]
    text = ""
    user_id = str(user_id)
    for i in user_id:
        text += alphabet[int(i)]
    return text

async def get_warns(chat_id: int) -> dict[str, int]:
    warns = await warnsdb.find_one({"chat_id": chat_id})
    if not warns:
        return {}
    return warns["warns"]

async def get_warn(chat_id: int, name: str) -> Union[bool, dict]:
    name = name.lower().strip()
    warns = await get_warns(chat_id)
    if name in warns:
        return warns[name]

async def add_warn(chat_id: int, name: str, warn: dict):
    name = name.lower().strip()
    warns = await get_warns(chat_id)
    warns[name] = warn
    await warnsdb.update_one(
        {"chat_id": chat_id}, {"$set": {"warns": warns}}, upsert=True
    )

async def remove_warns(chat_id: int, name: str) -> bool:
    warnsd = await get_warns(chat_id)
    name = name.lower().strip()
    if name in warnsd:
        del warnsd[name]
        await warnsdb.update_one(
            {"chat_id": chat_id},
            {"$set": {"warns": warnsd}},
            upsert=True,
        )
        return True
    return False

async def member_permissions(chat_id: int, user_id: int):
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.privileges.__dict__ if member.privileges else {}
    except Exception:
        return {}

async def is_admin_with_privilege(
    message: Message,
    can_restrict_members: bool = False,
    can_promote_members: bool = False,
    can_delete_messages: bool = False,
    can_pin_messages: bool = False,
    can_change_info: bool = False,
    can_invite_users: bool = False,
):
    from_user_id = message.from_user.id
    chat_id = message.chat.id

    if from_user_id == OWNER_ID or from_user_id in SUDOERS:
        return True

    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply_text(f"ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ Cᴀɴ ᴏɴʟʏ ʙᴇ Uꜱᴇᴅ ɪɴ ɢʀᴏᴜᴘꜱ. {FOOTER_TEXT}")
        return False

    try:
        member = await message.chat.get_member(from_user_id)
    except Exception:
        await message.reply_text(f"Yᴏᴜ Aʀᴇ ɴᴏᴛ ᴀɴ Aᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ᴄʜᴀᴛ. {FOOTER_TEXT}")
        return False

    if member.status != ChatMemberStatus.ADMINISTRATOR and member.status != ChatMemberStatus.OWNER:
        await message.reply_text(f"Yᴏᴜ ɴᴏᴛ ᴀɴ Aᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ᴄʜᴀᴛ. {FOOTER_TEXT}")
        return False

    privileges = member.privileges

    bot_member = await app.get_chat_member(chat_id, app.id)
    if not bot_member.privileges:
        await message.reply_text(f"ɪ ᴅᴏɴ'T ʜᴀᴠᴇ ᴀɴʏ Aᴅᴍɪɴ ᴘᴇʀᴍɪꜱꜱɪᴏɴꜱ ɪɴ ᴛʜɪꜱ ᴄʜᴀᴛ. {FOOTER_TEXT}")
        return False
    
    if can_restrict_members and not bot_member.privileges.can_restrict_members:
        await message.reply_text(f"ɪ ᴅᴏɴ'T ʜᴀᴠᴇ 'ʀᴇꜱᴛʀɪᴄᴛ Uꜱᴇʀꜱ' ᴘᴇʀᴍɪꜱꜱɪᴏɴ ɪɴ ᴛʜɪꜱ ᴄʜᴀᴛ. {FOOTER_TEXT}")
        return False
    if can_promote_members and not bot_member.privileges.can_promote_members:
        await message.reply_text(f"ɪ ᴅᴏɴ'T ʜᴀᴠᴇ 'ᴀᴅᴅ ɴᴇᴡ Aᴅᴍɪɴꜱ' ᴘᴇʀᴍɪꜱꜱɪᴏɴ ɪɴ ᴛʜɪꜱ ᴄʜᴀᴛ. {FOOTER_TEXT}")
        return False
    if can_delete_messages and not bot_member.privileges.can_delete_messages:
        await message.reply_text(f"ɪ ᴅᴏɴ'T ʜᴀᴠᴇ 'ᴅᴇʟᴇᴛᴇ ᴍᴇꜱꜱᴀɢᴇꜱ' ᴘᴇʀᴍɪꜱꜱɪᴏɴ ɪɴ ᴛʜɪꜱ ᴄʜᴀᴛ. {FOOTER_TEXT}")
        return False
    if can_pin_messages and not bot_member.privileges.can_pin_messages:
        await message.reply_text(f"ɪ ᴅᴏɴ'T ʜᴀᴠᴇ 'ᴘɪɴ ᴍᴇꜱꜱᴀɢᴇꜱ' ᴘᴇʀᴍɪꜱꜱɪᴏɴ ɪɴ ᴛʜɪꜱ ᴄʜᴀᴛ. {FOOTER_TEXT}")
        return False
    if can_change_info and not bot_member.privileges.can_change_info:
        await message.reply_text(f"ɪ ᴅᴏɴ'T ʜᴀᴠᴇ 'ᴄʜᴀɴɢᴇ ᴄʜᴀᴛ ɪɴꜰᴏ' ᴘᴇʀᴍɪꜱꜱɪᴏɴ ɪɴ ᴛʜɪꜱ ᴄʜᴀᴛ. {FOOTER_TEXT}")
        return False
    if can_invite_users and not bot_member.privileges.can_invite_users:
        await message.reply_text(f"ɪ ᴅᴏɴ'T ʜᴀᴠᴇ 'ɪɴᴠɪᴛᴇ Uꜱᴇʀꜱ' ᴘᴇʀᴍɪꜱꜱɪᴏɴ ɪɴ ᴛʜɪꜱ ᴄʜᴀᴛ. {FOOTER_TEXT}")
        return False

    if can_restrict_members and not privileges.can_restrict_members:
        await message.reply_text(f"Yᴏᴜ ᴅᴏɴ'T ʜᴀᴠᴇ 'ʀᴇꜱᴛʀɪᴄᴛ Uꜱᴇʀꜱ' ᴘᴇʀᴍɪꜱꜱɪᴏɴ. {FOOTER_TEXT}")
        return False
    if can_promote_members and not privileges.can_promote_members:
        await message.reply_text(f"Yᴏᴜ ᴅᴏɴ'T ʜᴀᴠᴇ 'ᴀᴅᴅ ɴᴇᴡ Aᴅᴍɪɴꜱ' ᴘᴇʀᴍɪꜱꜱɪᴏɴ. {FOOTER_TEXT}")
        return False
    if can_delete_messages and not privileges.can_delete_messages:
        await message.reply_text(f"Yᴏᴜ ᴅᴏɴ'T ʜᴀᴠᴇ 'ᴅᴇʟᴇᴛᴇ ᴍᴇꜱꜱᴀɢᴇꜱ' ᴘᴇʀᴍɪꜱꜱɪᴏɴ. {FOOTER_TEXT}")
        return False
    if can_pin_messages and not privileges.can_pin_messages:
        await message.reply_text(f"Yᴏᴜ ᴅᴏɴ'T ʜᴀᴠᴇ 'ᴘɪɴ ᴍᴇꜱꜱᴀɢᴇꜱ' ᴘᴇʀᴍɪꜱꜱɪᴏɴ. {FOOTER_TEXT}")
        return False
    if can_change_info and not privileges.can_change_info:
        await message.reply_text(f"Yᴏᴜ ᴅᴏɴ'T ʜᴀᴠᴇ 'ᴄʜᴀɴɢᴇ ᴄʜᴀᴛ ɪɴꜰᴏ' ᴘᴇʀᴍɪꜱꜱɪᴏɴ. {FOOTER_TEXT}")
        return False
    if can_invite_users and not privileges.can_invite_users:
        await message.reply_text(f"Yᴏᴜ ᴅᴏɴ'T ʜᴀᴠᴇ 'ɪɴᴠɪᴛᴇ Uꜱᴇʀꜱ' ᴘᴇʀᴍɪꜱꜱɪᴏɴ. {FOOTER_TEXT}")
        return False

    return True


@app.on_message(filters.command(["kick", "skick"]) & ~filters.private & ~BANNED_USERS)
async def kickFunc(_, message: Message):
    if not await is_admin_with_privilege(message, can_restrict_members=True):
        return

    user_id, reason = await extract_user_and_reason_or_title(message, index_for_text_start=2) 
    if not user_id:
        return await message.reply_text(f"I Cᴀɴ't Fɪɴᴅ Tʜᴀᴛ Usᴇr. Pʟᴇᴀꜱᴇ Rᴇᴘly Tᴏ A Uꜱᴇr Oʀ Pʀᴏᴠɪᴅᴇ Tʜᴇɪʀ Uꜱᴇrɴᴀᴍᴇ/Iᴅ Oʀ Nᴀᴍᴇ. {FOOTER_TEXT}")
    
    if user_id == app.id:
        return await message.reply_text(f"I Cᴀɴ't Kɪᴄᴋ Mʏsᴇʟf, ɪ Cᴀɴ Lᴇᴀᴠᴇ Iғ Yᴏᴜ Wᴀɴᴛ. {FOOTER_TEXT}")
    
    if user_id == OWNER_ID or user_id in SUDOERS:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(f"Yᴏᴜ Cᴀɴɴᴏᴛ Kɪᴄᴋ A Sᴜᴅᴏ Uꜱᴇr Oʀ Tʜᴇ Oᴡɴᴇr. {FOOTER_TEXT}")
        elif user_id == message.from_user.id:
             return await message.reply_text(f"Yᴏᴜ Cᴀɴ'T Kɪᴄᴋ Yᴏᴜʀꜱᴇʟf. {FOOTER_TEXT}")

    try:
        user = await app.get_users(user_id)
        mention = user.mention
        msg = f"""
**Kɪᴄᴋᴇᴅ Usᴇr:** {mention}
**Kɪᴄᴋᴇᴅ Bʏ:** {message.from_user.mention if message.from_user else 'ᴀɴᴏɴʏᴍᴏᴜꜱ'}
**Rᴇᴀsᴏɴ:** {reason or 'Nᴏ Rᴇᴀsᴏɴ Pʀᴏᴠɪᴅᴇᴅ'}  {FOOTER_TEXT}"""
        
        await message.chat.ban_member(user_id)
        
        if message.command[0][0] == "s" and message.reply_to_message:
            await message.reply_to_message.delete()
        
        await message.reply_text(msg)
        await asyncio.sleep(1)
        await message.chat.unban_member(user_id)
        
    except UserNotParticipant:
        await message.reply_text(f"ᴛʜɪꜱ Uꜱᴇr ɪꜱ ɴᴏᴛ ɪɴ ᴛʜɪꜱ ᴄʜᴀᴛ ᴏʀ Aʟʀᴇᴀᴅʏ ᴋɪᴄᴋᴇᴅ. {FOOTER_TEXT}")
    except Exception as e:
        await message.reply_text(f"Fᴀɪʟᴇᴅ Tᴏ ᴋɪᴄᴋ: {str(e)} {FOOTER_TEXT}")

@app.on_message(filters.command("kickme") & ~filters.private & ~BANNED_USERS)
async def kickme_func(_, message: Message):
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return await message.reply_text(f"ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ Cᴀɴ ᴏɴʟʏ ʙᴇ Uꜱᴇᴅ ɪɴ ɢʀᴏᴜᴘꜱ. {FOOTER_TEXT}")

    user_id = message.from_user.id
    
    funny_quotes = [
        "Looks like someone needed a little push out the door! 👋",
        "Poof! And just like that, you're a free bird... or a kicked one. 🕊️",
        "Don't worry, the door's open for a quick re-entry! 😉",
        "Oops, did you just kick yourself? That's a new level of self-control! 😂",
        "Farewell, for now! May your return be swift and glorious. ✨",
        "Out of sight, not out of mind... just out of this chat. Bye! 👋",
        "Well, that was a dramatic exit! Hope you enjoyed the show! 🎬",
        "You asked for it, you got it! See ya, wouldn't wanna be ya... unless you rejoin. 😉",
    ]
    import random
    quote = random.choice(funny_quotes)

    try:
        bot_member = await app.get_chat_member(message.chat.id, app.id)
        if not bot_member.privileges or not bot_member.privileges.can_restrict_members:
            return await message.reply_text(f"ɪ ᴅᴏɴ'T ʜᴀᴠᴇ ᴘᴇʀᴍɪꜱꜱɪᴏɴ Tᴏ ᴋɪᴄᴋ/ᴜɴʙᴀɴ ᴍᴇᴍʙᴇʀꜱ. ᴘʟᴇᴀꜱᴇ ɢʀᴀɴᴛ ᴍᴇ 'ʀᴇꜱᴛʀɪᴄᴛ Uꜱᴇʀꜱ' ᴘᴇʀᴍɪꜱꜱɪᴏɴ. {FOOTER_TEXT}")
        
        await message.chat.ban_member(user_id)
        await message.reply_text(f"**{quote}**\n\nYᴏᴜ ʜᴀᴠᴇ ʙᴇᴇɴ ᴋɪᴄᴋᴇᴅ ʙʏ Yᴏᴜʀꜱᴇʟf! Yᴏᴜ Cᴀɴ ʀᴇjoin ᴛʜᴇ ɢʀᴏᴜᴘ ᴀɴʏᴛɪᴍᴇ. {FOOTER_TEXT}")
        await asyncio.sleep(1)
        await message.chat.unban_member(user_id)
    except Exception as e:
        await message.reply_text(f"Fᴀɪʟᴇᴅ Tᴏ ᴋɪᴄᴋ Yᴏᴜʀꜱᴇʟf: {str(e)} {FOOTER_TEXT}")

@app.on_message(
    filters.command(["ban", "sban", "tban"]) & ~filters.private & ~BANNED_USERS
)
async def banFunc(_, message: Message):
    if not await is_admin_with_privilege(message, can_restrict_members=True):
        return

    if message.command[0] == "tban":
        args = message.text.strip().split()
        user_id = None
        time_value = None
        reason_text = None

        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            if len(args) > 1:
                time_value = args[1]
                reason_text = " ".join(args[2:])
        else: 
            potential_user_input_parts = []
            found_user_by_name = None
            start_index_for_time = -1
            
            for i in range(1, len(args)):
                potential_user_input_parts.append(args[i])
                potential_name = " ".join(potential_user_input_parts)
                
                async for member in app.get_chat_members(message.chat.id):
                    if member.user:
                        user_full_name = ((member.user.first_name or "") + " " + (member.user.last_name or "")).strip()
                        if potential_name.lower() == user_full_name.lower() or \
                           potential_name.lower() == (member.user.first_name or "").lower():
                            found_user_by_name = member.user
                            start_index_for_time = i + 1 # The next argument after the name
                            break
                if found_user_by_name:
                    user_id = found_user_by_name.id
                    break
            
            if found_user_by_name:
                if len(args) > start_index_for_time:
                    time_value = args[start_index_for_time]
                    reason_text = " ".join(args[start_index_for_time + 1:])
            else: # If it's not @username, ID, or a recognized name, then it's an invalid format for user
                if len(args) > 1:
                    if args[1].startswith("@") or args[1].isdigit():
                        try:
                            target_user = await app.get_users(args[1])
                            user_id = target_user.id
                            if len(args) > 2:
                                time_value = args[2]
                                reason_text = " ".join(args[3:])
                        except Exception:
                            pass # Let the next check handle if user_id is still None
                    else: # If it's not @username, ID, or a recognized name, then it's an invalid format for user
                        return await message.reply_text(f"Iɴᴠᴀʟɪᴅ Uꜱᴇrɴᴀᴍᴇ/ɪᴅ ᴏʀ ᴜɴʀᴇᴄᴏɢɴɪᴢᴇᴅ ꜰᴏʀᴍᴀᴛ. {FOOTER_TEXT}")

        if not user_id:
            return await message.reply_text(f"ɪ Cᴀɴ'T ғɪɴᴅ ᴛʜᴀᴛ ᴜsᴇr. ᴘʟᴇᴀꜱᴇ ʀᴇᴘly ᴏʀ ᴘʀᴏᴠɪᴅᴇ Uꜱᴇrɴᴀᴍᴇ/ɪᴅ/ɴᴀᴍᴇ. {FOOTER_TEXT}")
        
        if not time_value:
            return await message.reply_text(f"ᴘʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴛɪᴍᴇ ᴀɴᴅ ᴏᴘᴛɪᴏɴᴀʟ ʀᴇᴀꜱᴏɴ ꜰᴏʀ ᴛᴇᴍᴘᴏʀᴀʀʏ ʙᴀɴ. ᴇ.g., `/ᴛʙᴀɴ 1ʜ ꜱᴘᴀᴍᴍɪɴɢ` {FOOTER_TEXT}")
        
        try:
            temp_ban_unix_timestamp = await time_converter(message, time_value)
            temp_ban_until = datetime.datetime.fromtimestamp(temp_ban_unix_timestamp)
        except ValueError:
            return 

        try:
            user = await app.get_users(user_id)
            mention = user.mention
        except Exception:
             mention = (
                message.reply_to_message.sender_chat.title
                if message.reply_to_message and message.reply_to_message.sender_chat
                else "ᴀɴᴏɴʏᴍᴏᴜꜱ ᴄʜᴀɴɴᴇʟ"
            )
        
        msg = (
            f"**ʙᴀɴɴᴇᴅ Uꜱᴇr:** {mention} 🔨\n"
            f"**ʙᴀɴɴᴇᴅ ʙʏ:** {message.from_user.mention if message.from_user else 'ᴀɴᴏɴʏᴍᴏᴜꜱ'}\n"
            f"**ʙᴀɴɴᴇᴅ ꜰᴏr:** {time_value}\n"
        )
        if reason_text:
            msg += f"**ʀᴇᴀꜱᴏɴ:** {reason_text}"
        msg += FOOTER_TEXT
        
        try:
            await message.chat.ban_member(user_id, until_date=temp_ban_until)
            await message.reply_text(msg)
        except UserNotParticipant:
            await message.reply_text(f"ᴛʜɪꜱ Uꜱᴇr ɪꜱ ɴᴏᴛ ɪɴ ᴛʜɪꜱ ᴄʜᴀᴛ ᴏʀ Aʟʀᴇᴀᴅʏ ʙᴀɴɴᴇᴅ. {FOOTER_TEXT}")
        except RPCError as e:
            await message.reply_text(f"Fᴀɪʟᴇᴅ Tᴏ ᴛᴇᴍᴘᴏʀᴀʀɪʟʏ ʙᴀɴ: {e.MESSAGE} {FOOTER_TEXT}")
        except Exception as e:
            await message.reply_text(f"Fᴀɪʟᴇᴅ Tᴏ ᴛᴇᴍᴘᴏʀᴀʀɪʟʏ ʙᴀɴ: {str(e)} {FOOTER_TEXT}")
        return

    # For /ban and /sban
    user_id, reason = await extract_user_and_reason_or_title(message, sender_chat=True, index_for_text_start=2)
    if not user_id:
        return await message.reply_text(f"I Cᴀɴ't Fɪɴd Tʜᴀᴛ Usᴇr. Pʟᴇᴀꜱᴇ Rᴇᴘly Tᴏ A Uꜱᴇr Oʀ Pʀᴏᴠɪᴅᴇ Tʜᴇɪʀ Uꜱᴇrɴᴀᴍᴇ/Iᴅ Oʀ nᴀᴍᴇ. {FOOTER_TEXT}")
    
    if user_id == app.id:
        return await message.reply_text(f"ɪ Cᴀɴ'T ʙᴀɴ ᴍʏꜱᴇʟf, ɪ Cᴀɴ ʟᴇᴀᴠᴇ ɪꜰ Yᴏᴜ ᴡᴀɴᴛ. {FOOTER_TEXT}")
    
    if user_id == OWNER_ID or user_id in SUDOERS:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(f"Yᴏᴜ Cᴀɴɴᴏᴛ ʙᴀɴ ᴀ Sᴜᴅᴏ Uꜱᴇr ᴏʀ ᴛʜᴇ ᴏᴡɴᴇr. {FOOTER_TEXT}")
        elif user_id == message.from_user.id:
             return await message.reply_text(f"Yᴏᴜ Cᴀɴ'T ʙᴀɴ Yᴏᴜʀꜱᴇʟf. {FOOTER_TEXT}")

    try:
        user = await app.get_users(user_id)
        mention = user.mention
    except Exception:
        mention = (
            message.reply_to_message.sender_chat.title
            if message.reply_to_message and message.reply_to_message.sender_chat
            else "ᴀɴᴏɴʏᴍᴏᴜꜱ ᴄʜᴀɴɴᴇʟ"
        )
    
    msg = (
        f"**ʙᴀɴɴᴇᴅ Uꜱᴇr:** {mention} 🔨\n"
        f"**ʙᴀɴɴᴇᴅ ʙʏ:** {message.from_user.mention if message.from_user else 'ᴀɴᴏɴʏᴍᴏᴜꜱ'}\n"
    )
    
    if message.command[0] == "sban" and message.reply_to_message:
        await message.reply_to_message.delete()
    
    if reason:
        msg += f"**ʀᴇᴀꜱᴏɴ:** {reason}"
    msg += FOOTER_TEXT
    
    try:
        member = await message.chat.get_member(user_id)
        if member.status == ChatMemberStatus.BANNED:
            return await message.reply_text(f"{mention} ɪꜱ Aʟʀᴇᴀᴅʏ ʙᴀɴɴᴇᴅ. {FOOTER_TEXT}")

        await message.chat.ban_member(user_id)
        await message.reply_text(msg)
    except UserNotParticipant:
        await message.reply_text(f"ᴛʜɪꜱ Uꜱᴇr ɪꜱ ɴᴏᴛ ɪɴ ᴛʜɪꜱ ᴄʜᴀᴛ ᴏʀ Aʟʀᴇᴀᴅʏ ʙᴀɴɴᴇᴅ. {FOOTER_TEXT}")
    except RPCError as e:
        await message.reply_text(f"Fᴀɪʟᴇᴅ Tᴏ ʙᴀɴ: {e.MESSAGE} {FOOTER_TEXT}")
    except Exception as e:
        await message.reply_text(f"Fᴀɪʟᴇᴅ Tᴏ ʙᴀɴ: {str(e)} {FOOTER_TEXT}")

@app.on_message(filters.command("unban") & ~filters.private & ~BANNED_USERS)
async def unban_func(_, message: Message):
    if not await is_admin_with_privilege(message, can_restrict_members=True):
        return

    user_id, _ = await extract_user_and_reason_or_title(message, index_for_text_start=2) 
    if not user_id:
        return await message.reply_text(f"I Cᴀɴ'T Fɪɴd Tʜᴀᴛ Uꜱᴇr. Pʟᴇᴀꜱᴇ Rᴇᴘly Tᴏ A Uꜱᴇr Oʀ Pʀᴏᴠɪᴅᴇ Tʜᴇɪʀ Uꜱᴇrɴᴀᴍᴇ/Iᴅ Oʀ Nᴀᴍᴇ. {FOOTER_TEXT}")
    
    try:
        member = await message.chat.get_member(user_id)
        if member.status != ChatMemberStatus.BANNED:
            return await message.reply_text(f"{member.user.mention} ɪꜱ Aʟʀᴇᴀᴅʏ ᴜɴʙᴀɴɴᴇᴅ. 🎉 {FOOTER_TEXT}")

        await message.chat.unban_member(user_id)
        user = await app.get_users(user_id)
        umention = user.mention
        await message.reply_text(f"ᴜɴʙᴀɴɴᴇᴅ! {umention} 🎉 {FOOTER_TEXT}")
    except UserNotParticipant:
        await message.reply_text(f"ᴛʜɪꜱ Uꜱᴇr ɪꜱ ɴᴏᴛ ɪɴ ᴛʜɪꜱ ᴄʜᴀᴛ ᴏʀ Aʟʀᴇᴀᴅʏ ᴜɴʙᴀɴɴᴇᴅ. {FOOTER_TEXT}")
    except PeerIdInvalid:
        await message.reply_text(f"Iɴᴠᴀʟɪᴅ Uꜱᴇr ɪᴅ ᴏʀ ɴᴏᴛ ꜰᴏᴜɴᴅ. {FOOTER_TEXT}")
    except RPCError as e:
        await message.reply_text(f"Fᴀɪʟᴇᴅ Tᴏ ᴜɴʙᴀɴ: {e.MESSAGE} {FOOTER_TEXT}")
    except Exception as e:
        await message.reply_text(f"Fᴀɪʟᴇᴅ Tᴏ ᴜɴʙᴀɴ: {str(e)} {FOOTER_TEXT}")

@app.on_message(
    filters.command(["promote", "fullpromote"]) & ~filters.private & ~BANNED_USERS
)
async def promoteFunc(_, message: Message):
    if not await is_admin_with_privilege(message, can_promote_members=True):
        return

    user_id = None
    title = None
    args = message.text.strip().split()

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        title = " ".join(args[1:]) if len(args) > 1 else None
    elif len(args) > 1:
        # Check if the first argument is a mention or ID
        if args[1].startswith("@") or args[1].isdigit():
            try:
                target_user = await app.get_users(args[1])
                user_id = target_user.id
                title = " ".join(args[2:]) if len(args) > 2 else None
            except Exception:
                return await message.reply_text(f"Iɴᴠᴀʟɪᴅ Uꜱᴇrɴᴀᴍᴇ/ɪᴅ ᴏʀ ᴜɴᴀʙʟᴇ Tᴏ ғᴇᴛᴄʜ Uꜱᴇr. {FOOTER_TEXT}")
        else:
            # Try to find user by name from the first argument
            full_name_query_parts = []
            current_user_id = None
            current_title_parts = []

            # Iterate through arguments to find a user by name
            for i in range(1, len(args)):
                full_name_query_parts.append(args[i])
                potential_name = " ".join(full_name_query_parts)
                found_user = None
                async for member in app.get_chat_members(message.chat.id):
                    if member.user and (potential_name.lower() == ((member.user.first_name or "") + " " + (member.user.last_name or "")).lower() or \
                                       potential_name.lower() == (member.user.first_name or "").lower()):
                        found_user = member.user
                        break
                
                if found_user:
                    current_user_id = found_user.id
                    # The rest of the arguments after the name would be the title
                    current_title_parts = args[i+1:]
                    break
            
            user_id = current_user_id
            title = " ".join(current_title_parts) if current_title_parts else None

    if not user_id:
        return await message.reply_text(f"I Cᴀɴ'T Fɪɴd Tʜᴀᴛ Uꜱᴇr. Pʟᴇᴀꜱᴇ Rᴇᴘly Tᴏ A Uꜱᴇr Oʀ Pʀᴏᴠɪᴅᴇ Tʜᴇɪʀ Uꜱᴇrɴᴀᴍᴇ/Iᴅ Oʀ Nᴀᴍᴇ. {FOOTER_TEXT}")
    if user_id == app.id:
        return await message.reply_text(f"ɪ Cᴀɴ'T Pʀᴏᴍᴏᴛᴇ ᴍʏꜱᴇʟf. {FOOTER_TEXT}")

    if user_id == message.from_user.id:
        if user_id == OWNER_ID or user_id in SUDOERS:
            return await message.reply_text(f"Yᴏᴜ Cᴀɴ'T Pʀᴏᴍᴏᴛᴇ YᴏᴜʀꜱᴇLf. {FOOTER_TEXT}")

    try:
        user = await app.get_users(user_id)
        if not user:
            return await message.reply_text(f"ᴜɴᴀʙʟᴇ Tᴏ ғᴇᴛᴄʜ ᴜsᴇ rᴅᴇᴛᴀɪʟꜱ. {FOOTER_TEXT}")
        umention = user.mention
        
        target_member = await app.get_chat_member(message.chat.id, user_id)
        
        if target_member.status == ChatMemberStatus.ADMINISTRATOR:
            if message.command[0] == "fullpromote":
                if (target_member.privileges.can_change_info and
                    target_member.privileges.can_invite_users and
                    target_member.privileges.can_delete_messages and
                    target_member.privileges.can_restrict_members and
                    target_member.privileges.can_pin_messages and
                    target_member.privileges.can_promote_members and
                    target_member.privileges.can_manage_chat and
                    target_member.privileges.can_manage_video_chats):
                    if title and target_member.custom_title == title:
                         return await message.reply_text(f"{umention} ɪꜱ Aʟʀᴇᴀᴅʏ Fᴜʟʟʏ Pʀᴏᴍᴏᴛᴇᴅ Wɪᴛʜ ᴛʜɪꜱ ᴛɪᴛʟᴇ. ✨ {FOOTER_TEXT}")
                    elif not title:
                         return await message.reply_text(f"{umention} ɪꜱ Aʟʀᴇᴀᴅʏ Fᴜʟʟʏ Pʀᴏᴍᴏᴛᴇᴅ. ✨ {FOOTER_TEXT}")

            else:
                if target_member.status == ChatMemberStatus.ADMINISTRATOR:
                    if title and target_member.custom_title == title:
                        return await message.reply_text(f"{umention} ɪꜱ Aʟʀᴇᴀᴅʏ Pʀᴏᴍᴏᴛᴇᴅ Wɪᴛʜ ᴛɪꜱ ᴛɪᴛʟᴇ. ✨ {FOOTER_TEXT}")
                    elif not title:
                        return await message.reply_text(f"{umention} ɪꜱ Aʟʀᴇᴀᴅʏ Pʀᴏᴍᴏᴛᴇᴅ. ✨ {FOOTER_TEXT}")

        if not title:
            title = "Aᴅᴍɪɴ" if message.command[0] == "promote" else "Sᴜᴘᴇᴇʀ Aᴅᴍɪɴ"

        if message.command[0] == "fullpromote":
            new_privileges = ChatPrivileges(
                can_change_info=True,
                can_invite_users=True,
                can_delete_messages=True,
                can_restrict_members=True,
                can_pin_messages=True,
                can_promote_members=True,
                can_manage_chat=True,
                can_manage_video_chats=True,
            )
            await message.chat.promote_member(
                user_id=user_id,
                privileges=new_privileges,
            )
            if title:
                await app.set_administrator_title(message.chat.id, user_id, title)
            return await message.reply_text(f"Fᴜʟʟʏ Pʀᴏᴍᴏᴛᴇᴅ! {umention} Wɪᴛʜ ᴛɪᴛʟᴇ: **{title}** ✨ {FOOTER_TEXT}")

        new_privileges = ChatPrivileges(
            can_change_info=False,
            can_invite_users=True,
            can_delete_messages=True,
            can_restrict_members=False,
            can_pin_messages=True,
            can_promote_members=False,
            can_manage_chat=False,
            can_manage_video_chats=True,
            can_post_messages=False,
            can_edit_messages=False,
            can_manage_topics=False,
        )
        await message.chat.promote_member(
            user_id=user_id,
            privileges=new_privileges,
        )
        if title:
            await app.set_administrator_title(message.chat.id, user_id, title)
        await message.reply_text(f"Pʀᴏᴍᴏᴛᴇᴅ! {umention} Wɪᴛʜ ᴛɪᴛʟᴇ: **{title}** ✨ {FOOTER_TEXT}")
    except UserNotParticipant:
        await message.reply_text(f"ᴛʜɪꜱ Uꜱᴇr ɪꜱ ɴᴏᴛ ɪɴ ᴛʜɪꜱ ᴄʜᴀᴛ. {FOOTER_TEXT}")
    except PeerIdInvalid:
        await message.reply_text(f"Iɴᴠᴀʟɪᴅ Uꜱᴇr ɪᴅ ᴏʀ ɴᴏᴛ ꜰᴏᴜɴᴅ. {FOOTER_TEXT}")
    except RPCError as e:
        await message.reply_text(f"Fᴀɪʟᴇᴅ Tᴏ Pʀᴏᴍᴏᴛᴇ: {e.MESSAGE} {FOOTER_TEXT}")
    except Exception as e:
        await message.reply_text(f"Fᴀɪʟᴇᴅ Tᴏ Pʀᴏᴍᴏᴛᴇ: {str(e)} {FOOTER_TEXT}")

@app.on_message(filters.command("purge") & ~filters.private)
async def purgeFunc(_, message: Message):
    if not await is_admin_with_privilege(message, can_delete_messages=True):
        return

    replied = message.reply_to_message
    if not replied:
        return await message.reply_text(
            f"Rᴇᴘʟʏ Tᴏ ᴀ Mᴇꜱꜱᴀɢᴇ Tᴏ Pᴜʀɢᴇ ꜰʀᴏᴍ. 🧹 {FOOTER_TEXT}"
        )

    chat_id = message.chat.id
    start_id = replied.id
    end_id = message.id - 1  # We’ll delete this later, so exclude from purge range

    # Optional: handle /purge 10
    try:
        if len(message.command) > 1:
            limit = int(message.command[1])
            end_id = min(start_id + limit - 1, end_id)
    except:
        pass

    deleted = 0
    for msg_id in range(start_id, end_id + 1):
        try:
            await app.delete_messages(chat_id, msg_id)
            deleted += 1
        except:
            continue
    
    try:
        await app.delete_messages(chat_id, message.id)
    except:
        pass

    if deleted > 0:
        await message.reply_text(
            f"Sᴜᴄᴄᴇssғᴜʟʟʏ Pᴜʀɢᴇᴅ {deleted} Mᴇssᴀɢᴇs.🗑️ {FOOTER_TEXT}",
            quote=False
        )
    else:
        await message.reply_text(f"Nᴏ Mᴇssᴀɢᴇs Tᴏ Pᴜʀɢᴇ. {FOOTER_TEXT}")


@app.on_message(filters.command("del") & ~filters.private)
async def delete_message(_, message: Message):
    if not await is_admin_with_privilege(message, can_delete_messages=True):
        return

    if message.reply_to_message:
        await message.reply_to_message.delete()
        await message.delete()
    else:
        await message.reply_text(f"ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ Tᴏ ᴀ ᴍᴇssᴀɢᴇ Tᴏ ᴅᴇʟᴇᴛᴇ ɪᴛ. {FOOTER_TEXT}")


@app.on_message(filters.command("demote") & ~filters.private & ~BANNED_USERS)
async def demoteFunc(_, message: Message):
    if not await is_admin_with_privilege(message, can_promote_members=True):
        return

    user_id, _ = await extract_user_and_reason_or_title(message, index_for_text_start=2) 
    if not user_id:
        return await message.reply_text(f"I Cᴀɴ'T Fɪɴd Tʜᴀᴛ Uꜱᴇr. Pʟᴇᴀꜱᴇ Rᴇᴘly Tᴏ A Uꜱᴇr Oʀ Pʀᴏᴠɪᴅᴇ Tʜᴇɪʀ Uꜱᴇrɴᴀᴍᴇ/Iᴅ Oʀ Nᴀᴍᴇ. {FOOTER_TEXT}")
    
    if user_id == app.id:
        return await message.reply_text(f"ɪ Cᴀɴ'T Dᴇᴍᴏᴛᴇ ᴍʏꜱᴇʟf. {FOOTER_TEXT}")
    
    if user_id == OWNER_ID or user_id in SUDOERS:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(f"Yᴏᴜ Cᴀɴɴᴏᴛ Dᴇᴍᴏᴛᴇ ᴀ Sᴜᴅᴏ Uꜱᴇr ᴏʀ ᴛʜᴇ ᴏᴡɴᴇʀ. {FOOTER_TEXT}")
        elif user_id == message.from_user.id:
             return await message.reply_text(f"Yᴏᴜ Cᴀɴ'T Dᴇᴍᴏᴛᴇ YᴏᴜʀꜱᴇLf. {FOOTER_TEXT}")

    try:
        user = await app.get_users(user_id)
        if not user:
            return await message.reply_text(f"ᴜɴᴀʙʟᴇ Tᴏ ғᴇᴛᴄʜ ᴜsᴇ rᴅᴇᴛᴀɪʟꜱ. {FOOTER_TEXT}")
        umention = user.mention
        
        target_member = await app.get_chat_member(message.chat.id, user_id)
        
        if target_member.status != ChatMemberStatus.ADMINISTRATOR:
            return await message.reply_text(f"{umention} ɪꜱ ɴᴏᴛ ᴀɴ Aᴅᴍɪɴ. 😅 {FOOTER_TEXT}")

        await message.chat.promote_member(
            user_id=user_id,
            privileges=ChatPrivileges(
                can_change_info=False,
                can_invite_users=False,
                can_delete_messages=False,
                can_restrict_members=False,
                can_pin_messages=False,
                can_promote_members=False,
                can_manage_chat=False,
                can_manage_video_chats=False,
            ),
        )
        await message.reply_text(f"Dᴇᴍᴏᴛᴇᴅ! {umention} 👎 {FOOTER_TEXT}")
    except UserNotParticipant:
        await message.reply_text(f"ᴛʜɪꜱ Uꜱᴇr ɪꜱ ɴᴏᴛ ɪɴ ᴛʜɪꜱ ᴄʜᴀᴛ. {FOOTER_TEXT}")
    except PeerIdInvalid:
        await message.reply_text(f"Iɴᴠᴀʟɪᴅ Uꜱᴇr ɪᴅ ᴏʀ ɴᴏᴛ ꜰᴏᴜɴᴅ. {FOOTER_TEXT}")
    except RPCError as e:
        await message.reply_text(f"Fᴀɪʟᴇᴅ Tᴏ Dᴇᴍᴏᴛᴇ: {e.MESSAGE} {FOOTER_TEXT}")
    except Exception as e:
        await message.reply_text(f"Fᴀɪʟᴇᴅ Tᴏ Dᴇᴍᴏᴛᴇ: {str(e)} {FOOTER_TEXT}")


@app.on_message(filters.command("pin") & ~filters.private & ~BANNED_USERS)
async def pin_message_func(_, message: Message):
    if not await is_admin_with_privilege(message, can_pin_messages=True):
        return

    if not message.reply_to_message:
        return await message.reply_text(f"ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ Tᴏ ᴀ ᴍᴇssᴀɢᴇ Tᴏ ᴘɪɴ ɪᴛ. {FOOTER_TEXT}")

    try:
        await message.reply_to_message.pin()
        await message.reply_text(f"ᴍᴇssᴀɢᴇ ᴘɪɴɴᴇᴅ! 📌 {FOOTER_TEXT}")
    except RPCError as e:
        await message.reply_text(f"Fᴀɪʟᴇᴅ Tᴏ ᴘɪɴ ᴍᴇssᴀɢᴇ: {e.MESSAGE} {FOOTER_TEXT}")
    except Exception as e:
        await message.reply_text(f"Fᴀɪʟᴇᴅ Tᴏ ᴘɪɴ ᴍᴇssᴀɢᴇ: {str(e)} {FOOTER_TEXT}")


@app.on_message(filters.command("unpin") & ~filters.private & ~BANNED_USERS)
async def unpin_message_func(_, message: Message):
    if not await is_admin_with_privilege(message, can_pin_messages=True):
        return

    if not message.reply_to_message:
        return await message.reply_text(f"ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ Tᴏ ᴀ ᴍᴇssᴀɢᴇ Tᴏ ᴜɴᴘɪɴ ɪᴛ. {FOOTER_TEXT}")

    try:
        await message.reply_to_message.unpin()
        await message.reply_text(f"ᴍᴇssᴀɢᴇ ᴜɴᴘɪɴɴᴇᴅ! 📍 {FOOTER_TEXT}")
    except RPCError as e:
        await message.reply_text(f"Fᴀɪʟᴇᴅ Tᴏ ᴜɴᴘɪɴ ᴍᴇssᴀɢᴇ: {e.MESSAGE} {FOOTER_TEXT}")
    except Exception as e:
        await message.reply_text(f"Fᴀɪʟᴇᴅ Tᴏ ᴜɴᴘɪɴ ᴍᴇssᴀɢᴇ: {str(e)} {FOOTER_TEXT}")


@app.on_message(filters.command("unpinall") & ~filters.private & ~BANNED_USERS)
async def unpin_all_messages_func(_, message: Message):
    if not await is_admin_with_privilege(message, can_pin_messages=True):
        return

    try:
        await app.unpin_all_chat_messages(message.chat.id)
        await message.reply_text(f"ᴀʟʟ ᴍᴇssᴀɢᴇs ᴜɴᴘɪɴɴᴇᴅ! 📍 {FOOTER_TEXT}")
    except RPCError as e:
        await message.reply_text(f"Fᴀɪʟᴇᴅ Tᴏ ᴜɴᴘɪɴ ᴀʟʟ ᴍᴇssᴀɢᴇs: {e.MESSAGE} {FOOTER_TEXT}")
    except Exception as e:
        await message.reply_text(f"Fᴀɪʟᴇᴅ Tᴏ ᴜɴᴘɪɴ ᴀʟʟ ᴍᴇssᴀɢᴇs: {str(e)} {FOOTER_TEXT}")


@app.on_message(filters.command(["mute", "tmute"]) & ~filters.private & ~BANNED_USERS)
async def mute_func(_, message: Message):
    if not await is_admin_with_privilege(message, can_restrict_members=True):
        return

    if message.command[0] == "tmute":
        args = message.text.strip().split()
        user_id = None
        time_value = None
        reason_text = None

        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            if len(args) > 1:
                time_value = args[1]
                reason_text = " ".join(args[2:])
        else: 
            potential_user_input_parts = []
            found_user_by_name = None
            start_index_for_time = -1
            
            for i in range(1, len(args)):
                potential_user_input_parts.append(args[i])
                potential_name = " ".join(potential_user_input_parts)
                
                async for member in app.get_chat_members(message.chat.id):
                    if member.user:
                        user_full_name = ((member.user.first_name or "") + " " + (member.user.last_name or "")).strip()
                        if potential_name.lower() == user_full_name.lower() or \
                           potential_name.lower() == (member.user.first_name or "").lower():
                            found_user_by_name = member.user
                            start_index_for_time = i + 1 # The next argument after the name
                            break
                if found_user_by_name:
                    user_id = found_user_by_name.id
                    break
            
            if found_user_by_name:
                if len(args) > start_index_for_time:
                    time_value = args[start_index_for_time]
                    reason_text = " ".join(args[start_index_for_time + 1:])
            else: # If it's not @username, ID, or a recognized name, then it's an invalid format for user
                if len(args) > 1:
                    if args[1].startswith("@") or args[1].isdigit():
                        try:
                            target_user = await app.get_users(args[1])
                            user_id = target_user.id
                            if len(args) > 2:
                                time_value = args[2]
                                reason_text = " ".join(args[3:])
                        except Exception:
                            pass # Let the next check handle if user_id is still None
                    else: # If it's not @username, ID, or a recognized name, then it's an invalid format for user
                        return await message.reply_text(f"Iɴᴠᴀʟɪᴅ Uꜱᴇrɴᴀᴍᴇ/ɪᴅ ᴏʀ ᴜɴʀᴇᴄᴏɢɴɪᴢᴇᴅ ꜰᴏʀᴍᴀᴛ. {FOOTER_TEXT}")

        if not user_id:
            return await message.reply_text(f"ɪ Cᴀɴ'T ғɪɴᴅ ᴛʜᴀᴛ ᴜsᴇr. ᴘʟᴇᴀꜱᴇ ʀᴇᴘly ᴏʀ ᴘʀᴏᴠɪᴅᴇ Uꜱᴇrɴᴀᴍᴇ/ɪᴅ/ɴᴀᴍᴇ. {FOOTER_TEXT}")
        
        if not time_value:
            return await message.reply_text(f"ᴘʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴛɪᴍᴇ ᴀɴᴅ ᴏᴘᴛɪᴏɴᴀʟ ʀᴇᴀꜱᴏɴ ꜰᴏʀ ᴛᴇᴍᴘᴏʀᴀʀʏ ᴍᴜᴛᴇ. ᴇ.g., `/ᴛᴍᴜᴛᴇ 30ᴍ ᴄʜᴀᴛᴛɪɴɢ` {FOOTER_TEXT}")
        
        try:
            temp_mute_unix_timestamp = await time_converter(message, time_value)
            temp_mute_until = datetime.datetime.fromtimestamp(temp_mute_unix_timestamp)
        except ValueError:
            return 

        try:
            user = await app.get_users(user_id)
            mention = user.mention
        except Exception:
             mention = (
                message.reply_to_message.sender_chat.title
                if message.reply_to_message and message.reply_to_message.sender_chat
                else "ᴀɴᴏɴʏᴍᴏᴜꜱ ᴄʜᴀɴɴᴇʟ"
            )
        
        msg = (
            f"**ᴍᴜᴛᴇᴅ Uꜱᴇr:** {mention} 🔇\n"
            f"**ᴍᴜᴛᴇᴅ ʙʏ:** {message.from_user.mention if message.from_user else 'ᴀɴᴏɴʏᴍᴏᴜꜱ'}\n"
            f"**ᴍᴜᴛᴇᴅ ꜰᴏr:** {time_value}\n"
        )
        if reason_text:
            msg += f"**ʀᴇᴀꜱᴏɴ:** {reason_text}"
        msg += FOOTER_TEXT
        
        try:
            await message.chat.restrict_member(user_id, ChatPermissions(), until_date=temp_mute_until)
            await message.reply_text(msg)
        except UserNotParticipant:
            await message.reply_text(f"ᴛʜɪꜱ Uꜱᴇr ɪꜱ ɴᴏᴛ ɪɴ ᴛʜɪꜱ ᴄʜᴀᴛ ᴏʀ Aʟʀᴇᴀᴅʏ ᴍᴜᴛᴇᴅ. {FOOTER_TEXT}")
        except RPCError as e:
            await message.reply_text(f"Fᴀɪʟᴇᴅ Tᴏ ᴛᴇᴍᴘᴏʀᴀʀɪʟʏ ᴍᴜᴛᴇ: {e.MESSAGE} {FOOTER_TEXT}")
        except Exception as e:
            await message.reply_text(f"Fᴀɪʟᴇᴅ Tᴏ ᴛᴇᴍᴘᴏʀᴀʀɪʟʏ ᴍᴜᴛᴇ: {str(e)} {FOOTER_TEXT}")
        return

    # For /mute
    user_id, reason = await extract_user_and_reason_or_title(message, sender_chat=True, index_for_text_start=2)
    if not user_id:
        return await message.reply_text(f"I Cᴀɴ'T Fɪɴd Tʜᴀᴛ Usᴇr. Pʟᴇᴀꜱᴇ Rᴇᴘly Tᴏ A Uꜱᴇr Oʀ Pʀᴏᴠɪᴅᴇ Tʜᴇɪʀ Uꜱᴇrɴᴀᴍᴇ/Iᴅ Oʀ Nᴀᴍᴇ. {FOOTER_TEXT}")
    
    if user_id == app.id:
        return await message.reply_text(f"ɪ Cᴀɴ'T ᴍᴜᴛᴇ ᴍʏꜱᴇʟf. {FOOTER_TEXT}")
    
    if user_id == OWNER_ID or user_id in SUDOERS:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(f"Yᴏᴜ Cᴀɴɴᴏᴛ ᴍᴜᴛᴇ ᴀ Sᴜᴅᴏ Uꜱᴇr ᴏʀ ᴛʜᴇ ᴏᴡɴᴇʀ. {FOOTER_TEXT}")
        elif user_id == message.from_user.id:
             return await message.reply_text(f"Yᴏᴜ Cᴀɴ'T ᴍᴜᴛᴇ YᴏᴜʀꜱᴇLf. {FOOTER_TEXT}")

    try:
        user = await app.get_users(user_id)
        mention = user.mention
    except Exception:
        mention = (
            message.reply_to_message.sender_chat.title
            if message.reply_to_message and message.reply_to_message.sender_chat
            else "ᴀɴᴏɴʏᴍᴏᴜꜱ ᴄʜᴀɴɴᴇʟ"
        )
    
    msg = (
        f"**ᴍᴜᴛᴇᴅ Uꜱᴇr:** {mention} 🔇\n"
        f"**ᴍᴜᴛᴇᴅ ʙʏ:** {message.from_user.mention if message.from_user else 'ᴀɴᴏɴʏᴍᴏᴜꜱ'}\n"
    )
    if reason:
        msg += f"**ʀᴇᴀꜱᴏɴ:** {reason}"
    msg += FOOTER_TEXT
    
    try:
        member = await message.chat.get_member(user_id)
        if member.status == ChatMemberStatus.RESTRICTED:
            return await message.reply_text(f"{mention} ɪꜱ Aʟʀᴇᴀᴅʏ ᴍᴜᴛᴇᴅ. {FOOTER_TEXT}")

        await message.chat.restrict_member(user_id, ChatPermissions())
        await message.reply_text(msg)
    except UserNotParticipant:
        await message.reply_text(f"ᴛʜɪꜱ Uꜱᴇr ɪꜱ ɴᴏᴛ ɪɴ ᴛʜɪꜱ ᴄʜᴀᴛ ᴏʀ Aʟʀᴇᴀᴅʏ ᴍᴜᴛᴇᴅ. {FOOTER_TEXT}")
    except RPCError as e:
        await message.reply_text(f"Fᴀɪʟᴇᴅ Tᴏ ᴍᴜᴛᴇ: {e.MESSAGE} {FOOTER_TEXT}")
    except Exception as e:
        await message.reply_text(f"Fᴀɪʟᴇᴅ Tᴏ ᴍᴜᴛᴇ: {str(e)} {FOOTER_TEXT}")

@app.on_message(filters.command("unmute") & ~filters.private & ~BANNED_USERS)
async def unmute_func(_, message: Message):
    if not await is_admin_with_privilege(message, can_restrict_members=True):
        return

    user_id, _ = await extract_user_and_reason_or_title(message, index_for_text_start=2) 
    if not user_id:
        return await message.reply_text(f"I Cᴀɴ'T Fɪɴd Tʜᴀᴛ Uꜱᴇr. Pʟᴇᴀꜱᴇ Rᴇᴘly Tᴏ A Uꜱᴇr Oʀ Pʀᴏᴠɪᴅᴇ Tʜᴇɪʀ Uꜱᴇrɴᴀᴍᴇ/Iᴅ Oʀ Nᴀᴍᴇ. {FOOTER_TEXT}")
    
    try:
        member = await message.chat.get_member(user_id)
        if member.status != ChatMemberStatus.RESTRICTED:
            return await message.reply_text(f"{member.user.mention} ɪꜱ Aʟʀᴇᴀᴅʏ ᴜɴᴍᴜᴛᴇd. 🎉 {FOOTER_TEXT}")

        # संशोधित लाइन: can_send_stickers, can_send_animations, can_send_games, can_use_inline_bots हटा दिए गए हैं।
        # can_send_media_messages और can_send_other_messages सामान्य मीडिया/अन्य संदेशों को कवर करते हैं।
        await message.chat.restrict_member(user_id, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_polls=True, can_send_other_messages=True, can_add_web_page_previews=True, can_change_info=False, can_invite_users=False, can_pin_messages=False, can_manage_topics=False))
        user = await app.get_users(user_id)
        umention = user.mention
        await message.reply_text(f"Uɴᴍᴜᴛᴇᴅ! {umention} 🎉 {FOOTER_TEXT}")
    except UserNotParticipant:
        await message.reply_text(f"ᴛʜɪꜱ Uꜱᴇr ɪꜱ ɴᴏᴛ ɪɴ ᴛʜɪꜱ ᴄʜᴀᴛ ᴏʀ Aʟʀᴇᴀᴅʏ ᴜɴᴍᴜᴛᴇᴅ. {FOOTER_TEXT}")
    except PeerIdInvalid:
        await message.reply_text(f"Iɴᴠᴀʟɪᴅ Uꜱᴇr ɪᴅ ᴏʀ ɴᴏᴛ ꜰᴏᴜɴᴅ. {FOOTER_TEXT}")
    except RPCError as e:
        await message.reply_text(f"Fᴀɪʟᴇᴅ Tᴏ ᴜɴᴍᴜᴛᴇ: {e.MESSAGE} {FOOTER_TEXT}")
    except Exception as e:
        await message.reply_text(f"Fᴀɪʟᴇᴅ Tᴏ ᴜɴᴍᴜᴛᴇ: {str(e)} {FOOTER_TEXT}")

@app.on_message(filters.command(["warn", "swarn"]) & ~filters.private & ~BANNED_USERS)
async def warn_func(_, message: Message):
    if not await is_admin_with_privilege(message, can_restrict_members=True):
        return
    
    user_id = None
    reason = None
    user_name_for_db = None

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        reason = " ".join(message.command[1:]) if len(message.command) > 1 else None
        user_name_for_db = (message.reply_to_message.from_user.first_name + " " + (message.reply_to_message.from_user.last_name or "")).strip()
    elif len(message.command) > 1:
        user_id, reason = await extract_user_and_reason_or_title(message, index_for_text_start=2)
        if user_id:
            try:
                user = await app.get_users(user_id)
                user_name_for_db = (user.first_name + " " + (user.last_name or "")).strip()
            except Exception:
                user_name_for_db = str(user_id)
        else:
            user_name_for_db = " ".join(message.command[1:2]) # First word after command for name
            reason = " ".join(message.command[2:]) if len(message.command) > 2 else None


    if not user_id and not user_name_for_db:
        return await message.reply_text(f"ɪ Cᴀɴ'T Fɪɴd Tʜᴀᴛ Uꜱᴇr. Pʟᴇᴀꜱᴇ Rᴇᴘly Tᴏ A Uꜱᴇr Oʀ Pʀᴏᴠɪᴅᴇ Tʜᴇɪʀ Uꜱᴇrɴᴀᴍᴇ/Iᴅ Oʀ Nᴀᴍᴇ. {FOOTER_TEXT}")

    if user_id == app.id:
        return await message.reply_text(f"ɪ Cᴀɴ'T ᴡᴀʀɴ ᴍʏꜱᴇLf. {FOOTER_TEXT}")
    
    if user_id == OWNER_ID or user_id in SUDOERS:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(f"Yᴏᴜ Cᴀɴɴᴏᴛ ᴡᴀʀɴ ᴀ Sᴜᴅᴏ Uꜱᴇr ᴏʀ ᴛʜᴇ ᴏᴡɴᴇr. {FOOTER_TEXT}")
        elif user_id == message.from_user.id:
             return await message.reply_text(f"Yᴏᴜ Cᴀɴ'T ᴡᴀʀɴ YᴏᴜʀꜱᴇLf. {FOOTER_TEXT}")

    if message.command[0] == "swarn" and message.reply_to_message:
        await message.reply_to_message.delete()
    
    if not user_name_for_db and user_id:
        try:
            user = await app.get_users(user_id)
            user_name_for_db = (user.first_name + " " + (user.last_name or "")).strip()
        except Exception:
            user_name_for_db = str(user_id)

    if not user_name_for_db:
        return await message.reply_text(f"ᴜɴᴀʙʟᴇ Tᴏ ɪᴅᴇɴᴛɪғʏ Uꜱᴇr ᴛᴏ ᴡᴀʀɴ. {FOOTER_TEXT}")

    warn_data = await get_warn(message.chat.id, user_name_for_db)
    if warn_data:
        current_warns = warn_data.get("warns", 0) + 1
    else:
        current_warns = 1
    
    warn_info = {"warns": current_warns, "reason": reason or "Nᴏ Rᴇᴀsᴏɴ Pʀᴏᴠɪᴅᴇᴅ"}
    await add_warn(message.chat.id, user_name_for_db, warn_info)

    try:
        mention = (await app.get_users(user_id)).mention if user_id else user_name_for_db
    except Exception:
        mention = user_name_for_db
    
    await message.reply_text(
        f"**ᴡᴀʀɴᴇᴅ Uꜱᴇr:** {mention}\n"
        f"**ᴡᴀʀɴs:** {current_warns}\n"
        f"**ʀᴇᴀꜱᴏɴ:** {reason or 'Nᴏ Rᴇᴀsᴏɴ Pʀᴏᴠɪᴅᴇᴅ'} {FOOTER_TEXT}"
    )


@app.on_message(filters.command("rmwarns") & ~filters.private & ~BANNED_USERS)
async def rmwarns_func(_, message: Message):
    if not await is_admin_with_privilege(message, can_restrict_members=True):
        return
    
    user_id = None
    user_name_for_db = None

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        user_name_for_db = (message.reply_to_message.from_user.first_name + " " + (message.reply_to_message.from_user.last_name or "")).strip()
    elif len(message.command) > 1:
        user_id, _ = await extract_user_and_reason_or_title(message, index_for_text_start=2)
        if user_id:
            try:
                user = await app.get_users(user_id)
                user_name_for_db = (user.first_name + " " + (user.last_name or "")).strip()
            except Exception:
                user_name_for_db = str(user_id)
        else:
            user_name_for_db = " ".join(message.command[1:])


    if not user_id and not user_name_for_db:
        return await message.reply_text(f"ɪ Cᴀɴ'T Fɪɴd Tʜᴀᴛ Uꜱᴇr. Pʟᴇᴀꜱᴇ Rᴇᴘly Tᴏ A Uꜱᴇr Oʀ Pʀᴏᴠɪᴅᴇ Tʜᴇɪʀ Uꜱᴇrɴᴀᴍᴇ/Iᴅ Oʀ Nᴀᴍᴇ. {FOOTER_TEXT}")

    if not user_name_for_db:
        return await message.reply_text(f"ᴜɴᴀʙʟᴇ Tᴏ ɪᴅᴇɴᴛɪғʏ Uꜱᴇr ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴡᴀʀɴs. {FOOTER_TEXT}")

    if await remove_warns(message.chat.id, user_name_for_db):
        try:
            mention = (await app.get_users(user_id)).mention if user_id else user_name_for_db
        except Exception:
            mention = user_name_for_db
        await message.reply_text(f"ᴀʟʟ ᴡᴀʀɴɪɴɢs ʀᴇᴍᴏᴠᴇᴅ ꜰᴏr {mention}. ✅ {FOOTER_TEXT}")
    else:
        try:
            mention = (await app.get_users(user_id)).mention if user_id else user_name_for_db
        except Exception:
            mention = user_name_for_db
        await message.reply_text(f"{mention} ʜᴀꜱ ɴᴏ ᴡᴀʀɴɪɴɢs. ✅ {FOOTER_TEXT}")


@app.on_message(filters.command("warns") & ~filters.private & ~BANNED_USERS)
async def warns_func(_, message: Message):
    if not await is_admin_with_privilege(message):
        return

    user_id = None
    user_name_for_db = None

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        user_name_for_db = (message.reply_to_message.from_user.first_name + " " + (message.reply_to_message.from_user.last_name or "")).strip()
    elif len(message.command) > 1:
        user_id, _ = await extract_user_and_reason_or_title(message, index_for_text_start=2)
        if user_id:
            try:
                user = await app.get_users(user_id)
                user_name_for_db = (user.first_name + " " + (user.last_name or "")).strip()
            except Exception:
                user_name_for_db = str(user_id)
        else:
            user_name_for_db = " ".join(message.command[1:])


    if not user_id and not user_name_for_db:
        return await message.reply_text(f"ɪ Cᴀɴ'T Fɪɴd Tʜᴀᴛ Uꜱᴇr. Pʟᴇᴀꜱᴇ Rᴇᴘly Tᴏ A Uꜱᴇr Oʀ Pʀᴏᴠɪᴅᴇ Tʜᴇɪʀ Uꜱᴇrɴᴀᴍᴇ/Iᴅ Oʀ Nᴀᴍᴇ. {FOOTER_TEXT}")

    if not user_name_for_db:
        return await message.reply_text(f"ᴜɴᴀʙʟᴇ Tᴏ ɪᴅᴇɴᴛɪғʏ Uꜱᴇr ᴛᴏ ꜱʜᴏᴡ ᴡᴀʀɴs. {FOOTER_TEXT}")

    try:
        mention = (await app.get_users(user_id)).mention if user_id else user_name_for_db
    except Exception:
        mention = (
            message.reply_to_message.sender_chat.title
            if message.reply_to_message and message.reply_to_message.sender_chat
            else "ᴀɴᴏɴʏᴍᴏᴜꜱ ᴄʜᴀɴɴᴇʟ"
        )
        user_name_for_db = (message.reply_to_message.sender_chat.title if message.reply_to_message and message.reply_to_message.sender_chat else str(user_id)) if message.reply_to_message else str(user_id)

    warn_data = await get_warn(message.chat.id, user_name_for_db)
    current_warns = warn_data.get("warns", 0) if warn_data else 0
    warn_reason = warn_data.get("reason", "N/A") if warn_data else "N/A"

    if current_warns > 0:
        await message.reply_text(
            f"**{mention} ʜᴀꜱ {current_warns} Wᴀʀɴɪɴɢꜱ.**\n"
            f"**ʟᴀꜱᴛ ʀᴇᴀꜱᴏɴ:** {warn_reason} {FOOTER_TEXT}"
        )
    else:
        await message.reply_text(f"{mention} ʜᴀꜱ ɴᴏ Wᴀʀɴɪɴɢꜱ. ✅ {FOOTER_TEXT}")


@app.on_message(filters.command("link") & ~BANNED_USERS)
async def invite(_, message):
    if not await is_admin_with_privilege(message, can_invite_users=True):
        return
        
    if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        link = (await app.get_chat(message.chat.id)).invite_link
        if not link:
            link = await app.export_chat_invite_link(message.chat.id)
        # --- START: /link command formatting update ---
        await message.reply_text(
            f"ʜᴇʀᴇ's ᴛʜᴇ ɢʀᴏᴜᴘ ɪɴᴠɪᴛᴇ ʟɪɴᴋ 🔗\n\n" # Moved to new line, added emoji
            f"{link}\n" # Link on new line
            f"{FOOTER_TEXT}" # Added footer on a new line
        )
        # --- END: /link command formatting update ---
    else:
        await message.reply_text(f"ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴄᴀɴ ᴏɴʟʏ ʙᴇ ᴜꜱᴇᴅ ɪɴ ɢʀᴏᴜᴘꜱ ᴀɴᴅ ꜱᴜᴘᴇʀɢʀᴏᴜᴘꜱ. {FOOTER_TEXT}") # Added footer

@app.on_message(filters.command("zombies") & ~filters.private & ~BANNED_USERS)
async def zombies_func(_, message: Message):
    if not await is_admin_with_privilege(message, can_restrict_members=True):
        return

    deleted_accounts = []
    async for member in app.get_chat_members(message.chat.id, filter=ChatMembersFilter.DELETED):
        if member.user.is_deleted:
            deleted_accounts.append(member.user.id)

    if not deleted_accounts:
        return await message.reply_text(f"ɴᴏ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴts (ᴢᴏᴍʙɪᴇs) ғᴏᴜɴᴅ ɪɴ ᴛʜɪs ᴄʜᴀᴛ. 🎉 {FOOTER_TEXT}")

    banned_count = 0
    for user_id in deleted_accounts:
        with suppress(RPCError):
            await message.chat.ban_member(user_id)
            banned_count += 1
            await asyncio.sleep(0.1) # Small delay to avoid flood waits

    await message.reply_text(
        f"Sᴜᴄᴄᴇssғᴜʟʟʏ ʙᴀɴɴᴇᴅ {banned_count} ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴts (ᴢᴏᴍʙɪᴇs). 🔨 {FOOTER_TEXT}"
    )

@app.on_message(filters.command(["report", "@admins", "@admin"]) & ~filters.private & ~BANNED_USERS)
async def report_func(_, message: Message):
    if not message.reply_to_message:
        return await message.reply_text(f"ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ Tᴏ ᴀ ᴍᴇssᴀɢᴇ Tᴏ ʀᴇᴘᴏrᴛ ɪᴛ. {FOOTER_TEXT}")

    admin_mentions = []
    async for member in app.get_chat_members(message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS):
        if member.user and member.user.id != message.from_user.id and member.user.id != app.id:
            admin_mentions.append(member.user.mention)
    
    if not admin_mentions:
        return await message.reply_text(f"ɴᴏ ᴀᴅᴍɪɴs ғᴏᴜɴᴅ ɪɴ ᴛʜɪs ᴄʜᴀᴛ ᴛᴏ ʀᴇᴘᴏrᴛ ᴛᴏ. {FOOTER_TEXT}")

    report_reason = " ".join(message.command[1:]) if len(message.command) > 1 else "ɴᴏ ʀᴇᴀsᴏɴ ᴘrᴏᴠɪᴅᴇᴅ"
    
    report_message = (
        f"**Rᴇᴘᴏrᴛ:** {message.reply_to_message.link}\n"
        f"**Rᴇᴘᴏrᴛᴇᴅ Bʏ:** {message.from_user.mention}\n"
        f"**Rᴇᴀsᴏɴ:** {report_reason}\n\n"
        f"**Aᴅᴍɪɴs:** {' '.join(admin_mentions)} {FOOTER_TEXT}"
    )

    await message.reply_to_message.reply_text(report_message)
    await message.delete()
