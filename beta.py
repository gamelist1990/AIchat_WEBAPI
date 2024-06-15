import asyncio
from fastapi import FastAPI, File, Form, Request,HTTPException, Response, UploadFile
from fastapi.concurrency import run_in_threadpool
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
from g4f.Provider import OpenaiChat,Gemini,You,Bing,GeminiProChat,Reka
import uuid
import psutil,socket
import platform
from g4f.cookies import set_cookies, set_cookies_dir, read_cookie_files
from APIandCookes import *


cookies_dir = os.path.join(os.path.dirname(__file__), "har")
set_cookies_dir(cookies_dir)
read_cookie_files(cookies_dir)


conversation_histories: Dict[str, List[Dict[str, str]]] = {}


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

Token = Bing_U
Kiev_cookies = Bing_Kiev





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
     client = AsyncClient(
        provider=g4f.Provider.HuggingChat,
        cookies=set_cookies_dir(cookies_dir),
    )
     
     response = await client.chat.completions.create(
        model="CohereForAI/c4ai-command-r-plus",
        messages=messages,
    )
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        # If the ask function fails, return an error message
        response_error = f"(追記：6/11時点Response 500が返されるというエラーが起きています)HuggingChatプロバイダーでエラーが発生しましたエラー内容:"
        return JSONResponse(content={"response": response_error+str(e)}, status_code=500)

    try:
         ai_response = response.choices[0].message.content
         remove_string = "\u0000"
         clean_response = ai_response.replace(remove_string, "")
         decoded_response = json.loads(json.dumps(ai_response))
    except json.decoder.JSONDecodeError:
        error_message = "Invalid JSON response"
        logging.error(f"{error_message}: {ai_response}")
        return JSONResponse(content={"error": error_message}, status_code=500)

    return JSONResponse(content={"response": decoded_response}, status_code=200)



async def geminipro(user_id: str, prompt: str):
    # ユーザー識別子がなければUUIDで新たに作成
    if not user_id:
        user_id = str(uuid.uuid4())

    # ユーザー識別子に対応する会話履歴を取得、なければ新たに作成
    conversation_history = conversation_histories.get(user_id, [])

    # ユーザーのメッセージを会話履歴に追加
    conversation_history.append({"role": "user", "content": prompt})

    # 最新の5つのメッセージのみを保持
    conversation_history = conversation_history[-5:]
    conversation_histories[user_id] = conversation_history

    try:
        client = AsyncClient(
            provider=GeminiProChat,
            #api_key=read_cookie_files(cookies_dir),  # 正しい関数名に修正
        )
        response = await client.chat.completions.create(
            model="default",
            messages=conversation_history,
        )
        return response.choices[0].message.content  # 正常な応答を返す
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        return "GeminiProのプロバイダーでエラーが発生しました。何度も起きる場合はServerERRORのため管理者に連絡してください。"  # エラーメッセージを返す







# 会話履歴を保持する辞書は関数の外で定義

async def chat_with_OpenAI(user_id: str, prompt: str):
    # ユーザー識別子がなければUUIDで新たに作成
    if not user_id:
        user_id = str(uuid.uuid4())

    # ユーザー識別子に対応する会話履歴を取得、なければ新たに作成
    conversation_history = conversation_histories.get(user_id, [])

    # ユーザーのメッセージを会話履歴に追加
    conversation_history.append({"role": "user", "content": prompt})

    # 最新の5つのメッセージのみを保持
    conversation_history = conversation_history[-5:]
    conversation_histories[user_id] = conversation_history

    try:
        client = AsyncClient(
            provider=g4f.Provider.OpenaiChat,
            api_key=read_cookie_files(cookies_dir),  # 正しい関数名に修正
        )
        response = await client.chat.completions.create(
            model="auto",
            messages=conversation_history,
        )
        return response.choices[0].message.content  # 正常な応答を返す
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        return "OpenAIのプロバイダーでエラーが発生しました。何度も起きる場合はServerERRORのため管理者に連絡してください。"  # エラーメッセージを返す

    


chatlist = {}  # 全ユーザーの会話履歴を保存する辞書


async def g4f_gemini(user_id: str, prompt: str):
    # ユーザー識別子がなければUUIDで新たに作成
    if not user_id:
        user_id = str(uuid.uuid4())
    try:
        client = AsyncClient(
            provider=Gemini,
            api_key=read_cookie_files(cookies_dir),
        )
        response = await client.chat.completions.create(
            model="gemini",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content  # 正常な応答を返す
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        return f"Geminiプロバイダーでエラーが発生しました: 何度も起きる場合はServerERRORの為管理者に連絡してください"  # エラーメッセージを返す

    

async def reka_core(user_id: str, prompt: str):
    if not user_id:
        user_id = str(uuid.uuid4())
    try:
        client = AsyncClient(
            provider=Reka,
            api_key=read_cookie_files(cookies_dir),
        )
        response = await client.chat.completions.create(
                model="reka",
                messages=[{"role": "user", "content": prompt}],
            )
        
        ai_response = response.choices[0].message.content
        remove_string = ["(Translation:", "<sep"]
        clean_response = ai_response
        for string in remove_string:
            clean_response = clean_response.split(string, 1)[0]
        return clean_response
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        return f"Bingプロバイダーでエラーが発生しました: 何度も起きる場合はServerERRORの為管理者に連絡してください"  # エラーメッセージを返す


async def lianocloud(user_id: str, prompt: str, system: str):
    if not user_id:
        user_id = str(uuid.uuid4())
        
    try:
        client = AsyncClient(
            provider=g4f.Provider.Liaobots,
            auth=Li_auth,
        )
        response = await client.chat.completions.create(
                model="claude-3-opus-20240229",
                systemPrompt=system,
                messages=[{"role": "user", "content": prompt}],
            )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        return f"Liaobotsプロバイダーでエラーが発生しました: 何度も起きる場合はServerERRORの為管理者に連絡してください"  # エラーメッセージを返す

AI_prompt = "あなたは有能なAIです"


async def process_chat(provider: str, user_id: str, prompt: str, system: str = AI_prompt):
    if provider == 'OpenAI':
        response = await chat_with_OpenAI(user_id, prompt)
    elif provider == 'Gemini':
        response = await g4f_gemini(user_id, prompt)
    elif provider == 'GeminiPro':
        response = await geminipro(user_id, prompt)
    elif provider == 'Reka':
        response = await reka_core(user_id, prompt)
    elif provider == "Claude3":
        response = await lianocloud(user_id, prompt, system)
    else:
        return JSONResponse(content={"error": "Invalid provider specified"}, status_code=400)

    return JSONResponse(content={"response": response})




@app.get("/chat")
async def chat(request: Request, provider: str, prompt: str, system: str = AI_prompt):
    user_id = request.query_params.get('user_id') or request.client.host
    if not user_id:
        user_id = str(uuid.uuid4())

    if not prompt:
        return JSONResponse(content={"response": "No question asked"}, status_code=200)
    
    if not system:
         system = AI_prompt


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

    return await process_chat(provider, user_id, prompt, system)













    
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
