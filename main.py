import os
import json
import re
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from whatsapp_chatbot_python import GreenAPIBot, Notification
from deep_translator import GoogleTranslator

load_dotenv()  # Load environment variables from .env file

required_env_vars = [
    "OPENAI_API_KEY",
    "GREENAPI_ID_INSTANCE",
    "GREENAPI_ACCESS_TOKEN",
    "GROQ_API_KEY"
]

for var in required_env_vars:
    if os.getenv(var) is None or os.getenv(var) == "":
        print(f"{var} is not set")
        exit(1)

bot = GreenAPIBot(os.getenv("GREENAPI_ID_INSTANCE"), os.getenv("GREENAPI_ACCESS_TOKEN"))
openaiClient = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

from src.GroqClass import GroqClass
myGroq = GroqClass(api_key=os.getenv("GROQ_API_KEY"))

def is_hebrew(prompt: str) -> bool:
    return any('\u0590' <= char <= '\u05FF' for char in prompt)

def translate_text(text: str, target_language: str):
    try:
        translated = GoogleTranslator(source='auto', target=target_language).translate(text)
        return translated
    except Exception as e:
        return f"Error occurred during translation: {e}"

MAX_HISTORY_LENGTH = 10

def trim_chat_history(history: list) -> list:
    return history[-MAX_HISTORY_LENGTH:]

def load_chat_history(history_file: str) -> list:
    if os.path.exists(history_file):
        with open(history_file, "r") as file:
            return json.load(file)
    return []

def save_chat_history(history: list, history_file: str) -> None:
    with open(history_file, "w") as file:
        json.dump(history, file)

TEXT_TYPES = ["textMessage", "extendedTextMessage", "quotedMessage"]

@bot.router.message(type_message=TEXT_TYPES)
def txt_message_handler(notification: Notification) -> None:
    print(f"Start: type_message")
    
    try:
        sender_data = notification.event["senderData"]
        user_message = notification.message_text
        chat_id = sender_data["chatId"]
        phone_number = re.sub(r'\D', '', chat_id)        

        DATA_FOLDER = (Path(__file__).parent / "data").resolve()
        output_path = DATA_FOLDER / f'{phone_number}_data.json'        

        if is_hebrew(user_message):
            print("Hebrew")
            user_message = translate_text(user_message, "en")                
        else:
            print("Not Hebrew")
            
        # print(f"English message: {user_message}")
        
        system_message = "You are a sarcastic friend, quick with witty remarks and a playful attitude. Keep your responses concise and to the point."
        chat_history = load_chat_history(output_path)

        chat_history.append(f"User: {user_message}")

        history_prompt = "\n".join(chat_history) + "\n" + f"User: {user_message}"

        chat_history = trim_chat_history(chat_history)

        chat_response = myGroq.send_prompt(history_prompt, system_message, "random")
        
        chat_history.append(f"Bot: {chat_response}")

        save_chat_history(chat_history, output_path)

        if is_hebrew(notification.message_text) and not is_hebrew(chat_response):
            chat_response = translate_text(chat_response, "iw")

    except Exception as e:
        chat_response = f"Failed to return message: {str(e)}"
        print(f"Failed to return message: {str(e)}") 

    # print(chat_response)
    notification.answer(chat_response)

bot.run_forever()