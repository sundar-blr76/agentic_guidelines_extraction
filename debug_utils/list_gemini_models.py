
import google.generativeai as genai
import os

# Assuming the API key is set as an environment variable
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY environment variable not set.")
else:
    genai.configure(api_key=api_key)

    print("Available models:")
    for m in genai.list_models():
      if 'generateContent' in m.supported_generation_methods:
        print(m.name)
