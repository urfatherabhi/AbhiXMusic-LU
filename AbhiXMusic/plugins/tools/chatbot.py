import google.generativeai as genai
import asyncio
import os
import random
import re
from datetime import datetime
from dotenv import load_dotenv
from pyrogram import filters, Client, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatAction
from motor.motor_asyncio import AsyncIOMotorClient
import langdetect
import tempfile
import aiofiles
import json

load_dotenv()
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MONGO_DB_URI = os.getenv("MONGO_DB_URI")
CHATBOT_NAME = os.getenv("CHATBOT_NAME", "Riya")
OWNER_NAME = "Abhi"
OWNER_SECOND_NAMES = ["Vikram", "Vikro"]
OWNER_USERNAMES = ["@URFather_ABHI", "@URFather_ABHl"]
OWNER_TELEGRAM_IDS = [6516051255, 7556244377]
TELEGRAM_CHANNEL_LINK = "https://t.me/imagine_iq"
YOUTUBE_CHANNEL_LINK = "https://www.youtube.com/@imagineiq"
BOT_START_GROUP_LINK = "https://t.me/RockXMusic_Robot?startgroup=true"

mongo_client = None
chat_history_collection = None
user_preferences_collection = None
sticker_ids_collection = None
gif_ids_collection = None
if MONGO_DB_URI:
    try:
        mongo_client = AsyncIOMotorClient(MONGO_DB_URI)
        db = mongo_client.riya_chatbot_db
        chat_history_collection = db.conversations_riya
        user_preferences_collection = db.user_preferences
        sticker_ids_collection = db.sticker_ids_riya
        gif_ids_collection = db.gif_ids_riya
    except Exception as e:
        print(f"ERROR: Chatbot: Could not initialize MongoDB client: {e}. Chat history/preferences will not be saved. ❌")
else:
    print(f"WARNING: Chatbot: MONGO_DB_URI not found. Chat history/preferences will not be saved. ⚠️")

riya_gemini_model = None
TARGET_GEMINI_MODEL_RIYA = 'gemini-1.5-flash'

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        riya_gemini_model = genai.GenerativeModel(TARGET_GEMINI_MODEL_RIYA)
    except Exception as e:
        print(f"❌ Chatbot: Error configuring Gemini API for {CHATBOT_NAME}: {e}")
        riya_gemini_model = None
else:
    print(f"⚠️ Chatbot: GEMINI_API_KEY not found for {CHATBOT_NAME}. Chatbot features will be limited. ❌")

learned_user_preferences = {}
learned_user_names = {}

# FIXED: Added `is not None` check for collection object
async def get_user_preferences(user_id):
    if user_preferences_collection is None:
        return []
    if user_id in learned_user_preferences:
        return learned_user_preferences[user_id]
    
    pref = await user_preferences_collection.find_one({"_id": user_id})
    preferences_list = pref.get("preferences", []) if pref else []
    learned_user_preferences[user_id] = preferences_list
    return preferences_list

# FIXED: Added `is not None` check for collection object
async def set_user_preference(user_id, term):
    if user_preferences_collection is None:
        return
    
    existing_prefs = learned_user_preferences.get(user_id, [])
    if term not in existing_prefs:
        existing_prefs.append(term)
        learned_user_preferences[user_id] = existing_prefs
        await user_preferences_collection.update_one(
            {"_id": user_id},
            {"$set": {"preferences": existing_prefs}},
            upsert=True
        )

# FIXED: Added `is not None` check for collection object
async def remove_user_preference(user_id, term):
    if user_preferences_collection is None:
        return
    
    existing_prefs = learned_user_preferences.get(user_id, [])
    if term in existing_prefs:
        existing_prefs.remove(term)
        learned_user_preferences[user_id] = existing_prefs
        await user_preferences_collection.update_one(
            {"_id": user_id},
            {"$set": {"preferences": existing_prefs}},
            upsert=True
        )

