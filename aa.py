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
    messages=[{"role": "user", "content": "hello"}]
)

# Get the AI's response
ai_response = response.choices[0].message.content

# Define the string to be removed
remove_string = "#### Please log in to access GPT-4 mode. \n\n#### For more information, check out our YouPro plan here: https://you.com/plans.\n\nAnswering your question without GPT-4 mode:"

# Remove the string from the AI's response
clean_response = ai_response.replace(remove_string, "")

print(clean_response)
