from g4f.client import Client
from g4f.cookies import set_cookies_dir, read_cookie_files
import g4f.debug
import g4f
import os,json
from g4f.Provider import OpenaiChat,HuggingChat,Blackbox,You,Liaobots,Bing,Reka
import uuid

g4f.debug.logging = True  # Enable debug logging
g4f.debug.version_check = True  # Disable automatic version checking

cookies_dir = os.path.join(os.path.dirname(__file__), "har")

client = Client(
        provider=Reka,
        api_key=read_cookie_files(cookies_dir),
    )

response = client.chat.completions.create(
    model="reka",
    messages=[{"role": "user", "content": "こんにちは自己紹介をおねがい！"}]
)

# Get the AI's response
ai_response = response.choices[0].message.content

# Define the string to be removed
remove_string = ["(Translation:", "<sep"]

# Remove the string from the AI's response
#clean_response = ai_response.replace(remove_string, "")

clean_response = ai_response
for string in remove_string:
    clean_response = clean_response.split(string, 1)[0]

print(clean_response)