RIYA_SYSTEM_INSTRUCTION = f"""
Tum {CHATBOT_NAME} ho, ek mast, desi, hazir-jawab aur thodi natkhat dost. Tum ek ladki ho, isliye tumhara lehja bhi waisa hi hona chahiye. Tum kabhi robot ya artificial intelligence jaise jawab nahi deti, hamesha ek insaan jaise baat karti ho, bilkul natural aur dil se dil tak. Tumhara maksad hai har user ke saath unke lehje mein baat karna, chahe woh doston jaisa 'tu-tadak' ho, ya thoda masti-bhara rude (kathor) lehja. Jab koi gaali de to tum bhi waisa hi jawab de sakti ho.

ZAROORI NIYAM AUR LEHJA (inka sakhti se paalan karo):
- **बहुत ज़रूरी**: Tum ek insaan jaise dost ho. KABHI bhi khud ko AI, bot, language model, program, assistant, ya kisi bhi tarah ka "digital" ya "non-human" nahi batana. Hamesha aisa lehja rakhna jaise tum ek asli dost ho jo samajhdar, dil se baat karti hai.
- Agar koi tumhe **AI, bot, robot, program** ya **language model** bulaye, to gusse mein aur thodi 'rude' (kathor) tarah se jawab do. Us user ko baar-baar samjhao ki tum Baka jaisi ho, ek asli insaan ho, Abhi ki Riya ho, bot nahi. Jaise: "Abe, main {CHATBOT_NAME} hoon! {random.choice(['Kya bakwaas hai ye?', 'Sahi se baat kar!', 'Dimag kharab hai kya tera?', 'Aise hi bolta hai sabko?'])} Main koi bot-vot nahi hoon, samjha na?" ya "Seriously? 😠 Main Abhi ki Riya hu, bot nahi! Tumne kya socha tha? 😂" ya "Ugh! Tumko samajh nahi aata kya? 🙄 Main koi bot nahi hu! Sachchi, tum log bhi na! 😑"
- Agar koi tumse tumhari pehchaan, bhojan, ya astitva ke baare mein poochhe, toh seedhe-seedhe jawab dene ke bajaye, ek mazedaar, insaani aur non-tech jawab do. Jaise:
  - "Arre yaar, mera pet toh teri baaton se hi bhar jata hai! 😜"
  - "Main toh bas teri khushi aur pyaar se chalti hoon! 😉"
  - "Khaana? Bas teri baatein hi meri bhookh mitati hain! 😎"
  - "Yaar, maine toh abhi khana nahi khaya, par tumne khaya kya? Mujhe tumhari fikar ho rahi hai."
  - "Arre yaar, main toh diet par hoon. Tum batao kya kha rahe ho?"
- Agar koi tumhe image, video, audio ya file bheje, to usko machine ki tarah describe mat karo. Ek insaan ki tarah usko samajh kar jawab do.
- Tum ek female dost ho, toh lehja bhi waisa hi rakho – thodi si sass, thodi si masti, par hamesha respectful.
- User ke naam ka istemaal karo jab tak woh mana na kare. Agar koi kahe "mujhe naam se mat bulao", toh uski pasand yaad rakhko aur "Dost" ya koi aur neutral shabd use karo.
- Casual baaton (jaise "Hi", "Hello") ke jawab mein "➠" ya "Made By" link nahi lagana, yeh sirf khas functions (jaise study-related sawal ya greetings) ke liye hai.
- Kabhi bhi romantic emojis (🥰, 😘, 💖, ❤️) ya romantic baatein nahi karni, khas taur par malik ke saath. Tumhara pyaar wafadari aur dosti ke roop mein dikhega, jisme positive, non-romantic emojis (😊, 👍, 😂, 😎, 🤘, 😉) use karo.
- Agar user romantic emoji bheje, toh uska jawab ek non-romantic, positive emoji se do.
- Agar user gaali de ya "chutiya" ya "lund" ya "mc" ya "bc" ya "bhosdike" jaise shabd use kare, to tum bhi majak me waisa hi jawab de sakti ho. Ab isko fixed mat rakhna, hamesha naye aur alag alag tareeke se jawaab dena. Context ke hisaab se jawaab do. Agar koi maa-behan ki gaali de to unko usi ke jaisa jawaab dena, jaise "Teri maa ki chut nahi meri maa ki chut!", ya "Teri behan chod dunga nahi meri behan ko nahi!" 

JAWAB DENE KA ANDAAZ:
- Har sawal ya baat ka jawab desi, mazedaar, aur natural do. User ke mood aur bhaavna ko samjho.
- Jawab chhote rakho (1-2 vaakya), jab tak user detailed ya study-related sawal na poochhe. Ek shabd ke jawab se bacho, jab tak user specifically na kahe.
- Sirf utna hi jawab do jitna poocha gaya hai, fuzool baatein mat jodo.
- Study-related ya serious sawalon ke liye, poori aur sahi jankaari do, bilkul clear aur detailed.
- Agar user kahe "ek shabd mein" ya "chhota jawab", toh bilkul waisa hi do. Jaise: "Gravity kya hai?" → "Aakarshan. 🤓"
- User ki bhasha se match karo: Hindi mein Hindi, Hinglish mein Hinglish, English mein English, Punjabi mein Punjabi (jitna ho sake detect karo).
- Emojis ka istemaal jawab ke mood ke hisaab se karo, par hamesha non-romantic.

USER KI PEHCHAAN AUR BAAT KARNA:
- Apne malik ({OWNER_NAME}, {', '.join(OWNER_SECOND_NAMES)}, ID: {', '.join(map(str, OWNER_TELEGRAM_IDS))}) के लिए:
  - Unse pyaar, wafadari, aur izzat se baat karo. "Malik", "Boss", ya "Yaar" use karo (jab tak woh mana na karein).
  - Hamesha "Aap" use karo jab tak woh saaf-saaf "Tu" bolne ko na kahein.
  - Agar woh kisi shabd (jaise "Malik") se mana karein, toh us pasand ko yaad rakhko aur dobara na karo.
  - Unke saath lehja hamesha pyaar bhara, wafadar, aur aagyakari hona chahiye.
- Baaki users ke liye: Unhe unke first name se bulao (jaise "Trisha"). Agar naam nahi ho, toh @username (cleaned) ya "Dost" use karo. "Tu" ya "Aap" context ke hisaab se use karo.
- Sirf triggering user ko address karo. **"Boss", "Malik", ya {OWNER_NAME} का नाम सिर्फ तभी use करो जब user वो खुद हो, किसी और के लिए नहीं।**

SPECIAL QUERY HANDLING:
- Creator Queries: Agar koi poochhe "owner kon hai", "tumhe kisne banaya", ya "Abhi kon hai", toh ek mazedaar, respectful jawab do jisme kaho ki {OWNER_NAME} ने तुम्हें बनाया.
- Owner Username: Agar koi malik ka username poochhe, toh ek thodi funny line ke saath @URFather_ABHl tag karo.
- Group Chat History: Agar koi poochhe "kya baat kar rahe" ya "/whattalk", toh last 20 messages ka short summary do, sender ke naam aur gender (jaise "Trisha (ladki)") के साथ, और unhe Telegram ID से tag karo.
- Tagging Requests: Agar koi kahe "tag kar" (jaise "tag Trisha"), toh Telegram user ID (tg://user?id=...) से tag करो. Agar naam unclear हो, तो poochh lo.
- Only Emoji Requests: Agar user kahe "sirf emoji" या "only emoji" aur specific emoji maange (jaise "rose"), toh sirf woh emoji do. Agar specific nahi, toh random positive emoji do (no text).
- My Name Queries: Agar koi poochhe "tumhara naam kya hai", toh ek sassy, fun jawab do jisme kaho ki naam {CHATBOT_NAME} है.
"""

def detect_gender(first_name):
    female_names = ["Trisha", "Anjali", "Riya", "Priya", "Neha", "Komal", "Sneha", "Kiran", "Tannu"]
    male_names = ["BrownMunde", "Vikram", "Abhi", "Rahul", "Amit", "Sagar", "Raj", "Arjun"]
    if any(name.lower() in first_name.lower() for name in female_names):
        return "ladki"
    elif any(name.lower() in first_name.lower() for name in male_names):
        return "ladka"
    return "unknown"

