from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Optional,Dict,List
import g4f.Provider
from bingart import BingArt
import uuid
import g4f, json,os
import logging
import shutil
import threading
import time
import re
import requests
import base64
from datetime import datetime, timedelta
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio
from g4f.client import AsyncClient
from g4f.Provider import OpenaiChat,Gemini,GeminiPro
import uuid


# ユーザーIDとブロック終了時間のマッピング
blocked_users = {}

last_prompt = {}

# Define a dictionary to store the request count for each IP
request_count = defaultdict(int)

# Define a dictionary to store the time of the last request for each IP
last_request = defaultdict(datetime.now)

# Define the maximum number of requests per second for each IP
max_requests_per_second = 6

# Define the ban duration
ban_duration = timedelta(hours=1)

last_comment = {}






g4f.debug.logging = True  # Enable debug logging
g4f.debug.version_check = False  # Disable automatic version checking


logging.basicConfig(level=logging.INFO)

Token = "1fLiqsoxS1kQ2nqDgwS1sYdWQcyNWDADy63_OEuf5QenAxE7Gg0iu9YYoMHVgPDXbpn4gJez8ke2nOqhifrv2cO6o833JNpQcxxjxpel_5UpdkbhkBKvrdVQyK-gjLY70lFZmPCTxgp-1ADoR0eWh8RAv-6s7OpJXPUOvdct1nppQ-x4x6gFuEjhEyph-Xhn1IJgTxsoK-Wy2gC_OhaW1yg"
os.environ["BING_COOKIES"] = "SRCHUSR=DOB=20240116&T=1714006033000&TPC=1714006031000&POEX=W;_Rwho=u=d&ts=2024-04-25;ai_session=At4+ChJVF0LD87KpP8DdPH|1714006025247|1714006025247;SRCHHPGUSR=SRCHLANG=ja&IG=244C454B3BE946D5954941A280D15109&BRW=S&BRH=S&CW=1040&CH=602&SCW=1402&SCH=264&DPR=1.5&UTC=540&DM=0&PV=15.0.0&WTS=63849602833&HV=1714006811&PRVCW=1040&PRVCH=602&CIBV=1.1694.0&cdxtone=Precise&cdxtoneopts=h3precise,clgalileo,gencontentv3&CMUID=35379CE37E9F69BE35EF8F767FE56895;ANON=A=649D3D6D20A7AC222A3CF3D5FFFFFFFF&E=1db0&W=1;MicrosoftApplicationsTelemetryDeviceId=d7843aa6-84d4-4812-8bb0-464314296234;_SS=SID=1C92891F69116D3725E49D7368406CC1&R=2508&RB=2508&GB=0&RG=0&RP=2508;ipv6=hit=1714010411829;dsc=order=Video;_U=1-3KDP5zuUL89eDUMA7PpxaGgKEiWDOUNDCBUMG--ejjSBaNNIZUyBljuGuTzN9X_FsafyiZT1dxkYyOr9TvQnPNp3JR6AakWhuAKiFRrzDfdgjnkK_5c2gHpCTdVYJIICHBFZErGtJ-M1sC6ucA1YAifM_iZxWs_er-CQdO9LvAnImqkquw-zuExs8S3EPZu41gt5qquJ2cGcf1TE6cMoQ;SRCHD=AF=NOFORM;PPLState=1;NAP=V=1.9&E=1d0a&C=ULVVHYtoRXv7AAfOV0LwSdbczxJbzaZliNSbu6J_GBMUOvykmJE4eg&W=1;BFBUSR=CMUID=35379CE37E9F69BE35EF8F767FE56895;_RwBf=r=0&ilt=5&ihpd=2&ispd=0&rc=2508&rb=2508&gb=0&rg=0&pc=2508&mtu=0&rbb=0.0&g=0&cid=&clo=0&v=4&l=2024-04-24T07:00:00.0000000Z&lft=0001-01-01T00:00:00.0000000&aof=0&ard=0001-01-01T00:00:00.0000000&rwdbt=0001-01-01T16:00:00.0000000-08:00&o=0&p=BINGTRIAL5TO250P201808&c=MY01Z9&t=3904&s=2022-12-16T04:28:10.3614922+00:00&ts=2024-04-25T01:00:20.7471736+00:00&rwred=0&wls=2&wlb=0&wle=0&ccp=2&lka=0&lkt=0&aad=0&TH=&rwflt=0001-01-01T16:00:00.0000000-08:00&mta=0&dci=1&e=QoclB8e2sddv2GffMFHbXbey7veb7h31d0b99dlmxFF270knav1wc-kfxi82EEyd-At9a4ANfRbcpdarCcMBKd_GH3jVBPFayIID_Qeg0Eg&A=649D3D6D20A7AC222A3CF3D5FFFFFFFF&cpt=0;_UR=cdxcls=0&QS=0&TQS=0;_EDGE_S=SID=1C92891F69116D3725E49D7368406CC1&mkt=ja-jp;_C_ETH=1;MUIDB=35379CE37E9F69BE35EF8F767FE56895;USRLOC=HS=1&ELOC=LAT=38.261199951171875|LON=140.89187622070312|N=%E4%BB%99%E5%8F%B0%E5%B8%82%E3%80%81%E5%AE%AE%E5%9F%8E%E7%9C%8C|ELT=4|;_HPVN=CS=eyJQbiI6eyJDbiI6NiwiU3QiOjAsIlFzIjowLCJQcm9kIjoiUCJ9LCJTYyI6eyJDbiI6NiwiU3QiOjAsIlFzIjowLCJQcm9kIjoiSCJ9LCJReiI6eyJDbiI6NiwiU3QiOjAsIlFzIjowLCJQcm9kIjoiVCJ9LCJBcCI6dHJ1ZSwiTXV0ZSI6dHJ1ZSwiTGFkIjoiMjAyNC0wNC0yNVQwMDowMDowMFoiLCJJb3RkIjowLCJHd2IiOjAsIlRucyI6MCwiRGZ0IjpudWxsLCJNdnMiOjAsIkZsdCI6MCwiSW1wIjoxNCwiVG9ibiI6MH0=;ak_bmsc=B0CB872657E78C69D7F684CB0BCDA34D~000000000000000000000000000000~YAAQwXcyFzWboumOAQAA4oK4EhfHrfOPIrkRT6k4ZvJl4u+2rYCufLPvXSVfJX1kJuKRbU/7Bi2hT2XVJqGRpnWSGuw8J+F0FCJnc7yS1+tJknRh7W4LBTJoObM4eMnsGrNDK5x7f5YjFh5e4tffi6qB0vcf30fCan5z8CBX2G1mukqkgt9mrSNj53G07ayhVjda6ioZkUNJAoyYgk7tHlpqwNvL70k9WGP6DdE4SXbtMGi/V2C1gIYdcA0I8PBLFc6A7Z2j66mnBhzLc5OEvlmjvL1l17MVc652pc1apXZ6W4ooEoKPJLp+xM0ZOlSjezuMfE8ZXZVou+9bbDVTQhxEmbNFjg9Ep/di33wA9bHgys3bOpteIUqnujRpGOhi4Q2EcLbWKy8=;KievRPSSecAuth=FABaBBRaTOJILtFsMkpLVWSG6AN6C/svRwNmAAAEgAAACHTHrQgl6Hv4GAQksU2im9moce25Lm5n2KoVCaC9P94JY/t6qRYKt8qyKkTkvY51Vf+JdbZt4lSYLYRJoWfQyKiVLjY3vc9fIMklu/4xAzs1/Udz/ZYZMjVetyu/CcOTtbm1pJoilR+CVJ4hrL8JaIGzKpVjX+quGoAukPR8q+E/7IHc0QqPvUjZpz6yC+Flz+Mqc7/QhNThrVy62WSHVz2XaUYmCgaCI75aVC1lsKgD7dPf4j7CSuU/N6L6Os6u7bCB1k30ufv/4ZzuyVYncQNHJL9hlRx0Uj2BkZfzW0NBoptm1Me9NNzIAnnxL6Cn8PvtSoUSQFD4az/vOGOHoLzGJougcXz5Siq6y8rWpF1qblUww8EHS4iHO9m9ZTfGCcQ0tDCF53rCvJt52g4mP9Xa4f+CAZIvf3v6WEovchvMzpsIQ+f8SjpGUToQeV7DYRVk7EzV8+KVb2tooLhT+ih8MtloUXgJI2vv/6jQNLYJQAb9i8J+f8+7lZEsQSROto2F55u9zryR3GjIX8vt9EQIjeU5YYtOOLEd/B3Ao10g246Do3kL1zX/IRka65G3OOcZlHHuVwjLXQZH2uCIvTdx84epba0ukaZsemu3HGTuHXrE2Nl2A6kNPiOKIOY3KYwGGlImsq3Tam26t9AHvHWQgN1TQ5nMFTMZPLwNeA4qFyA22EgZGqTRdsuc+yh5XUxSKQu+SKh4fSIwUgDZ1Wqo7jmsjsMl19QzNYYrH124isKDCs7hR86Yx1udao9G8sEdkg7DR5dnsHoojyvpkUSeQdmV8y53CgutqLejJj7KW5asQ8Jn+QsfthIhmatfkMIpKDlRrNEc11qNfVNKo+Ga7VFQdb77nteya2DfiVRIMVjeRNKxaQjEmnGcirZtzw3MSxR8hXsYrnPAwEx9jbV/aiA+5z+FT5mpGJWaiuwQkW4NLTGDpZkeOT6DRFDtjvbilE7r/JnG8CB63AqRUhMUfeAn8pUUmLrUhn7aRiLx8iUu8hg/8OVWjchy2PApcKDjgJlygg4/2HJQesj3WdzUfYps/4jf6N8xwyRlmX6d/BbR2+4iknTdi96wOVN+vPuYSwfrINdNp6NcNlpKqtkfKg2nF3UpwIMnMheVD/vU2q/5pVlVNh40zxLk6oHFVjkeaw0TQQHQWZjUXvZd7lTh2khJ31Q463BdQSFP4lIqT8142rjLqI4Ewal1RgZc+pfwT7sAGimSmOVuhjDsYhOChj6EmBIFOb4jus7xX/HTqEH6NfIGcK/bFHrCmAGbBYCTqWRJuo1+7hGJeMVbPS9S4wY3MHcE/YXgOgSqZUEbl4zJPSH/DhVWdoyLBHkGyEeveiCHjyH85OQotPH9Q9bgbHLgf7x+tyD4JUqVjsWPiagS0KKXiMio3+RCXNCFmKTlFADAJqICnOAAJdTbigmlVbpVXIgFOg==;MSCCSC=1;MUID=35379CE37E9F69BE35EF8F767FE56895;SRCHUID=V=2&GUID=502D4593A4C24362AF72887B5D96CC3C&dmnchg=1;WLID=BIUZnBVQJAft9EMWSy31xj6dTlH/8OJ89vBt7KZII+keBAlhyBwRtgRcn7Y2Rrk4ZrDt7Ho7rJoygTPuZBe7v3SNy8ZNjm536A7PXv3OZl8=;WLS=C=48fb86083bf470c3&N=jp"
Kiev_cookies = 'FABaBBRaTOJILtFsMkpLVWSG6AN6C/svRwNmAAAEgAAACD1+oAq+j1C3GARTMaPEYoMT8s1UgavpEQPQyIR7wpqbqajGLOyLIQyyTkjly+nOyVpPjIsV5yPYsWD1eP9viiiNLZxs/FN35U1G4DyIy1y9B6/XVG8s32Epr76fehg+6gdIHKfqKjs7I+4hlSrWvggd299+iA6XOfo2ehrETPoSX1ho0VeD5YZ9ZKLv/SsMQmYigqLXQksNynmNG/Z+8fslP2Y2GsG0tZmlDEMaizixQ+Fgq2ACo9wapmDVbGv43jEjCSM9UM8W6R+WV2ACYYfOqbQPQ3R68RfH2qekX/qJNHf7YDo45zyN0Eo7LxoxeWvxAkFJxRHqhU2Q/P5QoCzOgb8I6/Pwy0J65VRLAoyz17N1HBxeBEhO2RNDe7fmHReTPiew2KtrHXOYa+MoLSvMn40PbSdG17V4HObZXcFPTz+PWpmzNvldWbkbtaryReyqswP1TK0QxS5OFders4B9+K8IRcKvd0b4YPagDuMsxAsgWGdiITkCzLodrJHnz6ExSq+PCGuvOHn8bQaRoqpTEG05tkM+thNpA3yjVxCe841gLEdi2++SRMOyDCURS/XlNxYtDsFpfSmk5xQvxn/AZHNzmlpLiNCnKwSEjQcYrf7s5v4UhKi71uavuHU07cJSiQoS0P0I/0BHH9fte7Urss0/i6LhIqu4fg0brN2awkWiUbHKXDrwVa1pclEugJR3up0VOgA5+EDC0HlkD/kECU4Rw7up9zYtd3ejrtyi9Cb+iTYqrQbUqddtMZ9bD3SXN4zdtAaPN1xEPgafXbEHZ6r63qr4itwQzMKMhi9oZFS6DJWxAw7sptXSTGGM90nCEr5VEIzhTauQDFDYqvLYsm70F48nBTmSHOvI9ZHXKS8v8RfRsjTzPOd7B1M/rIEONNq41iNbq04hzB7vLZPErzTjV7cJjSkjZKTkk/UHCX65cpLT4DnPKzjz64TBfb3/lqDf/2jkRwY7CWWuf3emWmDnyl2JdY7KIT5qc1bCz0CoMwV1nOGUbdTojkun/9jHeiRJhotjLqj0hTQS+xjci493ULgaIQegcdT2vraT7sgzPX4HshtEGXdQZXYncgzhYRN+DJaMUviuf58PCpTVatvMMz2kEuv9Gb0dbRj6lTZzwdJDJ6KN5zOx7AQLCqnKSGjKqYJtc+9FaTOa++BjqpiEjeT/iFCB95PFK2Mw8r1Uof16vpkhAIh+KkGxqPYZlwH2QA6zNsK/yNmfq+8GzuG6ImEhmd9pa+q+HAR3VAz/9YBKujNwuZf13cphL8GVWLzsciDJU0U5751XPUQykDvHakgmBol4nHNUdkyAyvSvdkK4ibN/WMO075WG3NeE+ZBLl5l3IruWPe0Tc5mbG6iWa9Ogojk9VF/rBN1GMwBUJ/0BmqXyQT1rM2/ot0EsFAA+5wBls+EEmkVpUsjScKYCajUwkw=='


