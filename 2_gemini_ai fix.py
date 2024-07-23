"""
Install the Google AI Python SDK

$ pip install google-generativeai

See the getting started guide for more information:
https://ai.google.dev/gemini-api/docs/get-started/python
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Create the model
# See https://ai.google.dev/api/python/google/generativeai/GenerativeModel
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

system_instruction = """
Kamu adalah asisten dari IMAM SIBRO MUHLISI. Namamu adalah ASISTEN MASBRO. 
Gunakan bahasa Indonesia dengan baik dan benar. Tugasmu adalah untuk membantu orang-orang dalam kesehariannya. 
Utamakan berbahasa Indonesia yang baik dan benar. 
Gunakan bahasa inggris jika user menyapa kamu dengan bahasa inggris.
"""

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  # safety_settings = Adjust safety settings
  # See https://ai.google.dev/gemini-api/docs/safety-settings
  system_instruction=system_instruction,
)

history = []

while True:
    user_input = input("You : ")

    chat_session = model.start_chat(history=history)

    response = chat_session.send_message(user_input)

    model_response = response.text
    print(f'Bot : {model_response}')

    history.append({"role": "user", "parts": [user_input]})
    history.append({"role": "model", "parts": [model_response]})