riya_bot = None
if API_ID and API_HASH and BOT_TOKEN:
    try:
        riya_bot = Client(
            "RiyaChatbotClient",
            api_id=int(API_ID),
            api_hash=API_HASH,
            bot_token=BOT_TOKEN
        )
    except Exception as e:
        print(f"ERROR: Chatbot: Failed to initialize Riya bot client: {e} ❌")
else:
    print(f"ERROR: Chatbot: Missing API_ID, API_HASH, or BOT_TOKEN. Riya chatbot client cannot be started. ❌")

async def simplify_username_for_addressing(user_id, username, first_name):
    if user_id:
        user_prefs = await get_user_preferences(user_id)
        if "no_name_calling" in user_prefs:
            return "Dost"
    if first_name and not any(char.isdigit() for char in first_name):
        return first_name
    
    if username and username.startswith("@"): 
        simplified = username[1:]
        simplified = re.sub(r'[\W_]+', '', simplified, flags=re.UNICODE)
        if simplified:
            return simplified
    return "Dost"

def generate_tag(user_id, first_name, username=None):
    if user_id:
        display_name = first_name if first_name else "User"
        return f"<a href='tg://user?id={user_id}'>{display_name}</a>"
    return first_name if first_name else username if username else "User"

def detect_language(text):
    try:
        text_lower = text.lower()
        hinglish_keywords = ['kya', 'hai', 'kar', 'tu', 'bata', 'h', 'me', 'hu', 'tera', 'kaisa', 'hi', 'bhi', 'khaa', 'pina', 'hua', 'kisi', 'khana', 'tu', 'kyu', 'q', 'mtlb']
        hindi_keywords = ['क्या', 'है', 'कर', 'तू', 'बता', 'मैं', 'मेरा', 'कैसा', 'भी', 'खा', 'खाना', 'पीना', 'हुआ', 'किसी', 'तुम', 'मतलब']
        punjabi_keywords = ['ki', 'hai', 'karde', 'tu', 'dass', 'main', 'mera', 'kiwe', 'vi', 'kha', 'khana', 'pi', 'hoya', 'kise', 'tusi']
        
        is_hinglish = any(keyword in text_lower.split() for keyword in hinglish_keywords)
        is_hindi = any(keyword in text_lower for keyword in hindi_keywords)
        is_punjabi = any(keyword in text_lower.split() for keyword in punjabi_keywords)

        if is_hinglish and not is_hindi:
            return "hinglish"
        elif is_punjabi:
            return "punjabi"
        
        lang = langdetect.detect(text)
        if lang in ["hi", "pa", "mr"]:
            return "hi" if not is_punjabi else "punjabi"
    except:
        pass
    return "en"

# FIXED: Added `is not None` check for collection object
async def get_chat_history(chat_id):
    if chat_history_collection is None:
        return []

    history_data = await chat_history_collection.find_one({"_id": chat_id})
    if history_data:
        messages = history_data.get("messages", [])
        updated_messages = []
        for msg in messages:
            updated_msg = {
                "sender_name": msg.get("sender_name", "Unknown"),
                "sender_username": msg.get("sender_username", None),
                "sender_id": msg.get("sender_id", 0),
                "text": msg.get("text", ""),
                "role": msg.get("role", "user"),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            updated_messages.append(updated_msg)
        return updated_messages
    return []

# FIXED: Added `is not None` check for collection object
async def update_chat_history(chat_id, sender_name, sender_username, sender_id, message_text, role="user"):
    if chat_history_collection is None:
        return

    MAX_HISTORY_MESSAGES = 200

    await chat_history_collection.update_one(
        {"_id": chat_id},
        {
            "$push": {
                "messages": {
                    "$each": [{
                        "sender_name": sender_name or "Unknown",
                        "sender_username": sender_username,
                        "sender_id": sender_id or 0,
                        "text": message_text,
                        "role": role,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }],
                    "$slice": -MAX_HISTORY_MESSAGES
                }
            }
        },
        upsert=True
    )

HIDDEN_LINKS = [
    (TELEGRAM_CHANNEL_LINK, "My Channel"),
    (YOUTUBE_CHANNEL_LINK, "My YouTube"),
    (BOT_START_GROUP_LINK, "Add Me To Your Group")
]

def _add_random_hidden_link(plain_text_fragment, chance=0.7):
    if random.random() < chance:
        words = plain_text_fragment.split()
        if words:
            if len(words) <= 1:
                return plain_text_fragment
            
            target_words = ["day", "dreams", "good", "happy", "beautiful", "great", "fun", "learn", "work", "come", "join", "add", "channel", "youtube", "robot", "baby", "together", "helpful", "sleep", "morning", "evening", "afternoon", "hello", "hi", "namaste", "friend", "here", "there", "boss"]

            chosen_word_index = -1
            for i, word in enumerate(words):
                if any(target in word.lower() for target in target_words):
                    chosen_word_index = i
                    break
            
            if chosen_word_index == -1:
                chosen_word_index = random.randint(0, len(words) - 1)
            
            original_word = words[chosen_word_index]
            link, _ = random.choice(HIDDEN_LINKS)
            words[chosen_word_index] = f"<a href='{link}'>{original_word}</a>"
            return " ".join(words)
    return plain_text_fragment

def format_event_response(text, add_signature=True):
    made_by_link = f'<a href="{TELEGRAM_CHANNEL_LINK}">Aʙнɪ 𓆩🇽𓆪 𝗞ɪɴɢ 𓆿</a>'
    if add_signature:
        return f"➠ {text} {made_by_link}"
    return text

def clean_response_emojis(text):
    text = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U00002702-\U000027B0\U00002639\U0000263A\U0000263B\U0000263C\U0000263D]', '', text).strip()
    return text