app = FastAPI()


app.mount("/home", StaticFiles(directory="home"), name="home")



with open('cookies.json', 'r') as file:
    data = json.load(file)

cookies={}
for cookie in data:
    cookies[cookie["name"]] = cookie["value"]




    




# Set up logging to console
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[logging.StreamHandler()])

def cleanup_directories(root_dir, delay):
    while True:
        now = time.time()
        for dir in Path(root_dir).iterdir():
            if dir.is_dir() and re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', dir.name) and now - dir.stat().st_mtime > delay:
                shutil.rmtree(dir)
        time.sleep(delay)

# Start the cleanup task in a separate thread
threading.Thread(target=cleanup_directories, args=('.', 5*60)).start()

@app.get('/')
def home(request: Request):
    templates = Jinja2Templates(directory="templates")
    return templates.TemplateResponse("index.html", {"request": request})

geminis = {}

conversations = {}


@app.get('/ask')
async def ask(request: Request):
    text = request.query_params.get('text')
    user_id = request.query_params.get('user_id') or request.client.host

    if not text:
        return JSONResponse(content={"response": "No question asked"}, status_code=200)

    # 同じコメントが繰り返し使われていないかチェック
    if user_id in last_comment and text == last_comment[user_id]:
        return JSONResponse(content={"response": "同じコメントは連続して使用できません"}, status_code=400)

    # 最後のコメントを更新
    last_comment[user_id] = text

    # ユーザーがブロックされているかどうかをチェック
    if user_id in blocked_users and datetime.now() < blocked_users[user_id]:
        return JSONResponse(content={"response": "ご利用のIPから大量のリクエストを検知した為1時間はアクセスできません"}, status_code=429)

    # リクエストカウントと最後のリクエスト時間を更新
    request_count[user_id] += 1
    last_request[user_id] = datetime.now()

    # リクエスト数が一定の値を超えた場合、ユーザーを一時的にブロック
    if datetime.now() - last_request[user_id] < ban_duration and request_count[user_id] > max_requests_per_second:
        blocked_users[user_id] = datetime.now() + timedelta(hours=1)



    messages = [{"role":"user", "content": text}]

    try:
        response = await g4f.ChatCompletion.create_async(
            model="gemini-pro",
            provider=GeminiPro,
            api_key="AIzaSyBW0t8wOZ5n59RmO0n_NF8zAww-uhBaWnU",
            messages=messages,
        )
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        # If the ask function fails, return an error message
        response = g4f_gemini(text)
        return JSONResponse(content={"response": str(e)}, status_code=500)

    try:
        decoded_response = json.loads(json.dumps(response))
    except json.decoder.JSONDecodeError:
        error_message = "Invalid JSON response"
        logging.error(f"{error_message}: {response.text}")
        return JSONResponse(content={"error": error_message}, status_code=500)

    return JSONResponse(content=decoded_response, status_code=200)




