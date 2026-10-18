from google import genai
from keys import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)
response = client.interactions.create(
    model="gemini-3.8-flash",
    input="Say hello in five words.")
print(response.output_text)