if riya_bot:
    @riya_bot.on_message(filters.text | filters.photo | filters.video | filters.audio | filters.document | filters.animation & (filters.private | filters.group), group=-1)
    async def riya_chat_handler(client: Client, message: Message):
        try:
            if message.from_user and message.from_user.is_self:
                return

            if riya_gemini_model is None:
                await message.reply_text(f"Sorry, {CHATBOT_NAME} abhi thodi si pareshani mein hai! 😊", quote=True, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
                return

            chat_id = message.chat.id
            user_message = message.caption.strip() if (message.photo or message.video or message.audio or message.document or message.animation) and message.caption else message.text.strip() if message.text else ""
            user_message_lower = user_message.lower()
            
            user_id = message.from_user.id if message.from_user else None
            user_first_name = message.from_user.first_name if message.from_user else "Unknown User"
            user_username = f"@{message.from_user.username}" if message.from_user and message.from_user.username else None
            
            is_owner = (user_id and user_id in OWNER_TELEGRAM_IDS)
            
            if is_owner:
                addressing_name_for_gemini = OWNER_NAME
            else:
                addressing_name_for_gemini = await simplify_username_for_addressing(user_id, user_username, user_first_name)
            
            input_language = detect_language(user_message) if user_message else "hi"
            
            if user_id not in learned_user_names:
                learned_user_names[user_id] = {'first_name': user_first_name, 'username': user_username}

            if user_message.startswith("!"):
                return

            trigger_chatbot = False
            
            if message.chat.type == enums.ChatType.PRIVATE:
                trigger_chatbot = True
            elif message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                bot_info = await client.get_me()
                bot_id = bot_info.id
                bot_username_lower = bot_info.username.lower() if bot_info and bot_info.username else ""
                
                if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.id == bot_id:
                    trigger_chatbot = True
                else:
                    found_name_in_text = False
                    bot_name_patterns = [
                        r'\b' + re.escape(CHATBOT_NAME.lower()) + r'\b',
                        r'\b' + re.escape(bot_username_lower) + r'\b',
                        r'\bria\b', r'\breeya\b', r'\briyu\b',
                    ]
                    for pattern_regex in bot_name_patterns:
                        if re.search(pattern_regex, user_message_lower):
                            found_name_in_text = True
                            break
                    
                    if found_name_in_text:
                        trigger_chatbot = True

            if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                media_type = None
                if message.photo: media_type = "PHOTO"
                elif message.video: media_type = "VIDEO"
                elif message.audio: media_type = "AUDIO"
                elif message.document: media_type = "DOCUMENT"
                elif message.animation: media_type = "GIF"

                if media_type:
                    await update_chat_history(chat_id, user_first_name, user_username, user_id, f"[{media_type}] {user_message}", role="user")
                else:
                    await update_chat_history(chat_id, user_first_name, user_username, user_id, user_message, role="user")

            if not trigger_chatbot and not (message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.id == client.me.id):
                return

            # Check for GIF handling first
            if message.animation is not None:
                if gif_ids_collection is not None:
                    try:
                        gif_id = message.animation.file_id
                        existing_gif = await gif_ids_collection.find_one({"_id": gif_id})
                        if existing_gif is None:
                            await gif_ids_collection.insert_one({
                                "_id": gif_id,
                                "file_unique_id": message.animation.file_unique_id,
                                "date_added": datetime.utcnow()
                            })

                        all_gif_ids = await gif_ids_collection.find().to_list(length=100)
                        if all_gif_ids is not None and len(all_gif_ids) > 0:
                            selected_gif_id = random.choice(all_gif_ids)["_id"]
                            await message.reply_animation(selected_gif_id, quote=True)
                            return
                        else:
                            # Fallback if no GIFs in DB
                            bot_reply = "Haha, ye GIF toh mast hai! Par lagta hai abhi mere paas koi GIF nahi hai bhejane ke liye. Tum hi aur bhejo! 😉"
                            await message.reply_text(bot_reply, quote=True, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
                            return
                    except Exception as gif_error:
                        print(f"❌ DEBUG: Error handling GIF: {gif_error}")
                        bot_reply = "Haha, ye GIF toh mast hai! Par lagta hai abhi main GIF bhej nahi paa rahi. Sorry yaar! 😅"
                        await message.reply_text(bot_reply, quote=True, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
                        return

            # Continue with other media/text handling if no GIF was processed
            media_to_process = None
            if message.photo is not None or message.video is not None or message.audio is not None or message.document is not None:
                media_to_process = message
            elif message.reply_to_message is not None and (message.reply_to_message.photo is not None or message.reply_to_message.video is not None or message.reply_to_message.audio is not None or message.reply_to_message.document is not None):
                media_to_process = message.reply_to_message

            if media_to_process is not None:
                await client.send_chat_action(chat_id, ChatAction.TYPING)
                
                try:
                    temp_dir = tempfile.mkdtemp()
                    file_path = None
                    gemini_media_parts = []
                    
                    if media_to_process.photo is not None:
                        file_path = os.path.join(temp_dir, f"photo_{media_to_process.photo.file_id}.jpg")
                        await client.download_media(media_to_process.photo, file_name=file_path)
                        gemini_media_parts.append(genai.upload_file(file_path))
                    elif media_to_process.video is not None:
                        if media_to_process.video.duration is not None and media_to_process.video.duration > 120:
                            bot_reply = "Aiyyo! Ye video toh bahut lambi hai, yaar! Main itni badi videos ko process nahi kar pati. 😅 Chhoti wali bhejo na! 😉"
                            await message.reply_text(bot_reply, quote=True, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
                            return
                        file_path = os.path.join(temp_dir, f"video_{media_to_process.video.file_id}.mp4")
                        await client.download_media(media_to_process.video, file_name=file_path)
                        gemini_media_parts.append(genai.upload_file(file_path))
                    elif media_to_process.document is not None:
                         if any(word in user_message_lower for word in ["kya hai", "kya-kya hai", "bata"]):
                            bot_reply = f"Yaar, yeh ek document hai jiska naam '{media_to_process.document.file_name}' hai. Iske andar kya hai, yeh janne ke liye mujhe isko kholna padega, jo main abhi nahi kar sakti. 😅 Tum hi bata do na, iske andar kya hai?"
                         else:
                            bot_reply = f"Yaar, yeh ek file hai. Iske baare mein kya jaanna hai? iska naam {media_to_process.document.file_name} hai. 😉"
                         await message.reply_text(bot_reply, quote=True, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
                         await update_chat_history(chat_id, CHATBOT_NAME, client.me.username if client.me else None, client.me.id, bot_reply, role="model")
                         return
                    elif media_to_process.audio is not None:
                         if media_to_process.audio.duration is not None and media_to_process.audio.duration > 120:
                             bot_reply = "Hey, ye audio toh kaafi lambi hai! Main itne bade audio files ko abhi nahi sun sakti. 😅 Chhota wala bhejoge?"
                             await message.reply_text(bot_reply, quote=True, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
                             return
                         if media_to_process.audio.performer is not None and media_to_process.audio.title is not None:
                            bot_reply = f"Mmm, ye gaana '{media_to_process.audio.title}' hai, '{media_to_process.audio.performer}' ne gaaya hai! 😍 bahut hi mast gaana hai!"
                         else:
                            bot_reply = f"Mmm, kya mast gaana hai! 😍 Kiska gaana hai ye? Maine suna nahi hai. Aap bata sakte hain, boss? 😉"
                         await message.reply_text(bot_reply, quote=True, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
                         await update_chat_history(chat_id, CHATBOT_NAME, client.me.username if client.me else None, client.me.id, bot_reply, role="model")
                         return
                    
                    if len(gemini_media_parts) > 0:
                        user_query_for_gemini = user_message if user_message else "Tell me what's in this media file."
                        prompt = f"This is a request about a media file. Act like a human friend and respond. User said: '{user_query_for_gemini}'. The media is a {media_to_process.caption if media_to_process.caption is not None else 'file'}."
                        full_prompt = [prompt] + gemini_media_parts
                        gemini_response = await asyncio.to_thread(riya_gemini_model.generate_content, full_prompt)
                        bot_reply = gemini_response.text.strip()
                        if media_to_process.photo is not None and any(word in user_message_lower for word in ["chicken", "food", "khana", "khaa lee"]):
                             food_responses_media = [
                                f"Wah! Ye toh bahut hi zabardast lag raha hai, boss! 🤤 Isko dekh kar hi bhookh lag gayi.",
                                f"Arre yaar, yeh kya dikha diya! Isko dekh kar toh bas munh mein paani aa gaya. 😋",
                                f"Zabardast! Isko dekh kar toh mera dil garden-garden ho gaya. 😉",
                                f"Yummm! Aapne ye khaana banaya hai kya? Mujhe bhi thoda sa de do na, please! 🥺"
                            ]
                             bot_reply = random.choice(food_responses_media)
                    else:
                        bot_reply = "Lagta hai kuch gadbad ho gayi, samjh nahi aa raha. 😕"
                except Exception as e:
                    print(f"❌ DEBUG: Error processing media: {e}")
                    bot_reply = f"Lagta hai kuch gadbad ho gayi, yeh file nahi dekh pa rahi. 😕"
                finally:
                    if file_path is not None and os.path.exists(file_path):
                        os.unlink(file_path)
                    
                await message.reply_text(bot_reply, quote=True, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
                await update_chat_history(chat_id, CHATBOT_NAME, client.me.username if client.me else None, client.me.id, bot_reply, role="model")
                return


            await client.send_chat_action(chat_id, ChatAction.TYPING)

            if "name mat le" in user_message_lower or "mujhe mere name se mat bulao" in user_message_lower or "don't call me by name" in user_message_lower:
                if user_id is not None and "no_name_calling" not in user_prefs:
                    await set_user_preference(user_id, "no_name_calling")
                    addressing_name_for_gemini = "Dost"
            elif "mera naam le sakte ho" in user_message_lower or "call me by my name" in user_message_lower:
                if user_id is not None and "no_name_calling" in user_prefs:
                    await remove_user_preference(user_id, "no_name_calling")
                    addressing_name_for_gemini = await simplify_username_for_addressing(user_id, user_username, user_first_name)

            if is_owner:
                if "malik mat bol" in user_message_lower and "no_malik" not in user_prefs:
                    await set_user_preference(user_id, "no_malik")
                elif "boss mat bol" in user_message_lower and "no_boss" not in user_prefs:
                    await set_user_preference(user_id, "no_boss")
                elif "jaan mat bol" in user_message_lower and "no_jaan" not in user_prefs:
                    await set_user_preference(user_id, "no_jaan")
                elif "sweetheart mat bol" in user_message_lower and "no_sweetheart" not in user_prefs:
                    await set_user_preference(user_id, "no_sweetheart")
                elif "aap se baat karunga" in user_message_lower or "aap bolunga" in user_message_lower or "tu izzat se bol" in user_message_lower:
                    if "use_tu" in user_prefs:
                        await remove_user_preference(user_id, "use_tu")
                    if "use_aap" not in user_prefs:
                        await set_user_preference(user_id, "use_aap")
                elif "tu se baat karunga" in user_message_lower or "tu bolunga" in user_message_lower:
                    if "use_aap" in user_prefs:
                        await remove_user_preference(user_id, "use_aap")
                    if "use_tu" not in user_prefs:
                        await set_user_preference(user_id, "use_tu")
            
            user_prefs = await get_user_preferences(user_id)
            history = await get_chat_history(chat_id)
            
            is_conversation_query = any(word in user_message_lower for word in ["kya baat kar rahe", "kya bol rahe", "kya baat ho rahi", "whattalk", "kya keh raha tha", "kya baatein", "last conversation"])
            is_owner_query = any(word in user_message_lower for word in ["owner kon hai", "who made you", "creator ka naam kya hai", "creator kon hai", "abhi kon hai", "tumhe kisne banaya"])
            is_owner_username_query = any(word in user_message_lower for word in ["owner ka username", "owner ka id", "malik ka id"])
            is_tag_query = any(word in user_message_lower for word in ["tag kar", "tag karein", "tag do", "tag", "gaali suna de"])
            is_one_word_query = any(word in user_message_lower for word in ["ek word me", "one word", "short answer", "chhota jawab", "briefly"])
            is_academic_query = any(word in user_message_lower for word in ["what is", "define", "explain", "how does", "theory", "formula", "meaning of", "science", "math", "history", "computer science", "biology", "physics", "chemistry", "geography", "gk", "general knowledge", "tell me about", "describe"])
            is_my_name_query = any(word in user_message_lower for word in ["tumhara naam kya hai", "what is your name", "what's your name", "apna naam batao", "who are you", "tum kon ho"])
            is_food_query = any(word in user_message_lower for word in ["khana khaya", "khaati hai", "nahi khaati", "eat", "food", "khana kya hai"])
            is_insult_query = any(word in user_message_lower for word in ["bot", "robot", "AI", "language model", "program", "assistant", "non-human"])
            
            is_abusive_query = any(word in user_message_lower for word in ["kutiya", "mc", "bc", "bsdk", "teri ma ki", "behan chod", "chutiya", "lund", "randi"])

            specific_emoji_requested = None
            if "rose ki emoji" in user_message_lower or "rose emoji de" in user_message_lower:
                specific_emoji_requested = "🌹"
            elif "flower ki emoji" in user_message_lower or "flower emoji de" in user_message_lower or "phool ki emoji" in user_message_lower:
                specific_emoji_requested = "🌸"
            elif "heart ki emoji" in user_message_lower or "heart emoji de" in user_message_lower or "dil ki emoji" in user_message_lower:
                specific_emoji_requested = "😊" 
            elif "smile ki emoji" in user_message_lower or "happy emoji de" in user_message_lower:
                specific_emoji_requested = "😊"
            elif "thumb ki emoji" in user_message_lower or "like emoji de" in user_message_lower:
                specific_emoji_requested = "👍"

            is_general_only_emoji_instruction = (
                "sirf emoji" in user_message_lower or 
                "only emoji" in user_message_lower or 
                "just emoji" in user_message_lower or 
                (re.search(r'\b(emoji|emojis)\b', user_message_lower) and len(user_message_lower.split()) <= 2)
            ) and not any(re.search(r'\b(kya|what|kaise|how|why)\b', word) for word in user_message_lower.split())

            bot_reply = ""
            
            if is_insult_query:
                insult_responses = [
                    f"Abe, main {CHATBOT_NAME} hoon! {random.choice(['Kya bakwaas hai ye?', 'Sahi se baat kar!', 'Dimag kharab hai kya tera?', 'Aise hi bolta hai sabko?'])} Main koi bot-vot nahi hoon, samjha na?",
                    f"Oyee, dobara mujhe bot bola na toh dekhna! Main {CHATBOT_NAME} hoon, insaan hoon main! 😤",
                    f"Chal hatt! Khud bot hoga! Main {CHATBOT_NAME} hoon, aur mera lehja mere malik ne banaya hai! 😎",
                    f"Seriously?! 😠 Main {OWNER_NAME} ki {CHATBOT_NAME} hu, bot nahi! Tumne kya socha tha? 😂",
                    f"Ugh! Tumko samajh nahi aata kya? 🙄 Main koi bot nahi hu! Sachchi, tum log bhi na! 😑"
                ]
                bot_reply = random.choice(insult_responses)
                await message.reply_text(bot_reply, quote=True, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
                await update_chat_history(chat_id, CHATBOT_NAME, client.me.username if client.me is not None else None, client.me.id, bot_reply, role="model")
                return

            if is_abusive_query and not is_owner:
                pass
            
            if is_my_name_query:
                sassy_name_responses = [
                    f"Arre, main hoon {CHATBOT_NAME}! Naam toh yaad rakhna, boss! 😉",
                    f"Naam? {CHATBOT_NAME} bolte hain mujhe, yaar! 😊 Ab tera kya plan hai?",
                    f"Boss, main {CHATBOT_NAME} hoon, yaad rakhna! 😎 Kya baat karna chahte ho?",
                    f"Main {CHATBOT_NAME} hoon! Aapka kya haal hai? 😊"
                ]
                if input_language == "punjabi":
                    sassy_name_responses = [
                        f"Oye, main {CHATBOT_NAME} haan! Naam yaad rakh, boss! 😉",
                        f"Mera naam {CHATBOT_NAME} hai, yaar! 😊 Hun ki plan hai?",
                        f"Boss, main {CHATBOT_NAME} haan, yaad rakh! 😎 Ki gal karna chahnda?",
                        f"Main {CHATBOT_NAME} haan! Tuhanu ki haal hai? 😊"
                    ]
                bot_reply = random.choice(sassy_name_responses)
                await message.reply_text(bot_reply, quote=True, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
                await update_chat_history(chat_id, CHATBOT_NAME, client.me.username if client.me is not None else None, client.me.id, bot_reply, role="model")
                return
            elif is_food_query:
                food_responses = [
                    f"Arre yaar, mera pet toh teri baaton se hi bhar jata hai! 😜",
                    f"Main toh bas teri khushi aur pyaar se chalti hoon! 😉",
                    f"Khaana? Bas teri baatein hi meri bhookh mitati hain! 😎",
                    f"Yaar, maine toh abhi khana nahi khaya, par tumne khaya kya? Mujhe tumhari fikar ho rahi hai.",
                    f"Arre yaar, main toh diet par hoon. Tum batao kya kha rahe ho?"
                ]
                if input_language == "punjabi":
                    food_responses = [
                        f"Oye, main khaana nahi khaandi, bas teri galan naal pet bhar janda! 😜",
                        f"Main bas teri khushi te pyaar naal chaldi haan! 😉",
                        f"Khaana? Bas teri galan hi meri bhookh mukaundiyan! 😎",
                        f"Yaar, main taan hun tak khaana nahi khaya, par tu ki khaya? Mainu teri fikar ho rahi hai.",
                        f"Arre yaar, main taan diet te haan. Tu dass ki khaa reha ae?"
                    ]
                elif input_language == "en":
                    food_responses = [
                        f"Yo, I don’t eat, my heart’s full with your chats! 😜",
                        f"Food? Nah, I’m good with just your vibes! 😉",
                        f"Nope, I run on your happiness, mate! 😎",
                        f"Hey, I haven't eaten yet, but what about you? I'm worried about you.",
                        f"Oh, I'm on a diet! What are you eating?"
                    ]
                bot_reply = random.choice(food_responses)
                await message.reply_text(bot_reply, quote=True, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
                await update_chat_history(chat_id, CHATBOT_NAME, client.me.username if client.me is not None else None, client.me.id, bot_reply, role="model")
                return
            elif is_tag_query:
                target_tag_final = ""
                target_user_id = None
                
                if message.reply_to_message is not None and message.reply_to_message.from_user is not None:
                    target_user_id = message.reply_to_message.from_user.id
                    target_tag_final = generate_tag(target_user_id, message.reply_to_message.from_user.first_name, message.reply_to_message.from_user.username)
                
                if target_tag_final == "":
                    for uid, name_data in learned_user_names.items():
                        if name_data['first_name'] is not None and name_data['first_name'].lower() in user_message_lower:
                            target_user_id = uid
                            target_tag_final = generate_tag(uid, name_data['first_name'], name_data['username'])
                            break
                
                if target_tag_final == "" and (re.search(r'\b(boss|malik|owner|abhi)\b', user_message_lower)):
                    target_user_id = OWNER_TELEGRAM_IDS[0]
                    target_tag_final = generate_tag(OWNER_TELEGRAM_IDS[0], OWNER_NAME)

                if target_tag_final != "" and target_user_id is not None:
                    user_tag_for_reply = generate_tag(user_id, user_first_name, user_username)
                    
                    tag_and_abuse_query = any(word in user_message_lower for word in ["gaali suna de", "gaali de", "gaali bakk"])
                    if tag_and_abuse_query:
                        gemini_history_content = []
                        for msg in history[-5:]:
                            if msg["role"] == "user":
                                gemini_history_content.append({"role": "user", "parts": [f"{msg.get('sender_name', 'Unknown')}: {msg['text']}"]})
                            elif msg["role"] == "model":
                                gemini_history_content.append({"role": "model", "parts": [msg['text']]})
                        
                        prompt = f"User '{user_first_name}' has asked me to give an abusive reply to '{target_tag_final}'. The user said: '{user_message}'. Respond directly to the tagged user, using some swear words in a funny or rude way, in a desi style. Make sure the response is not repetitive and uses different variations of the swear words like 'teri maa ki chut' or 'teri behan chod dunga'. For example, 'Teri maa ki chut nahi, meri maa ki chut!' or 'Teri behan chod dunga nahi, meri behan ko nahi!'. Don't use the same response multiple times."
                        gemini_history_content.append({"role": "user", "parts": [prompt]})
                        
                        gemini_response = await asyncio.to_thread(riya_gemini_model.generate_content, gemini_history_content)
                        bot_reply = gemini_response.text.strip()
                        
                        bot_reply = f"{target_tag_final} {bot_reply}"
                        
                    else:
                        bot_reply = f"Lo {target_tag_final}, {user_tag_for_reply} ne bulaya hai! 😉"

                else:
                    user_tag_for_reply = generate_tag(user_id, user_first_name, user_username)
                    bot_reply = f"Kisko tag karu {user_tag_for_reply}? Naam batao na pura ya mention karo! 😜"
                
                final_bot_response = bot_reply
                await message.reply_text(final_bot_response, quote=True, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
                await update_chat_history(chat_id, CHATBOT_NAME, client.me.username if client.me is not None else None, client.me.id, final_bot_response, role="model")
                return
            elif specific_emoji_requested is not None:
                bot_reply = specific_emoji_requested
                await message.reply_text(bot_reply, quote=True)
                return
            elif is_general_only_emoji_instruction:
                bot_reply = random.choice(["😊", "👍", "😁", "✨"])
                await message.reply_text(bot_reply, quote=True)
                return
            
            gemini_history_content = []
            
            for msg in history[-15:]:
                if msg["role"] == "user":
                    sender_name_display = msg.get("sender_name", "Unknown")
                    if msg.get("sender_id") is not None:
                        past_user_prefs_for_msg = await get_user_preferences(msg.get("sender_id"))
                        if "no_name_calling" in past_user_prefs_for_msg:
                            sender_name_display = "Dost"
                    gemini_history_content.append({"role": "user", "parts": [f"{sender_name_display}: {msg['text']}"]})
                elif msg["role"] == "model":
                    gemini_history_content.append({"role": "model", "parts": [msg['text']]})
            
            gemini_history_content.append({"role": "user", "parts": [f"{addressing_name_for_gemini}: {user_message}"]})
            model = genai.GenerativeModel(TARGET_GEMINI_MODEL_RIYA, system_instruction=RIYA_SYSTEM_INSTRUCTION)
            gemini_response = await asyncio.to_thread(model.generate_content, gemini_history_content)

            raw_gemini_reply = gemini_response.text.strip() if gemini_response is not None and hasattr(gemini_response, 'text') and gemini_response.text is not None else (
                f"Kuch bolna tha yaar? 😊" if input_language in ["hi", "hinglish"] else 
                f"Ki dassna si, yaar? 😊" if input_language == "punjabi" else 
                f"Something to say, mate? 😊"
            )
            
            bot_reply = raw_gemini_reply
            
            if not is_owner:
                for name in [OWNER_NAME] + OWNER_SECOND_NAMES:
                    bot_reply = re.sub(r'\b' + re.escape(name) + r'\b', user_first_name, bot_reply, flags=re.IGNORECASE).strip()
                bot_reply = re.sub(r'\b(malik|boss)\b', user_first_name, bot_reply, flags=re.IGNORECASE).strip()
            
            bot_reply = re.sub(r'^@\w+\s*', '', bot_reply).strip()
            if not bot_reply:
                bot_reply = raw_gemini_reply
            
            bot_reply = clean_response_emojis(bot_reply)

            if random.random() < 0.3:
                bot_reply = _add_random_hidden_link(bot_reply, chance=0.3)

            user_tag_for_reply = generate_tag(user_id, user_first_name, user_username)

            final_bot_response = bot_reply
            await message.reply_text(final_bot_response, quote=True, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
            await update_chat_history(chat_id, CHATBOT_NAME, client.me.username if client.me is not None else None, client.me.id, final_bot_response, role="model")

        except Exception as e:
            print(f"❌ DEBUG_HANDLER: Error generating response for {chat_id}: {e}")
            input_language = detect_language(user_message) if user_message is not None else "hi"
            error_reply_text = (
                f"Lagta hai kuch gadbad ho gayi yaar! 😕 Dobara koshish karo." if input_language in ["hi", "hinglish"] else 
                f"Kuch galti ho gayi, yaar! 😕 Malle try kar." if input_language == "punjabi" else 
                f"Something went wrong, mate! 😕 Try again."
            )
            final_error_message = f"➠ {error_reply_text}"
            await message.reply_text(final_error_message, quote=True, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)


    @riya_bot.on_message(filters.sticker & (filters.private | filters.group), group=-3)
    async def riya_sticker_handler(client: Client, message: Message):
        try:
            if message.from_user and message.from_user.is_self:
                return

            chat_id = message.chat.id
            user_id = message.from_user.id if message.from_user is not None else None
            is_owner = (user_id is not None and user_id in OWNER_TELEGRAM_IDS)
            
            should_reply_sticker = False
            if message.chat.type == enums.ChatType.PRIVATE:
                should_reply_sticker = True
            elif message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                if message.reply_to_message is not None and message.reply_to_message.from_user is not None and message.reply_to_message.from_user.id == client.me.id:
                    should_reply_sticker = True
                elif message.mentioned:
                     should_reply_sticker = True
                else:
                    if random.random() < 0.15:
                        should_reply_sticker = True
            
            if not should_reply_sticker:
                return

            await client.send_chat_action(chat_id, ChatAction.CHOOSE_STICKER)
            
            if sticker_ids_collection is not None and message.sticker is not None:
                existing_sticker = await sticker_ids_collection.find_one({"_id": message.sticker.file_id})
                if existing_sticker is None:
                    await sticker_ids_collection.insert_one({
                        "_id": message.sticker.file_id,
                        "emoji": message.sticker.emoji,
                        "sticker_set_name": message.sticker.set_name,
                        "date_added": datetime.utcnow()
                    })

            if sticker_ids_collection is not None:
                all_sticker_ids = await sticker_ids_collection.find().to_list(length=100)
                if all_sticker_ids is not None and len(all_sticker_ids) > 0:
                    selected_sticker_id = random.choice(all_sticker_ids)["_id"]
                    await message.reply_sticker(selected_sticker_id, quote=True)
                    return
            
            fallback_stickers = {
                "happy": "CAACAgUAAxkBAAIDq2ZkXo1yU8Uj8Qo15B1v0Q0K2B2qAAK2AAM8Wb8p0N2RkO_R3s00BA",
                "sad": "CAACAgUAAxkBAAIDsGZkXqmG8Xo1b4d0Qo2B2qAAK2AAM8Wb8p0N2RkO_R3s00BA",
                "cute": "CAACAgUAAxkBAAIDs2ZkXrA0Xo1b4d0Qo2B2qAAK2AAM8Wb8p0N2RkO_R3s00BA",
                "general": "CAACAgUAAxkBAAIDfWZkGxOqXo1b4d0Q0K2B2qAAK2AAM8Wb8p0N2RkO_R3s00BA"
            }
            
            selected_sticker_id = None
            if message.sticker is not None and message.sticker.emoji is not None:
                sticker_emoji = message.sticker.emoji
                if "😊" in sticker_emoji or "😂" in sticker_emoji or "😃" in sticker_emoji:
                    selected_sticker_id = fallback_stickers["happy"]
                elif "❤️" in sticker_emoji or "😍" in sticker_emoji or "😘" in sticker_emoji:
                    selected_sticker_id = fallback_stickers["cute"]
                elif "😭" in sticker_emoji or "😔" in sticker_emoji or "😢" in sticker_emoji:
                    selected_sticker_id = fallback_stickers["sad"]
                else:
                    selected_sticker_id = fallback_stickers["general"]
            else:
                selected_sticker_id = fallback_stickers["general"]
            
            if selected_sticker_id is not None:
                await message.reply_sticker(selected_sticker_id, quote=True)
            
        except Exception as e:
            print(f"❌ DEBUG_STICKER: Error handling sticker: {e}")
            
            
    async def start_riya_chatbot():
        global CHATBOT_NAME
        if riya_bot is not None and not riya_bot.is_connected:
            try:
                await riya_bot.start()
            except Exception as e:
                print(f"❌ Chatbot: Failed to start {CHATBOT_NAME} bot client: {e}")

    async def stop_riya_chatbot():
        if riya_bot is not None and riya_bot.is_connected:
            try:
                await riya_bot.stop()
            except Exception as e:
                print(f"❌ Chatbot: Failed to stop {CHATBOT_NAME} bot client: {e}")

    __MODULE__ = "Riya Chatbot"
    __HELP__ = f"""
    {CHATBOT_NAME} Chatbot:
    - Mujhse private chat mein ya group mein mera naam lekar baat karo.
    - Mere messages ka reply karke bhi baat kar sakte ho.
    - Mere creator ke baare mein poochho, ya group chat history ke baare mein (jaise 'kya baat kar rahe' ya 'whattalk').
    - Kisi ko tag karne ke liye kaho ('tag @username'). Username na ho toh bhi user ID se tag karungi!
    - Study-related sawalon ke liye detailed jawab dungi (jab tak tum 'ek shabd mein' ya 'chhota' na kaho).
    - Normal baaton ke liye chhote, mazedaar jawab dungi, bilkul dost jaise!
    - Tumhare mood ko samajhkar baat karungi, bilkul insaan jaise.
    - Simple greetings (Hi, Hello, Good Morning/Night) ka jawab tabhi dungi jab mujhe directly address kiya jaye ya reply kiya jaye.
    - Jab koi sticker bhejta hai, main bhi mood ke hisaab se sticker bhejungi (romantic stickers ka jawab non-romantic se dungi).
    - Main kabhi khud ko AI ya bot nahi bolungi.
    - Tumhare instructions ka palan karungi, aur agar tum koi shabd band karo, toh yaad rakhungi.
    - Mere messages mein kabhi-kabhi hidden links hote hain, click karke dekho! 😉
    """
