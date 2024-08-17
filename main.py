import streamlit as st
import os
import json
import re
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from whatsapp_chatbot_python import GreenAPIBot, Notification
from deep_translator import GoogleTranslator
from functools import lru_cache
from filelock import FileLock, Timeout

load_dotenv()

st.set_page_config(page_title="WhatsApp Bot Dashboard", page_icon=":speech_balloon:", layout="wide")

st.markdown("""
<style>
.stApp {
    background-color: #1E1E1E;
    color: #FFFFFF;
}
.stTextInput > div > div > input {
    background-color: #2E2E2E;
    color: #FFFFFF;
}
</style>
""", unsafe_allow_html=True)

required_env_vars = [
    "OPENAI_API_KEY",
    "GREENAPI_ID_INSTANCE",
    "GREENAPI_ACCESS_TOKEN",
    "GROQ_API_KEY"
]

for var in required_env_vars:
    if not os.getenv(var):
        st.error(f"{var} is not set")
        st.stop()

bot = GreenAPIBot(os.getenv("GREENAPI_ID_INSTANCE"), os.getenv("GREENAPI_ACCESS_TOKEN"))
openaiClient = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

from src.GroqClass import GroqClass
myGroq = GroqClass(api_key=os.getenv("GROQ_API_KEY"))

@lru_cache(maxsize=1000)
def is_hebrew(prompt: str) -> bool:
    return any('\u0590' <= char <= '\u05FF' for char in prompt)

@lru_cache(maxsize=1000)
def translate_text(text: str, target_language: str):
    try:
        translator = GoogleTranslator(source='auto', target=target_language)
        return translator.translate(text)
    except Exception as e:
        return f"Error occurred during translation: {e}"

MAX_HISTORY_LENGTH = 20
DATA_FOLDER = Path(__file__).parent / "data"
DATA_FOLDER.mkdir(exist_ok=True)

def get_chat_history(phone_number: str) -> list:
    output_path = DATA_FOLDER / f'{phone_number}_data.json'
    if output_path.exists():
        with output_path.open('r') as file:
            return json.load(file)
    return []

def save_chat_history(phone_number: str, history: list) -> None:
    output_path = DATA_FOLDER / f'{phone_number}_data.json'
    with output_path.open('w') as file:
        json.dump(history, file)

TEXT_TYPES = ["textMessage", "extendedTextMessage", "quotedMessage"]

                             
@bot.router.message(text_message=["start", "/start", "Start"])
def start_message_handler(notification: Notification) -> None:
    st.write(f"Start: start_message_handler")    
    sender_data = notification.event["senderData"]
    sender_name = sender_data["senderName"]
    notification.answer(
            (
                f"הי, {sender_name} אני החבר הסרקסטי, מהיר עם הערות שנונות וגישה שובבה.\n"
                "על כל שאלה שתשאל אפנק אותך בתשובה שנונה"
            )
        )
    
@bot.router.message(type_message=TEXT_TYPES)
def txt_message_handler(notification: Notification) -> None:
    try:
        st.write(f"Start: txt_message_handler")

        sender_data = notification.event["senderData"]
        user_message = notification.message_text
        chat_id = sender_data["chatId"]
        phone_number = re.sub(r'\D', '', chat_id)

        is_hebrew_message = is_hebrew(user_message)
        if is_hebrew_message:
            user_message = translate_text(user_message, "en")

        system_message = "You are a sarcastic friend, quick with witty remarks and a playful attitude. Keep your responses concise and to the point."
        chat_history = get_chat_history(phone_number)

        chat_history.append(f"User: {user_message}")
        chat_history = chat_history[-MAX_HISTORY_LENGTH:]

        history_prompt = "\n".join(chat_history) + f"\nUser: {user_message}"

        chat_response = myGroq.send_prompt(history_prompt, system_message, "random")
        
        chat_history.append(f"Bot: {chat_response}")
        save_chat_history(phone_number, chat_history)

        if is_hebrew_message and not is_hebrew(chat_response):
            chat_response = translate_text(chat_response, "iw")

    except Exception as e:
        chat_response = f"Failed to return message: {str(e)}"
        st.error(f"Failed to return message: {str(e)}")

    notification.answer(chat_response)
@bot.router.message(type_message=["imageMessage"])
def image_message_handler(notification: Notification) -> None:
    """
    Handler for image messages. Uses OCR and NLP to read values from the image and respond to the user.

    :param notification: Notification object containing event details.
    """
    st.write(f"Start: image_message_handler")    

    try:
        sender_data = notification.event["senderData"]
        chat_id = sender_data["chatId"]
        image_url = notification.event["messageData"]["fileMessageData"]["downloadUrl"]
        user_message = notification.event["messageData"]["fileMessageData"]["caption"]
        
        # Extract only numbers
        phone_number = re.sub(r'\D', '', chat_id)        

        DATA_FOLDER = (Path(__file__).parent / "data").resolve()
        output_path = DATA_FOLDER / f'{phone_number}_data.json'        

        system_prompt = (
            "Use OCR and NLP to read values from the image. It's very important you get the values accurately "
            "or it will result in a bad user experience."
        )
        user_prompt = "I'm partially blind, help me read the image below. "

        is_hebrew_message = False
        if user_message.strip():
            is_hebrew_message = is_hebrew(user_message)
            if is_hebrew_message:
                st.info("User message is in Hebrew.")
                # Translate Hebrew to English
                user_message = translate_text(user_message, "en")
            else:
                st.info("User message is not in Hebrew.")
            user_prompt += user_message
        else:
            st.warning("User message is empty.")

        # Load chat history
        chat_history = get_chat_history(phone_number)

        chat_history.append(f"User: {user_message}")
        chat_history = chat_history[-MAX_HISTORY_LENGTH:]

        history_prompt = "\n".join(chat_history) + f"\nUser: {user_message}"

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": history_prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ]

        response = openaiClient.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=messages,
            temperature=0.0,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

        chat_response = response.choices[0].message.content

        chat_history.append(f"Bot: {chat_response}")
        save_chat_history(phone_number, chat_history)

        if is_hebrew_message and not is_hebrew(chat_response):
            chat_response = translate_text(chat_response, "iw")

    except Exception as e:
        st.error(f"Failed to return message: {e}")
        chat_response = f"Failed to return message: {e}"

    notification.answer(chat_response)

st.success("All required environment variables are set!")
st.write("Bot is ready to run.")

# New code for single-run bot using filelock
LOCK_FILE = Path(__file__).parent / ".bot_lock"
lock = FileLock(LOCK_FILE)

def run_bot_once():
    try:
        with lock.acquire(timeout=1):
            st.write("Bot is starting...")
            bot.run_forever()
    except Timeout:
        st.write("Bot is already running in another instance.")

if __name__ == "__main__":
    run_bot_once()