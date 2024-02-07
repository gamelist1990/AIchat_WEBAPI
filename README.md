# Chatgpt/webapi

## 使用方法

### ①
https:/8trs.onrender.comにアクセスすることで使用する事が可能です。

### ②
WEBAPIですので、以下のようにRequestsを送る事で使用できます。ただエンドポイントの形式がask?text=コメントという感じになっています。

```python
import requests

url = "https://webapi-8trs.onrender.com/ask"

while True:
      ask = input("コメント :")
      ai = {"text": ask }
      response = requests.get(url, ai)
      print(response.json())
```
Requestsを送る事で使用できます。ただエンドポイントの形式がask?text=コメントという感じになっています</p>
<br>
## ③ インストール方法
まず<a href="https://github.com/Gamelist2023/api.git">https://github.com/Gamelist2023/api.git</a>でクローンしてください<br>それが出来たら開き`beta.py`を起動してくださいこれで基本的には完了です後は`Templates`に入っている`index.html`を少し変えたり出来ますCSSやJSは`home`フォルダに入っています
## ④ アクセス方法
起動するとfastAPIのサーバがhttp://0.0.0.0:5000 で起動しますもしhttp接続できない場合にはmain.pyでflaskサーバーを起動することでも大丈夫です(パフォーマンス面ではfastAPIの方が上)
## ④ カスタム方法
<a href="https://github.com/xtekky/gpt4free">https://github.com/xtekky/gpt4free</a>を見てくれ！<br>向こうの方がドキュメンテーションが豊富です少しだけ弄るなら<code>provider=g4f.Provider.Aura</code>の部分の<code>.Aura</code>を<code>.Bing</code>にしたりしてプロバイダーを変えるぐらいですまぁおすすめはこのままで良いと思いますけどあと画像生成ですがTokenの部分はBingの<code>_U</code>cookieですもし画像生成が機能しなくなった場合<a href="https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm">https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm</a><br>で拡張機能機能をいれて<br>次に<a href="https://copilot.microsoft.com/">https://copilot.microsoft.com/</a>に移動しログインしますログイン出来たら先程インストールした拡張機能を選択して<code>ALLsite</code>を選択しますそしてサーチのところに<code>_U</code>と入れ<code>Value</code>の部分をコピーしてTokenに貼り付けます

