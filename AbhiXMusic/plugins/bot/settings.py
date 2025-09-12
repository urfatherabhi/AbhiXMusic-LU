from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.errors import MessageNotModified
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    InputMediaPhoto,
    InputMediaVideo,
)
import logging

from AbhiXMusic import app
from AbhiXMusic.utils.database import (
    add_nonadmin_chat,
    get_authuser,
    get_authuser_names,
    get_playmode,
    get_playtype,
    get_upvote_count,
    is_nonadmin_chat,
    is_skipmode,
    remove_nonadmin_chat,
    set_playmode,
    set_playtype,
    set_upvotes,
    skip_off,
    skip_on,
)
from AbhiXMusic.utils.decorators.admins import ActualAdminCB
from AbhiXMusic.utils.decorators.language import language, languageCB
from AbhiXMusic.utils.inline.settings import (
    auth_users_markup,
    playmode_users_markup,
    setting_markup,
    vote_mode_markup,
)
from AbhiXMusic.utils.inline.start import private_panel
from config import BANNED_USERS, OWNER_ID, MUSIC_BOT_NAME, START_IMG_URL

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_message(
    filters.command(["settings", "setting"]) & filters.group & ~BANNED_USERS
)
@language
async def settings_mar(client, message: Message, _):
    buttons = setting_markup(_)
    await message.reply_text(
        _["setting_1"].format(app.mention, message.chat.id, message.chat.title),
        reply_markup=InlineKeyboardMarkup(buttons),
    )

@app.on_callback_query(filters.regex("gib_source") & ~BANNED_USERS)
@languageCB
async def gib_repo(client, CallbackQuery, _):
    current_media = getattr(CallbackQuery.message, 'video', None)
    new_media = "https://graph.org/file/84d30d4fd04570c0e0256.mp4"
    if current_media and current_media.file_id == new_media:
        return

    await CallbackQuery.edit_message_media(
        InputMediaVideo(new_media),
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="ʙᴀᴄᴋ", callback_data=f"settingsback_helper")]]
        ),
    )

@app.on_callback_query(
    filters.regex("settings_helper") & ~BANNED_USERS
)
@languageCB
async def settings_cb(client, CallbackQuery, _):
    try:
        await CallbackQuery.answer(_["set_cb_5"])
    except:
        pass
    buttons = setting_markup(_)
    return await CallbackQuery.edit_message_text(
        _["setting_1"].format(
            CallbackQuery.message.chat.title,
            CallbackQuery.message.chat.id,
        ),
        reply_markup=InlineKeyboardMarkup(buttons),
    )


