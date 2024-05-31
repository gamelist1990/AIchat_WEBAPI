from fastapi import FastAPI, Request,HTTPException
from fastapi.responses import JSONResponse,FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Optional,Dict,List
from bingart import BingArt

import g4f
import json
import os
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
from g4f.client import AsyncClient
from g4f.Provider import OpenaiChat,Gemini,You
import uuid
import psutil,socket
import platform
from g4f.cookies import set_cookies, set_cookies_dir, read_cookie_files



cookies_dir = os.path.join(os.path.dirname(__file__), "har")
set_cookies_dir(cookies_dir)
read_cookie_files(cookies_dir)




# ユーザーIDとブロック終了時間のマッピング
blocked_users = {}

last_prompt = {}

# Define a dictionary to store the request count for each IP
request_count = defaultdict(int)

# Define a dictionary to store the time of the last request for each IP
last_request = defaultdict(datetime.now)

# Define the maximum number of requests per second for each IP
max_requests_per_second = 10

# Define the ban duration
ban_duration = timedelta(hours=1)

last_comment = {}

conversation_history = {}
chatlist = {}

start_time = datetime.now()

# ロガーの設定


# ファイルハンドラの設定
handler = logging.FileHandler('console.log')
handler.setLevel(logging.INFO)


#
# ログファイルをクリアする時間間隔（分）
interval = 30

# 次にログファイルをクリアする時間
next_clear_time = datetime.now() + timedelta(minutes=interval)


with open('cookies.json', 'r') as file:
    data = json.load(file)

cookies={}
for cookie in data:
    cookies[cookie["name"]] = cookie["value"]









g4f.debug.logging = True  # Enable debug logging
g4f.debug.version_check = False  # Disable automatic version checking


logging.basicConfig(level=logging.INFO)

Token = "1Hg2irr_sM-seogXWY1X7SO0pO8OLMFe8wT9q42-WhDclPBVeTu0mMYhFa-RnDBl2q3rIl5lMW7f4Go4ZxQK_n0hcUbhxA94ifrEKviVG3k-NlK5_V5GJRyELVjX1fj3USYblstCFy3UjaknV3CPN5qJjYxLY_gmzJzlJj-XX8Sysrx72g9CvetbX0kTMVeUp0-tnzPRuWlBArYob_8iqKg"
Kiev_cookies = 'FABaBBRaTOJILtFsMkpLVWSG6AN6C/svRwNmAAAEgAAACGkveRq4YHiQGASQ7W8nVBTG3f34MKwATSDfhwqz2bdfD7QeDEq1JcomqPED5pjQt1a+1pE+oojpz0n5my5tp0PonwY+n/+cMtjBt04c+BT6PYHAnsbze5iNHEuwC0jwzuS8vE7UJCngqK9X0CVPGf1HL66J3ckR7ydiQJSqnfHx/YTUmBcgbiaK1S/ytbS3RWe+nnsk6NcEvGSKVRprl4luQmET+O1CrDpHNwrRcFtWUnDzRKPKXvXuv8y7G0nDnyWvkF1iV402PVNXq9VQhQWwJM+qzbNe/vzKc4ZHtLEI4B4EOmHD08ldm0Fb+qbDQhMqa13QZCojLIqESa2mTR9FA2woiQfXvjPywBsyAZkxoAVWWOIggQi7PTx4y5d7NepkAno6iSD6irSsPYuAMRJDm0sSA+CiWEpL5y8dDfioRv3lwZdzzhyw3tgsK5rZwdjBjXGM3HC/YAB5pI7t5PdOpbiaZf+ziTalOUswTGWW93QbAzJvEgt4GEMlljLeAIhVmdgyW+DC7iMvMCYnFGT7E/uZTtAABq2WLrLjq5bfGdWNyJ8XtJSVUik7l2yoHMdqiOdkaKYejkRHajaTKcVYesOtAbHxrgKDxIXAkqqx37v/n4bC2dcwdNX6XcbXuf0hIQUOY20TMeh/p49jm0UzqJx2Sk4CAE8gu9o8d2PuJpb5F60IaCMaJ39jriKu5W/ZsPRGY0qNz4+zJT3Paz9fc6yBZubLxIBkcRM+JAs5BipPUy8G8upbvvhRsjJAAZbKGX68+HFmjURRrfyyMIdXeK3VVbYxZRVlsqQTb/4tvkUgTCQ2xXPC9l3nfxXuTqZpet3snsfhksPFtXi+44arrTp5tSufH16lrfVEi78J0KLdGqeCEKK/KUMMqS95ykco0VbK/vXd5hJD3qw1M5yoivrH8+h1p0usjIlTL5jZKDfQYxjfFWOQ+q9GSwgY70yeQChqoKVT67wkj9UUK7pUCR+o0CoWPVRsF/dnrC1reGDQ9wFWsZNZDndr4JxNdYn//yHMjEVVJihGnI3Y5W8ujVq6GnIWRr+naLsAAWHJoOtiVQsSiPdDvgrf2bS+azoJW7y+STuBmGfh54pIXwhRoPXmaE0UCLUkQghO8Z8lFBjgTzTnGcFoV5KRzV5trsOssa0JMTKGxXmOqxMVUacvEn/KEdpeltVxz5+LNQHaWhJubBjTLkAtLkUpa7HDPIQYn7pIG5JOsVRO8Spr5IBTRqgQYy5z8V0DDskMYMbvjCFqGCetBOiGYzQalDGu3iNm54Hxf89IlvUkLbZSM1jR9DLO2tZXsRoJDQpyX7T4jYDqmjm18B+/2TfidRwkwD4fXdFtVK4eocoSqpN570SjxaB+iWuZlMIV1Wu3LcHh+5T9PIO8EA/REX0ZbPXIIPoTFAAVCusrvdhIVoo/buCKkwh1b+5PHA=='

