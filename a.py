from g4f.client import Client
from g4f.client.async_client import AsyncClient
from g4f.cookies import set_cookies_dir, read_cookie_files
import g4f.debug
import g4f
import os,json
from g4f.Provider import HuggingChat,OpenRouter,Blackbox,You,Gemini,Bing,Liaobots,GeminiProChat,OpenaiChat,HuggingFace,Reka,Koala
import uuid

g4f.debug.logging = True  # Enable debug logging

cookies_dir = os.path.join(os.path.dirname(__file__), "har")

client = Client(
        provider=OpenaiChat,
        api_key=read_cookie_files(cookies_dir),
    )
response =  client.chat.completions.create(
    model="auto",
    messages=[{"role": "user", "content": "自己紹介をおねがいします"}],
    stream=True,
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, flush=True, end="")
