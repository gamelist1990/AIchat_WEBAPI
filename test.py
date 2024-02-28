from g4f.client import Client
from g4f.Provider.GeminiPro import GeminiPro


comment = input("comment :")
client = Client(
    api_key="AIzaSyDHCVkGkQ0d5lQ230ssHzf3rg2XZBjNCZM",
    provider=GeminiPro
)

response = client.chat.completions.create_async(
    model="gemini-pro",
    messages=[{"role": "user", "content": comment}],
)
print(response.choices[0].message.content)