os.environ["BING_COOKIES"] = "_C_Auth=; MUID=262B60ED062C67BD345B7462075F6633; MUIDB=262B60ED062C67BD345B7462075F6633; SRCHD=AF=NOFORM; SRCHUID=V=2&GUID=1C4CEAA879734DEBA1C162B8989CE8E3&dmnchg=1; _UR=cdxcls=0&QS=0&TQS=0; MicrosoftApplicationsTelemetryDeviceId=a7756597-fb03-4946-ad1a-eb6b1a37f614; MSCCSC=1; ANON=A=649D3D6D20A7AC222A3CF3D5FFFFFFFF&E=1dd3&W=1; NAP=V=1.9&E=1d79&C=EVRh5EfVVv29bUfdA3L6s30mR7pqaFCoGgVSmHKEfjkVcF8r7BSjGQ&W=1; PPLState=1; KievRPSSecAuth=FABaBBRaTOJILtFsMkpLVWSG6AN6C/svRwNmAAAEgAAACGVfarnCKQ0gGASak54ERA4+WqgYFQ/JXRfuPDYV2LgWMKwwQbsxnIEVjyF4kqWVqF5wY6YdP8SSCX8lP9VF7M7h2jkP/qZo0V7VrLsKr102hnlzQcEFXBjv4iHQqh8fAtIXcfdgLfhXBiJK4gsqgz4eJKiwfwg6L84kNElQlSkRZgtnXZw2T64xoDfb5P3pOhGN9lBWT4B9dTinMsi6Re4kxTxSYz2yJvW3vxPvPaqsiS+Nb8WcIz8vDWg2y8Lbz2+RanFgnE9XB3m/1pV+FdHV+7IMhRasHoWmXXVOpxWo9ujXI9CRxjiaEz+fm9zV2FkUpdXzPtoLsUOOA5AB34/1AKLWQvMk9c8XOdQK9TbjjNYxiUNmqcBa9/C1QtoPbesffKTzcHEwQZRN4Gcld49cdUuXKRab5OTthBkWObOk4YyWvwZm6p5biPZLF9hR0lrs8NhYFOE1pWv/AjPbauzAOnaF6FuRn8jpAiINBIKJ1gNfOOup1BpY523zcshck6Dw2np9IqX2WDbSWry6EtEMUC6NPr6NLBaod7l09U4oGQKfDrTX8Cd+1V6qRE79Msc0hRSLGWpoZ+tm8oQI0b40SqtL5Dt0uqnoV8oeqM5MO2djU9ml0x/acFXYj/YjLM/QWcf7tupR48h3QApSytI0FDAMnbvx5ETOw9b8SxsSrdpkDl9MvmdEsDWAU4Pp/Dda2fcg8oJsOC/6yLri9T2wNMDIF2oY+8JSCjFy9JU2Cx3cXrhnPHSxAWwGL+gSH/RcCVByZWx+LgoanYf527oa0eiB+Wvvs726e1kui2i+IEUZF2ST19WRsfjqUBNcuMKudpkupArXofMGDNElMwBg+8RMNTUi2HldnwsyxlzKURt4WfMv7uGGcQznJrHy9IwdE1hXX188bASpSpS2aqPmLdGmcJkSztUqnL4m35wwC5iuwWQYIZaN2kDJBSddESpFlfmNXXWbz3Bbeoa8ksh9IsLZ69F3H5sTrcvk1+zdLC0tjK8hIy8WeWsKPevP9gZzaZK6dgazW1pLlM2hmmBpR55maMm6ZLuSMAomvAim+pIm0Dn1sYGg94Xc3wMpSdqZD/2gW3tL5Ys4wy99sAcH6euXqDiMa+qsgE1yfNLOtioSUg3FDf/L0g11IGSknLjCSls1CZagPW10gSRHSm6UZFYkiU/8oRLrneYMcR2XSuSj4BH0iS33dLinQE/XmOHXMx5hio8FKjRXK2rVNZZJzPBeH2ev8xSMm4o+BUKdW8eO4QWS5GvOJkZOlru1MkZ6x2++561X2tzxf0RfOBhMGYazcmCc+w6ZRkgAqHf90hYBIzyMpgf98TIhmYjDBp7GLv1chZZYA8jPzao4AwREwhEocI5g06zWtWK9U9+jL9s/ra4iybvnhxzlArAzhvFNFACfpdcaMZlCG5l89u4KyUtGFEMS7g==; _U=1ADoFkpeJzNChANGRk_u4tEezTUuNhI7tomStPDhU-Mo9vL3oHdPuudEP72pztyzfr0qXkXKCntUlf9-s5MwFP7DkHITX4axITqlQ24SIlBPVlWLGzENRhiNKZTQoqhu5AhysBtm8FnXg2FziVNXmc9ULjYAKUD5B6oY6la6xDSgtG0W0-EUZi4GLrGKlksUp5qBiPWnBRwyYC3XJ6YPi6A; MUIDB=262B60ED062C67BD345B7462075F6633; _EDGE_S=SID=3B52AC0A16B7663C339DB89A17DF67AB; WLS=C=48fb86083bf470c3&N=jp; ak_bmsc=4EA7CB3FDF5A782802B133866678E43D~000000000000000000000000000000~YAAQH8zVF+DcvLuPAQAAc4l4zRcxEu15QYhWtHvx7nFj37Tfa3rz0awwV2+B8WpLftfeKsPH8pMS8rakqJvO7TAjo88rdPTxgXu9Lzb2FXvOoVdFIrVfMTScArWL89JeaO3ZNoSB8XRHrKsfIIQ0o5vK48AyR5jv5o7hkPlvFVjFsmcRLPZ/ME60ZaPY6gea+9juHjHXpOy44q9WOLWPIbf2yjxQ+vW6WsurGbObzbYHJ9IDbvrd2FAY2aNAJ1zWqr9NF+yJ6cTB81rvwN96GGkxlCh5bYuraTZZeQhR8fiPPOvTmpB1cwQVZjRMro4EGaa+blyvfzma+J5u+nu/0hbONplPBzTc+z36FCH5Kq0lK9CTMWCzuIfhg0tzFf9jN9capg40tqIUp4KMm3cMwztKjwRiOCeceaEuaYYGiNA=; WLID=tHrtDXXyJq+VzfxRDyvEp8C1CUQyv2WPNe6NW15IyVkjDatCQxa+0dnTFFIGJ7Uv; ai_session=oPcrd2OVTD+J/zPgSSocwV|1717139185059|1717139185059; _Rwho=u=d&ts=2024-05-31; _SS=SID=3B52AC0A16B7663C339DB89A17DF67AB&R=2867&RB=2867&GB=0&RG=0&RP=2867; ipv6=hit=1717142785670&t=6; _HPVN=CS=eyJQbiI6eyJDbiI6MiwiU3QiOjAsIlFzIjowLCJQcm9kIjoiUCJ9LCJTYyI6eyJDbiI6MiwiU3QiOjAsIlFzIjowLCJQcm9kIjoiSCJ9LCJReiI6eyJDbiI6MiwiU3QiOjAsIlFzIjowLCJQcm9kIjoiVCJ9LCJBcCI6dHJ1ZSwiTXV0ZSI6dHJ1ZSwiTGFkIjoiMjAyNC0wNS0zMVQwMDowMDowMFoiLCJJb3RkIjowLCJHd2IiOjAsIlRucyI6MCwiRGZ0IjpudWxsLCJNdnMiOjAsIkZsdCI6MCwiSW1wIjoxMCwiVG9ibiI6MH0=; bm_sv=D89FBEB185DA6D6568A87DFA43C41907~YAAQH8zVFx3dvLuPAQAA2Mh4zRfEpZ6MbsXcpeDaJcYkbdJ1XdcygIpiJp2NtmD1xB9FCYR2vxfBuKEX970zGO0Cd+AQ47aXTwl07j+5ivjwoVCfKDyWe53uV0GKtB0+eIFMLzm6y+n/ERiSWBrHIeAuRo8/GXcmLnYr9Le5CU77JHIC96CIbxjXBAwkEwlumiz9D+9UwitXoJFV+nk+reu9iLNVq2Kd2407qO3vfPqQ7Lhvw/b4BWcs/VHpQQ==~1; SRCHUSR=DOB=20240530&T=1717139179000&TPC=1717139199000&POEX=W; _C_ETH=1; _RwBf=r=0&ilt=3&ihpd=2&ispd=0&rc=2867&rb=2867&gb=0&rg=0&pc=2867&mtu=0&rbb=0.0&g=0&cid=&clo=0&v=3&l=2024-05-31T07:00:00.0000000Z&lft=0001-01-01T00:00:00.0000000&aof=0&ard=0001-01-01T00:00:00.0000000&rwdbt=0001-01-01T16:00:00.0000000-08:00&rwflt=2024-05-28T21:33:36.5825753-07:00&o=0&p=BINGTRIAL5TO250P201808&c=MY01Z9&t=3904&s=2022-12-16T04:28:10.3614922+00:00&ts=2024-05-31T07:20:11.4713275+00:00&rwred=0&wls=2&wlb=0&wle=0&ccp=2&cpt=0&lka=0&lkt=0&aad=0&TH=&mta=0&e=QoclB8e2sddv2GffMFHbXbey7veb7h31d0b99dlmxFF270knav1wc-kfxi82EEyd-At9a4ANfRbcpdarCcMBKd_GH3jVBPFayIID_Qeg0Eg&A=; SRCHHPGUSR=SRCHLANG=ja&IG=F576A684961D4EE7AD02B1AB3C2E510B&BRW=S&BRH=M&CW=1035&CH=868&SCW=1402&SCH=221&DPR=1.5&UTC=540&DM=0&PV=15.0.0&HV=1717140024&WTS=63852636149&PRVCW=1035&PRVCH=868&CIBV=1.1760.0&cdxtone=Balanced&cdxtoneopts=galileo,fluxhinttr"
app = FastAPI()



