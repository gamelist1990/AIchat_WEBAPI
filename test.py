import g4f
import json

# ファイルからクッキーデータを読み込む
with open('cookies.json', 'r') as f:
    test = json.load(f)


response = g4f.ChatCompletion.create(
    model=g4f.models.default, # Using the default model
    provider=g4f.Provider.Bing, # Specifying the provider as Gemini
    messages=[{"role": "user", "content": "猫の画像を生成してください"}],
    set_cookies=test
    
)

# Displaying the response
print(response)