# ユーザー識別子をキーとして会話履歴とそのタイムスタンプを保存する辞書
conversation_histories: Dict[str, List[Dict[str, str]]] = {}

async def chat_with_OpenAI(user_id: str, prompt: str):
    # ユーザー識別子がなければUUIDで新たに作成
    if not user_id:
        user_id = str(uuid.uuid4())

    # ユーザー識別子に対応する会話履歴を取得、なければ新たに作成
    conversation_history = conversation_histories.get(user_id, [])

    # ユーザーのメッセージを会話履歴に追加
    conversation_history.append({"role": "user", "content": prompt})

    conversation_history = conversation_history[-5:]

    client = AsyncClient(
        provider=OpenaiChat,
    )

    response = await client.chat.completions.create(
        model="text-davinci-002-render-sha",
        messages=conversation_history,
    )

    # アシスタントの応答を会話履歴に追加
    conversation_history.append({"role": "assistant", "content": response.choices[0].message.content})

    # 更新した会話履歴を保存
    conversation_histories[user_id] = conversation_history

    return response.choices[0].message.content

    
async def g4f_gemini(prompt: str):
    current_directory = os.getcwd()
    file_path = os.path.join(current_directory, 'cookies.json')
    
    with open(file_path, 'r') as file:
      data = json.load(file)

    api={}
    for cookie in data:
       api[cookie["name"]] = cookie["value"]

    
    response = await g4f.ChatCompletion.create_async(
        model="gemini",
        provider=g4f.Provider.Gemini,
        api_key={"__Secure-1PSID","g.a000jAg-IYqJSUD3qzpCORsRCvwVFnd9RXqZod2n442jcW3nxwWqx4xi4AtXOv1gej18LgO1dQACgYKAScSAQASFQHGX2MiztZO4gM5nLCe0dM2Z30OYRoVAUF8yKrqr4sz-5jtJapa1fEQ_wno0076"},
        cookies=api,
        messages=[{"role": "user", "content": prompt}],
    )
    return response