app.mount("/home", StaticFiles(directory="home"), name="home")





    




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
        model="gpt-3.5-turbo",
        messages=conversation_history,
    )
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        # If the ask function fails, return an error message
        response = "不明"
        return JSONResponse(content={"response": str(e)}, status_code=500)

    try:
        decoded_response = json.loads(json.dumps(response))
    except json.decoder.JSONDecodeError:
        error_message = "Invalid JSON response"
        logging.error(f"{error_message}: {response.text}")
        return JSONResponse(content={"error": error_message}, status_code=500)

    return JSONResponse(content={"response": decoded_response}, status_code=200)





# ユーザー識別子をキーとして会話履歴とそのタイムスタンプを保存する辞書

async def chat_with_OpenAI(user_id: str, prompt: str):
    conversation_histories: Dict[str, List[Dict[str, str]]] = {}

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
        api_key=set_cookies_dir(cookies_dir),

    )

    response = await client.chat.completions.create(
        model="auto",
        messages=conversation_history,
    )

    # アシスタントの応答を会話履歴に追加
    conversation_history.append({"role": "assistant", "content": response.choices[0].message.content})

    # 更新した会話履歴を保存
    conversation_histories[user_id] = conversation_history

    return response.choices[0].message.content


chatlist = {}  # 全ユーザーの会話履歴を保存する辞書



