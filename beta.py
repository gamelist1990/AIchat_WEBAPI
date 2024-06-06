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
import g4f.Provider
from g4f.client import AsyncClient
from g4f.Provider import OpenaiChat,Gemini,You,Blackbox
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

#support model

openAI = "OpenAI"
gemini_normal = "Gemini"
blackbox_normal = "BlackBox"



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
        provider=g4f.Provider.HuggingChat,
        model="CohereForAI/c4ai-command-r-plus",
        api_key=set_cookies_dir(cookies_dir),
        messages=messages,
    )
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        # If the ask function fails, return an error message
        response = f"現在HuggingChatプロバイダーでエラーが発生しましたエラー内容:{str(e)}"
        return JSONResponse(content={"response": str(e)}, status_code=500)

    try:
        ai_response = response
        remove_string = "#### Please log in to access GPT-4 mode. \n\n#### For more information, check out our YouPro plan here: https://you.com/plans.\n\nAnswering your question without GPT-4 mode:"
        clean_response = ai_response.replace(remove_string, "")
        decoded_response = json.loads(json.dumps(clean_response))
    except json.decoder.JSONDecodeError:
        error_message = "Invalid JSON response"
        logging.error(f"{error_message}: {response.text}")
        return JSONResponse(content={"error": error_message}, status_code=500)

    return JSONResponse(content={"response": decoded_response}, status_code=200)






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

    try:
        client = AsyncClient(
        provider=OpenaiChat,
        api_key=set_cookies_dir(cookies_dir),
        )
        response = await client.chat.completions.create(
        model="auto",
        messages=conversation_history,
        )

    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        response = "OpenAIのプロバイダーでエラーが発生しました(何度も起きる場合：サーバー側のエラーの可能性があります)"
        return response
    
    

    

    

    conversation_history.append({"role": "assistant", "content": response.choices[0].message.content})

    # 更新した会話履歴を保存
    conversation_histories[user_id] = conversation_history

    return response.choices[0].message.content


chatlist = {}  # 全ユーザーの会話履歴を保存する辞書


async def g4f_gemini(user_id: str, prompt: str):
    # ユーザー識別子がなければUUIDで新たに作成
    if not user_id:
        user_id = str(uuid.uuid4())

    # ユーザー識別子に対応する会話履歴を取得、なければ新たに作成
    #conversation_history = chatlist.get(user_id, [])
    # ユーザーのメッセージを会話履歴に追加
    #conversation_history.append({"role": "user", "content": prompt})

    #conversation_history = conversation_history[-5:]

    try:
        response = await g4f.ChatCompletion.create_async(
        provider=Gemini,
        api_key=read_cookie_files(cookies_dir),
        model="gemini",
        messages=[{"role": "user", "content": prompt}],
    )
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        response = f"Geminiプロバイダーでエラーが発生しました:何度も起きる場合はServerERRORの為管理者に連絡してください"
        return response
    

async def blackbox(user_id: str, prompt: str):
    if not user_id:
        user_id = str(uuid.uuid4())
    try:
        response = await g4f.ChatCompletion.create_async(
        provider=Blackbox,
        api_key=read_cookie_files(cookies_dir),
        model="default",
        messages=[{"role": "user", "content": prompt}],
    )
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")


        response = "BlackBoxプロバイダーでエラーが発生しました:何度も起きる場合はServerERRORの為管理者に連絡してください"
        return response
        

   
    
    
    #conversation_history.append({"role": "assistant", "content": response})

    # 更新した会話履歴を保存
    #chatlist[user_id] = conversation_history

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

    return JSONResponse(content={"response": response})





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
    return JSONResponse(content={"response": response})


@app.get("/blackbox")
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


    response = await blackbox(user_id,prompt)

    return JSONResponse(content={"response": response})












    
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
