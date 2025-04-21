import openai
from dotenv import load_dotenv
import os
from typing import List

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

class OnboardingChatbot:
    def __init__(self):
        pass

    def generate_prompt(self, history: List[str]) -> str:
        base = "You're a friendly private tutor helping a student get started. Ask questions to fill in missing info like name, country, and score."
        history_text = "\n".join(history)
        return f"{base}\n\n{history_text}\nYou:"

    def chat(self, history: List[str]) -> str:
        print(f"--> Chat history: {history}")  # Log the current history to debug
        prompt = self.generate_prompt(history)

        # Log the prompt for debugging
        print(f"--> Prompt sent to OpenAI: {prompt}")

        try:
            # Correct API call using openai.ChatCompletion.create
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",  # Specify the model
                messages=[
                    {"role": "system", "content": "You're a friendly private tutor helping a student get started."}
                ] + [
                    {"role": "user", "content": message} for message in history  # Adding all user messages
                ]
            )

            # Correctly access the response object using dot notation
            print(f"--> OpenAI response: {response}")  # Log the response for debugging
            return response.choices[0].message.content.strip()  # Corrected access

        except openai.OpenAIError as e:  # Correct exception handling
            print(f"--> OpenAI error: {e}")
            return "Sorry, something went wrong. Please try again later."

        except Exception as e:
            print(f"--> General error: {e}")
            return "Sorry, something went wrong. Please try again later."