@app.get("/chat")
async def chat(request: Request,prompt: str):
    user_id = request.query_params.get('user_id') or request.client.host

    if not prompt:
        return JSONResponse(content={"response": "No question asked"}, status_code=200)

    # 同じコメントが繰り返し使われていないかチェック
    if user_id in last_comment and prompt == last_comment[user_id]:
        return JSONResponse(content={"response": "同じコメントは連続して使用できません"}, status_code=400)

    # 最後のコメントを更新
    last_comment[user_id] = prompt

    # ユーザーがブロックされているかどうかをチェック
    if user_id in blocked_users and datetime.now() < blocked_users[user_id]:
        return JSONResponse(content={"response": "ご利用のIPから大量のリクエストを検知した為1時間はアクセスできません"}, status_code=429)

    # リクエストカウントと最後のリクエスト時間を更新
    request_count[user_id] += 1
    last_request[user_id] = datetime.now()

    # リクエスト数が一定の値を超えた場合、ユーザーを一時的にブロック
    if datetime.now() - last_request[user_id] < ban_duration and request_count[user_id] > max_requests_per_second:
        blocked_users[user_id] = datetime.now() + timedelta(hours=1)

    response = await chat_with_OpenAI(user_id,prompt)
    return {"response": response}


@app.get("/gemini")
async def gemini(request: Request,prompt: str):
    user_id = request.query_params.get('user_id') or request.client.host

    if not prompt:
        return JSONResponse(content={"response": "No question asked"}, status_code=200)

    # 同じコメントが繰り返し使われていないかチェック
    if user_id in last_comment and prompt == last_comment[user_id]:
        return JSONResponse(content={"response": "同じコメントは連続して使用できません"}, status_code=400)

    # 最後のコメントを更新
    last_comment[user_id] = prompt

    # ユーザーがブロックされているかどうかをチェック
    if user_id in blocked_users and datetime.now() < blocked_users[user_id]:
        return JSONResponse(content={"response": "ご利用のIPから大量のリクエストを検知した為1時間はアクセスできません"}, status_code=429)

    # リクエストカウントと最後のリクエスト時間を更新
    request_count[user_id] += 1
    last_request[user_id] = datetime.now()

    # リクエスト数が一定の値を超えた場合、ユーザーを一時的にブロック
    if datetime.now() - last_request[user_id] < ban_duration and request_count[user_id] > max_requests_per_second:
        blocked_users[user_id] = datetime.now() + timedelta(hours=1)

    response = await g4f_gemini(prompt)
    return {"response": response}









    