chatlist = {}

async def g4f_gemini(user_id: str, prompt: str):
    # ユーザー識別子がなければUUIDで新たに作成
    if not user_id:
        user_id = str(uuid.uuid4())

    # ユーザー識別子に対応する会話履歴を取得、なければ新たに作成
    conversation_history = chatlist.get(user_id, [])
    # ユーザーのメッセージを会話履歴に追加
    conversation_history.append({"role": "user", "content": prompt})

    conversation_history = conversation_history[-10:]

   
    response = await g4f.ChatCompletion.create_async(
        provider=Gemini,
        api_key=read_cookie_files(cookies_dir),
        model="gemini",
        messages=conversation_history,
    )
    
    conversation_history.append({"role": "assistant", "content": response})

    # 更新した会話履歴を保存
    chatlist[user_id] = conversation_history

    return response




@app.get("/chat")
async def chat(request: Request,prompt: str):
    user_id = request.query_params.get('user_id') or request.client.host
    if not user_id:
        user_id = str(uuid.uuid4())

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
    if not user_id:
        user_id = str(uuid.uuid4())

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

    response = await g4f_gemini(user_id,prompt)
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



def clear_log():
    global next_clear_time
    # 現在の時間が次のクリア時間を超えていたらログファイルをクリア
    if datetime.now() >= next_clear_time:
        with open('console.log', 'w') as f:
            f.truncate(0)
        next_clear_time = datetime.now() + timedelta(minutes=interval)

