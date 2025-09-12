import google.generativeai as genai
import asyncio
import os
from dotenv import load_dotenv
from pyrogram import filters, enums
from pyrogram.enums import ChatAction
from pyrogram.types import Message
from AbhiXMusic import app

# --- Start of GEMINI_API_KEY loading logic ---
GEMINI_API_KEY = None
try:
    from AbhiXMusic.config import GEMINI_API_KEY as Configured_GEMINI_API_KEY
    if Configured_GEMINI_API_KEY:
        GEMINI_API_KEY = Configured_GEMINI_API_KEY
        print("DEBUG: Gemini.py: GEMINI_API_KEY loaded from AbhiXMusic.config.")
    else:
        print("DEBUG: Gemini.py: GEMINI_API_KEY in config.py was None or empty.")
except ImportError:
    print("DEBUG: Gemini.py: Could not import GEMINI_API_KEY from AbhiXMusic.config.")

# Fallback: if not loaded from config.py, try loading directly from .env
if GEMINI_API_KEY is None:
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        print("DEBUG: Gemini.py: GEMINI_API_KEY loaded directly from .env fallback.")
    else:
        print("DEBUG: Gemini.py: GEMINI_API_KEY still not found after direct .env load.")
# --- End of GEMINI_API_KEY loading logic ---


# Configure Gemini API
gemini_model = None
TARGET_GEMINI_MODEL = 'gemini-1.5-flash' 

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel(TARGET_GEMINI_MODEL)
        print(f"DEBUG: Real Bot: '{TARGET_GEMINI_MODEL}' model successfully initialized. ✅")
    except Exception as e:
        print(f"❌ Real Bot: Error configuring Gemini API or listing models: {e}")
        gemini_model = None
else:
    print("⚠️ Real Bot: GEMINI_API_KEY is not set. Gemini features will be disabled.")


# New commands: /ask and /abhi, also supporting !ask and !abhi
@app.on_message(filters.command(["ask", "abhi"], prefixes=["/", "!"]))
async def gemini_handler(client, message: Message):
    if not gemini_model:
        await message.reply_text(
            "Sorry, Gemini AI is not available at the moment. Please contact the bot admin. "
            "Ensure `GEMINI_API_KEY` is configured correctly.",
            quote=True
        )
        return

    await app.send_chat_action(message.chat.id, ChatAction.TYPING)

    user_input = ""
    if len(message.command) > 1:
        user_input = " ".join(message.command[1:])
    elif message.reply_to_message and message.reply_to_message.text:
        user_input = message.reply_to_message.text
    else:
        await message.reply_text("Example: `/ask Who Is @URFather_ABHI is AI?` or `!abhi What is the capital of India?`", quote=True)
        return

    if not user_input.strip():
        await message.reply_text("Please provide something to ask Gemini.", quote=True)
        return

    try:
        response = await asyncio.to_thread(gemini_model.generate_content, user_input)
        
        if response and hasattr(response, 'text') and response.text:
            # ONLY the username is a spoiler
            response_text = f"💡Fʀᴏᴍ: ||@URFather_ABHI||\n\n" \
                            f"{response.text}" # Gemini's actual response
            
            # Use MARKDOWN because of the spoiler tags
            await message.reply_text(response_text, quote=True, parse_mode=enums.ParseMode.MARKDOWN)
        else:
            await message.reply_text("Sorry! No meaningful response received from Gemini. Please try again.", quote=True)

    except Exception as e:
        print(f"❌ Error generating content from Gemini: {e}")
        await message.reply_text(
            f"Sorry, an error occurred while getting a response from Gemini: `{e}`\n"
            "Perhaps Gemini's rate limit has been reached or there's another server-side issue. "
            "Please try again after some time."
        )

__MODULE__ = "Gᴇᴍɪɴɪ"
__HELP__ = """
/ask [query] - Ask Gemini AI a question.
!ask [query] - Ask Gemini AI a question.
/abhi [query] - Ask Gemini AI a question.
!abhi [query] - Ask Gemini AI a question.
(All commands perform the same function)

You can also reply to a message with `/ask`, `!ask`, `/abhi`, or `!abhi` to ask Gemini AI a question based on that message.
"""