@app.get("/generate_image")
async def generate_image(request: Request, prompt: Optional[str] = None):
    user_id = request.query_params.get('user_id') or request.client.host

    if not prompt:
        return JSONResponse(content={"response": "No question asked"}, status_code=200)

    # 同じコメントが繰り返し使われていないかチェック
    if user_id in last_prompt and prompt == last_prompt[user_id]:
        return JSONResponse(content={"response": "同じコメントは連続して使用できません"}, status_code=400)

    # 最後のコメントを更新
    last_prompt[user_id] = prompt

    # ユーザーがブロックされているかどうかをチェック
    if user_id in blocked_users and datetime.now() < blocked_users[user_id]:
        return JSONResponse(content={"response": "ご利用のIPから大量のリクエストを検知した為1時間はアクセスできません"}, status_code=429)

    # リクエストカウントと最後のリクエスト時間を更新
    request_count[user_id] += 1
    last_request[user_id] = datetime.now()

    # リクエスト数が一定の値を超えた場合、ユーザーを一時的にブロック
    if datetime.now() - last_request[user_id] < ban_duration and request_count[user_id] > max_requests_per_second:
        blocked_users[user_id] = datetime.now() + timedelta(hours=1)

    # Ensure a prompt was provided
    if prompt is None:
        return JSONResponse(content={"error": "No prompt provided"}, status_code=400)
    
    bing_art = BingArt(auth_cookie_U=Token, auth_cookie_KievRPSSecAuth=Kiev_cookies)
    results = bing_art.generate_images(prompt)

    # 画像URLをbase64に変換
    images_base64 = []
    for image in results['images']:
        response = requests.get(image['url'])
        image_base64 = base64.b64encode(response.content).decode('utf-8')
        images_base64.append(image_base64)

    # base64に変換した画像を含むJSONを返す
    return JSONResponse(content={"images": images_base64})