@app.on_callback_query(filters.regex("settingsback_helper") & ~BANNED_USERS)
@languageCB
async def settings_back_markup(client, CallbackQuery: CallbackQuery, _):
    try:
        await CallbackQuery.answer()
    except:
        pass
    if CallbackQuery.message.chat.type == ChatType.PRIVATE:
        is_owner = False
        try:
            user = await app.resolve_peer(OWNER_ID)
            if user.user_id == CallbackQuery.from_user.id:
                is_owner = True
                logger.info(f"User {CallbackQuery.from_user.id} is the owner (OWNER_ID: {OWNER_ID})")
            else:
                logger.info(f"User {CallbackQuery.from_user.id} is NOT the owner (OWNER_ID: {OWNER_ID})")
        except Exception as e:
            logger.error(f"Error resolving OWNER_ID {OWNER_ID}: {str(e)}")
            pass

        buttons = private_panel(_)
        # Custom Owner button with stylish text
        buttons.append([InlineKeyboardButton(text="🥀 Dᴏɴᴛ Cʟɪᴄᴋ Hᴇʀᴇ 🥀", callback_data="owner_redirect")])
        
        current_media = getattr(CallbackQuery.message, 'photo', None)
        current_caption = CallbackQuery.message.caption or ""
        new_caption = _["start_2"].format(CallbackQuery.from_user.first_name, app.mention) + "\n\n⚡ Bᴀʙʏ... Fᴀᴛʜᴇʀ⚡\n✨ Hᴀꜱ Aʟʀᴇᴀᴅʏ  ✨\n🔥 Aʀʀɪᴠᴇᴅ... 🔥"

        if (current_media and current_media.file_id == START_IMG_URL) and (current_caption == new_caption):
            try:
                return await CallbackQuery.edit_message_reply_markup(
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
            except MessageNotModified:
                return

        return await CallbackQuery.edit_message_media(
            InputMediaPhoto(
                media=START_IMG_URL,
                caption=new_caption,
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    else:
        buttons = setting_markup(_)
        try:
            return await CallbackQuery.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except MessageNotModified:
            return

@app.on_callback_query(filters.regex("owner_redirect") & ~BANNED_USERS)
@languageCB
async def owner_redirect(client, CallbackQuery: CallbackQuery, _):
    try:
        await CallbackQuery.answer()
    except Exception as e:
        logger.error(f"Error answering callback query: {str(e)}")
        return

    owner_link = "tg://resolve?domain=URFather_ABHI"
    try:
        await CallbackQuery.edit_message_text(
            f"||Sᴀʏ Pᴀᴘᴀ Tᴏ Oᴡɴᴇʀ||\n👉 [ Pᴀᴘᴀ Jɪ  😎]({owner_link})",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="🥀 Pᴀᴘᴀ Jɪ 🥀 ", url=owner_link),
                        InlineKeyboardButton(text="🔙 Back", callback_data="settingsback_helper"),
                    ]
                ]
            ),
            disable_web_page_preview=False,
        )
        logger.info(f"Redirecting user {CallbackQuery.from_user.id} to owner link: {owner_link}")
    except Exception as e:
        logger.error(f"Error redirecting to owner link {owner_link}: {str(e)}")
        await CallbackQuery.edit_message_text(
            f"❌ Could not redirect to the owner. Please contact them manually at @URFather_ABHI 💬",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="🔙 Back", callback_data="settingsback_helper"),
                    ]
                ]
            ),
        )


@app.on_callback_query(
    filters.regex(
        pattern=r"^(SEARCHANSWER|PLAYMODEANSWER|PLAYTYPEANSWER|AUTHANSWER|ANSWERVOMODE|VOTEANSWER|PM|AU|VM)$"
    )
    & ~BANNED_USERS
)
@languageCB
async def without_Admin_rights(client, CallbackQuery, _):
    command = CallbackQuery.matches[0].group(1)
    if command == "SEARCHANSWER":
        try:
            return await CallbackQuery.answer(_["setting_2"], show_alert=True)
        except:
            return
    if command == "PLAYMODEANSWER":
        try:
            return await CallbackQuery.answer(_["setting_5"], show_alert=True)
        except:
            return
    if command == "PLAYTYPEANSWER":
        try:
            return await CallbackQuery.answer(_["setting_6"], show_alert=True)
        except:
            return
    if command == "AUTHANSWER":
        try:
            return await CallbackQuery.answer(_["setting_3"], show_alert=True)
        except:
            return
    if command == "VOTEANSWER":
        try:
            return await CallbackQuery.answer(
                _["setting_8"],
                show_alert=True,
            )
        except:
            return
    if command == "ANSWERVOMODE":
        current = await get_upvote_count(CallbackQuery.message.chat.id)
        try:
            return await CallbackQuery.answer(
                _["setting_9"].format(current),
                show_alert=True,
            )
        except:
            return
    if command == "PM":
        try:
            await CallbackQuery.answer(_["set_cb_2"], show_alert=True)
        except:
            pass
        playmode = await get_playmode(CallbackQuery.message.chat.id)
        if playmode == "Direct":
            Direct = True
        else:
            Direct = None
        is_non_admin = await is_nonadmin_chat(CallbackQuery.message.chat.id)
        if not is_non_admin:
            Group = True
        else:
            Group = None
        playty = await get_playtype(CallbackQuery.message.chat.id)
        if playty == "Everyone":
            Playtype = None
        else:
            Playtype = True
        buttons = playmode_users_markup(_, Direct, Group, Playtype)
    if command == "AU":
        try:
            await CallbackQuery.answer(_["set_cb_1"], show_alert=True)
        except:
            pass
        is_non_admin = await is_nonadmin_chat(CallbackQuery.message.chat.id)
        if not is_non_admin:
            buttons = auth_users_markup(_, True)
        else:
            buttons = auth_users_markup(_)
    if command == "VM":
        mode = await is_skipmode(CallbackQuery.message.chat.id)
        current = await get_upvote_count(CallbackQuery.message.chat.id)
        buttons = vote_mode_markup(_, current, mode)
    try:
        return await CallbackQuery.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except MessageNotModified:
        return