def execute_command(command):
    result = os.popen(command).read()  # コマンドを実行し、結果を取得します
    with open('console.log', 'a') as f:
        f.write(result)  # 結果をconsole.logに保存します

def show_status():
    # CPU使用率を取得
    cpu_usage = psutil.cpu_percent(interval=1)
    # メモリ使用率を取得
    memory_usage = psutil.virtual_memory().percent
    # 起動時間を取得
    boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    # OSバージョンを取得
    os_version = platform.system() + " " + platform.release()
    # Pythonバージョンを取得
    python_version = platform.python_version()
    # グローバルIPアドレスを取得
    global_ip = socket.gethostbyname(socket.gethostname())
    # 状態情報を辞書として保存
    status_info = {
        "CPU使用率": f"{cpu_usage}%",
        "メモリ使用率": f"{memory_usage}%",
        "時間": boot_time,
        "OS": os_version,
        "Pythonバージョン": python_version,
        "グローバルIPアドレス": global_ip,
    }
    return status_info  # 状態情報をJSON形式で直接返す

def check_files():
    directory = os.getcwd()
    files = os.listdir(directory)
    return json.dumps(files, ensure_ascii=False)

def change_name(old_name: str, new_name: str):
    if os.path.splitext(old_name)[1] != os.path.splitext(new_name)[1]:
        raise HTTPException(status_code=400, detail="拡張子の変更は許可されていません")
    os.rename(old_name, new_name)

def help_menu():
    help_pass = 'パスワードを記載します例：console?password=xxx これだけだとconsole.logが表示されます' 
    help_cmd = 'コマンドを実行します例：console?password=xxx&command=pip list これでpyの依存関係が表示されます'
    help_status = 'ステータスを表示します例：console?password=xxx&status=show これでサーバーの状態が表示されますよ'
    help_checkfile = 'ディレクトリをチェックできますただ整理していないので少し見にくいですけど'
    help_changename = 'このパラメータはファイル/フォルダの名前を変えるやつです例：testファイルがあると仮定：console?password=xxx&old_name=test&new_name=HELLO という感じにoldに古い名前/newに新しい名前を入れてください'
    help_show = 'このパラメータではファイルの内容を見れますバイナリ系は無理です例：console?password=xxx&show=ファイル名'

    help_info = {
        "使い方": "管理者用",
        "password": help_pass,
        "command": help_cmd,
        "status": help_status,
        "checkfile": help_checkfile,
        "changename": help_changename,
        "show": help_show,
    }
    return help_info

@app.get("/console")
async def console(password: str, command: str = None, status: str = None,menu:bool=False, checkfile: bool = False, old_name: str = None, new_name: str = None, show: str = None):
    if password != 'admin/@gamelist1990':
        raise HTTPException(status_code=401, detail="Unauthorized")
    else:
        clear_log()
        if command:
            execute_command(command)
        elif status and status == 'show':
            return show_status()
        elif checkfile:
            return {"files": check_files()}
        elif menu:
            return {"HELP": help_menu()}
        elif old_name and new_name:
            try:
                change_name(old_name, new_name)
                return {"message": f"{old_name}名 は {new_name}名 に変更されました"}
            except Exception as e:
                return {"error": str(e)}
        elif show:
            if os.path.exists(show):
                return FileResponse(show)
            else:
                return {"error": "指定されたファイルは存在しません"}
        with open('console.log', 'r') as f:
            console_log = f.readlines()
        return {"console_log": console_log}
    
@app.get("/check")
async def check_device(request: Request):
    client_host = request.client.host
    headers = request.headers
    return {"client_host": client_host, "headers": headers}
