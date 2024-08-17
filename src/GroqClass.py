import os
import random
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class GroqClass:
    def __init__(self, api_key):
        """
        Initialize the GroqClass with the provided Groq API key.
        
        :param api_key: Groq API key as a string.
        """
        self.api_key = api_key
        self.client = Groq(api_key=api_key)
        self.groq_models = os.getenv('GROQ_MODEL', '').split(',')
        
        print("GroqClass initialized with provided API key.")
        # print(f"Available models: {', '.join(self.groq_models)}")

    def send_prompt(self, user_message, system_message, model=None, max_tokens=256, temperature=0.3):
        """
        Send a prompt to the Groq API and get a response.
        
        :param user_message: Message from the user.
        :param system_message: Message from the system.
        :param model: Model to use for the completion (if None, uses the first model in the shuffled list).
        :param max_tokens: Maximum number of tokens to generate.
        :param temperature: Sampling temperature.
        :return: Response from the Groq API or False if an error occurs.
        """
        # print(f"Start: groq send_prompt(user_message={user_message})")
        # print(f"temperature: {temperature}")
        try:
            random.shuffle(self.groq_models)
            # print(f"Available models: {', '.join(self.groq_models)}")

            if model is None and self.groq_models:
                selected_model = self.groq_models[0]
            elif model == "random" and self.groq_models:
                selected_model = random.choice(self.groq_models)
            else:
                selected_model = model or "llama3-70b-8192"  # Fallback model if none specified
            
            print(f"Using model: {selected_model}")

            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_message
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                model=selected_model,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                stop=None
            )
            # Access the response content correctly
            result = response.choices[0].message.content.strip()
            print(f"Success: Received response from Groq API.")
            return result
        
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

# Usage example
if __name__ == "__main__":
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("API key not found. Please set the GROQ_API_KEY environment variable.")
    else:
        groq_instance = GroqClass(api_key=api_key)
        user_msg = "Hello, how can you help me today?"
        system_msg = "You are a helpful assistant."
        response = groq_instance.send_prompt(user_msg, system_msg)
        if response:
            print(f"Groq API Response: {response}")
        else:
            print("Failed to get a response from the Groq API.")