@app.on_callback_query(filters.regex("FERRARIUDTI") & ~BANNED_USERS)
@ActualAdminCB
async def addition(client, CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    mode = callback_data.split(None, 1)[1]
    if not await is_skipmode(CallbackQuery.message.chat.id):
        return await CallbackQuery.answer(_["setting_10"], show_alert=True)
    current = await get_upvote_count(CallbackQuery.message.chat.id)
    if mode == "M":
        final = current - 2
        print(final)
        if final == 0:
            return await CallbackQuery.answer(
                _["setting_11"],
                show_alert=True,
            )
        if final <= 2:
            final = 2
        await set_upvotes(CallbackQuery.message.chat.id, final)
    else:
        final = current + 2
        print(final)
        if final == 17:
            return await CallbackQuery.answer(
                _["setting_12"],
                show_alert=True,
            )
        if final >= 15:
            final = 15
        await set_upvotes(CallbackQuery.message.chat.id, final)
    buttons = vote_mode_markup(_, final, True)
    try:
        return await CallbackQuery.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except MessageNotModified:
        return


@app.on_callback_query(
    filters.regex(pattern=r"^(MODECHANGE|CHANNELMODECHANGE|PLAYTYPECHANGE)$")
    & ~BANNED_USERS
)
@ActualAdminCB
async def playmode_ans(client, CallbackQuery, _):
    command = CallbackQuery.matches[0].group(1)
    if command == "CHANNELMODECHANGE":
        is_non_admin = await is_nonadmin_chat(CallbackQuery.message.chat.id)
        if not is_non_admin:
            await add_nonadmin_chat(CallbackQuery.message.chat.id)
            Group = None
        else:
            await remove_nonadmin_chat(CallbackQuery.message.chat.id)
            Group = True
        playmode = await get_playmode(CallbackQuery.message.chat.id)
        if playmode == "Direct":
            Direct = True
        else:
            Direct = None
        playty = await get_playtype(CallbackQuery.message.chat.id)
        if playty == "Everyone":
            Playtype = None
        else:
            Playtype = True
        buttons = playmode_users_markup(_, Direct, Group, Playtype)
    if command == "MODECHANGE":
        try:
            await CallbackQuery.answer(_["set_cb_3"], show_alert=True)
        except:
            pass
        playmode = await get_playmode(CallbackQuery.message.chat.id)
        if playmode == "Direct":
            await set_playmode(CallbackQuery.message.chat.id, "Inline")
            Direct = None
        else:
            await set_playmode(CallbackQuery.message.chat.id, "Direct")
            Direct = True
        is_non_admin = await is_nonadmin_chat(CallbackQuery.message.chat.id)
        if not is_non_admin:
            Group = True
        else:
            Group = None
        playty = await get_playtype(CallbackQuery.message.chat.id)
        if playty == "Everyone":
            Playtype = False
        else:
            Playtype = True
        buttons = playmode_users_markup(_, Direct, Group, Playtype)
    if command == "PLAYTYPECHANGE":
        try:
            await CallbackQuery.answer(_["set_cb_3"], show_alert=True)
        except:
            pass
        playty = await get_playtype(CallbackQuery.message.chat.id)
        if playty == "Everyone":
            await set_playtype(CallbackQuery.message.chat.id, "Admin")
            Playtype = False
        else:
            await set_playtype(CallbackQuery.message.chat.id, "Everyone")
            Playtype = True
        playmode = await get_playmode(CallbackQuery.message.chat.id)
        if playmode == "Direct":
            Direct = True
        else:
            Direct = None
        is_non_admin = await is_nonadmin_chat(CallbackQuery.message.chat.id)
        if not is_non_admin:
            Group = True
        else:
            Group = None
        buttons = playmode_users_markup(_, Direct, Group, Playtype)
    try:
        return await CallbackQuery.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except MessageNotModified:
        return


@app.on_callback_query(filters.regex(pattern=r"^(AUTH|AUTHLIST)$") & ~BANNED_USERS)
@ActualAdminCB
async def authusers_mar(client, CallbackQuery, _):
    command = CallbackQuery.matches[0].group(1)
    if command == "AUTHLIST":
        _authusers = await get_authuser_names(CallbackQuery.message.chat.id)
        if not _authusers:
            try:
                return await CallbackQuery.answer(_["setting_4"], show_alert=True)
            except:
                return
        else:
            try:
                await CallbackQuery.answer(_["set_cb_4"], show_alert=True)
            except:
                pass
            j = 0
            await CallbackQuery.edit_message_text(_["auth_6"])
            msg = _["auth_7"].format(CallbackQuery.message.chat.title)
            for note in _authusers:
                _note = await get_authuser(CallbackQuery.message.chat.id, note)
                user_id = _note["auth_user_id"]
                admin_id = _note["admin_id"]
                admin_name = _note["admin_name"]
                try:
                    user = await app.get_users(user_id)
                    user = user.first_name
                    j += 1
                except:
                    continue
                msg += f"{j}➤ {user}[<code>{user_id}</code>]\n"
                msg += f"   {_['auth_8']} {admin_name}[<code>{admin_id}</code>]\n\n"
            upl = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text=_["BACK_BUTTON"], callback_data=f"AU"
                        ),
                        InlineKeyboardButton(
                            text=_["CLOSE_BUTTON"],
                            callback_data=f"close",
                        ),
                    ]
                ]
            )
            try:
                return await CallbackQuery.edit_message_text(msg, reply_markup=upl)
            except MessageNotModified:
                return
    try:
        await CallbackQuery.answer(_["set_cb_3"], show_alert=True)
    except:
        pass
    if command == "AUTH":
        is_non_admin = await is_nonadmin_chat(CallbackQuery.message.chat.id)
        if not is_non_admin:
            await add_nonadmin_chat(CallbackQuery.message.chat.id)
            buttons = auth_users_markup(_)
        else:
            await remove_nonadmin_chat(CallbackQuery.message.chat.id)
            buttons = auth_users_markup(_, True)
    try:
        return await CallbackQuery.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except MessageNotModified:
        return


@app.on_callback_query(filters.regex("VOMODECHANGE") & ~BANNED_USERS)
@ActualAdminCB
async def vote_change(client, CallbackQuery, _):
    command = CallbackQuery.matches[0].group(1)
    try:
        await CallbackQuery.answer(_["set_cb_3"], show_alert=True)
    except:
        pass
    mod = None
    if await is_skipmode(CallbackQuery.message.chat.id):
        await skip_off(CallbackQuery.message.chat.id)
    else:
        mod = True
        await skip_on(CallbackQuery.message.chat.id)
    current = await get_upvote_count(CallbackQuery.message.chat.id)
    buttons = vote_mode_markup(_, current, mod)

    try:
        return await CallbackQuery.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except MessageNotModified:
        return
