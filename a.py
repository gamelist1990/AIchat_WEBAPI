from g4f.client import Client
from g4f.cookies import set_cookies_dir, read_cookie_files
import g4f.debug
g4f.debug.logging = True
import g4f
import os,json
from g4f.client import AsyncClient
from g4f.Provider import Bing



cookies_dir = os.path.join(os.path.dirname(__file__), "har")

client = Client(
        provider=Bing,
        api_key=read_cookie_files(cookies_dir),

    )
response = client.chat.completions.create(
    model="Balanced",
    messages=[{"role": "user", "content": "Hello"}]
)
print(response.choices[0].message.content)