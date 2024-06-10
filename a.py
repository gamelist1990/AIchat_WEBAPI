from g4f.client import Client
from g4f.cookies import set_cookies_dir, read_cookie_files
import g4f.debug
import g4f
import os,json
from g4f.Provider import HuggingChat,OpenRouter,Blackbox,You,Gemini,Bing,Liaobots,HuggingChat
import uuid

g4f.debug.logging = True  # Enable debug logging

cookies_dir = os.path.join(os.path.dirname(__file__), "har")

client = Client(
        provider=HuggingChat,
        api_key=read_cookie_files(cookies_dir),
    )

response = client.chat.completions.create(
    #model="CohereForAI/c4ai-command-r-plus",
    model="CohereForAI/c4ai-command-r-plus",
    messages=[{"role": "user", "content": "your name"}]
)

# Get the AI's response
ai_response = response.choices[0].message.content

# Define the string to be removed
remove_string = ""

# Remove the string from the AI's response
clean_response = ai_response.replace(remove_string, "")

print(ai_response)
