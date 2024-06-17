
import asyncio
import subprocess
from fastapi import BackgroundTasks, Body, FastAPI, File, Form, Request, HTTPException, Response, UploadFile, Header
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Optional, Dict, List
from bingart import BingArt

import gzip
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
from g4f.Provider import OpenaiChat, Gemini, You, Bing, GeminiProChat, Reka
import uuid
import psutil, socket
import platform
from g4f.cookies import set_cookies, set_cookies_dir, read_cookie_files
from APIandCookes import *
from antibot import check_and_ban, ban_user, unban_user, get_ban_history, get_banned_count  # アンチボットシステムの関数をインポート

# 環境変数からパスワードを取得
import os
from dotenv import load_dotenv
from passlib.context import CryptContext

# Pusherのインポート
from pusher import Pusher

load_dotenv()  # .env ファイルから環境変数をロード

server_status = {
    "running": True,
    "stop_message":"サーバーメンテナンス中です"
}

# パスワードハッシュ化の設定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH")

cookies_dir = os.path.join(os.path.dirname(__file__), "har")
set_cookies_dir(cookies_dir)
read_cookie_files(cookies_dir)

conversation_histories: Dict[str, List[Dict[str, str]]] = {}

last_prompt = {}
last_comment = {}
conversation_history = {}

start_time = datetime.now()

# ファイルハンドラの設定
handler = logging.FileHandler('console.log')
handler.setLevel(logging.INFO)

# ログファイルをクリアする時間間隔（分）
interval = 10

# 次にログファイルをクリアする時間
next_clear_time = datetime.now() + timedelta(minutes=interval)

with open('cookies.json', 'r') as file:
    data = json.load(file)

cookies = {}
for cookie in data:
    cookies[cookie["name"]] = cookie["value"]

g4f.debug.logging = True  # Enable debug logging
g4f.debug.version_check = False  # Disable automatic version checking

logging.basicConfig(level=logging.INFO)

Token = Bing_U
Kiev_cookies = Bing_Kiev

app = FastAPI()
templates = Jinja2Templates(directory="templates")  # テンプレートエンジンの設定

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

def read_server_status():
    """loads.jsonからサーバーのステータスを読み込みます。"""
    global server_status
    try:
        with open(os.path.join(os.path.dirname(__file__), "loads.json"), 'r', encoding='utf-8') as f:
            server_status = json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="ファイル 'loads.json' が見つかりません。")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="ファイル 'loads.json' のJSON形式が正しくありません。")
    
read_server_status()

@app.get('/')
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

geminis = {}

@app.get('/ask')
async def ask(request: Request):

    if not server_status["running"]:
        return JSONResponse(content={"response": server_status["stop_message"]})  # 停止メッセージを返す
    
    text = request.query_params.get('text')
    user_id = request.query_params.get('user_id') or request.client.host

    if not text:
        return JSONResponse(content={"response": "No question asked"}, status_code=200)

    # 同じコメントが繰り返し使われていないかチェック
    if user_id in last_comment and text == last_comment[user_id]:
        return JSONResponse(content={"response": "同じコメントは連続して使用できません"}, status_code=400)

    # 最後のコメントを更新
    last_comment[user_id] = text

    # アンチボットシステムでユーザーをチェック
    is_banned, reason = check_and_ban(user_id, request)  # antibot.py の関数を呼び出す

    if is_banned:
        return JSONResponse(content={"response": reason}, status_code=429)

    messages = [{"role": "user", "content": text}]

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
        return JSONResponse(content={"response": response_error + str(e)}, status_code=500)

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

    if not server_status["running"]:
        return JSONResponse(content={"response": server_status["stop_message"]})  # 停止メッセージを返す
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

    # アンチボットシステムでユーザーをチェック
    is_banned, reason = check_and_ban(user_id, request)  # antibot.py の関数を呼び出す

    if is_banned:
        return JSONResponse(content={"response": reason}, status_code=429)

    return await process_chat(provider, user_id, prompt, system)


@app.get("/generate_image")
async def generate_image(request: Request, prompt: Optional[str] = None):
    user_id = request.query_params.get('user_id') or request.client.host

    if not prompt:
        return JSONResponse(content={"response": "No question asked"}, status_code=200)

    # 同じコメントが繰り返し使われていないかチェック
    if user_id in last_prompt and prompt == last_prompt[user_id]:
        return JSONResponse(content={"response": "同じコメントは連続して使用できません"}, status_code=400)
    
    if not server_status["running"]:
        return JSONResponse(content={"response": server_status["stop_message"]})  # 停止メッセージを返す

    # 最後のコメントを更新
    last_prompt[user_id] = prompt

    # アンチボットシステムでユーザーをチェック
    is_banned, reason = check_and_ban(user_id, request)  # antibot.py の関数を呼び出す

    if is_banned:
        return JSONResponse(content={"response": reason}, status_code=429)

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
    """コマンドを実行し、結果をconsole.logに保存します。"""
    result = os.popen(command).read()  # コマンドを実行し、結果を取得します
    with open('console.log', 'a') as f:
        f.write(result)  # 結果をconsole.logに保存します

def show_status():
    """サーバーの状態情報を取得します。"""
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
    # ディスク使用率を取得
    disk_usage = psutil.disk_usage('/').percent
    # ネットワーク情報を取得
    # 状態情報を辞書として保存
    status_info = {
        "CPU使用率": f"{cpu_usage}%",
        "メモリ使用率": f"{memory_usage}%",
        "ディスク使用率": f"{disk_usage}%",
        "時間": boot_time,
        "OS": os_version,
        "Pythonバージョン": python_version,
        "グローバルIPアドレス": global_ip,
    }
    return status_info  # 状態情報をJSON形式で直接返す

def check_files():
    """現在のディレクトリのファイル一覧を取得します。"""
    directory = os.getcwd()
    files = os.listdir(directory)
    return json.dumps(files, ensure_ascii=False)

def change_name(old_name: str, new_name: str):
    """ファイルまたはフォルダの名前を変更します。"""
    if os.path.splitext(old_name)[1] != os.path.splitext(new_name)[1]:
        raise HTTPException(status_code=400, detail="拡張子の変更は許可されていません")
    os.rename(old_name, new_name)

def restart_server():
    """FastAPI を再起動します。"""
    subprocess.run(['python', 'beta.py'], check=True)
    return {"message": "FastAPI を再起動しました。"}

def shutdown_server():
    """FastAPI を停止します。"""
    return {"message": "FastAPI を停止します。"}  # 実行中のプロセスを終了



@app.get("/check")
async def check_device(request: Request):
    client_host = request.client.host
    headers = request.headers
    return {"client_host": client_host, "headers": headers}

@app.post("/admin")
async def admin_console(request: Request, command: str = Form(None), rename: Dict[str, str] = Form(None),show: str = Form(None)): 
    """管理者用コンソールコマンド処理（パスワード認証が必要な操作のみ）"""
    form = await request.form()  # Form dataを取得
    password = form.get("password")

    if pwd_context.verify(password, ADMIN_PASSWORD_HASH):
        # コマンドの実行
        if command:
            return execute_and_log_command(command)

        # ファイル/フォルダの名前変更
        elif rename:
            return rename_file_or_folder(rename["old_name"], rename["new_name"])

        # ファイルの表示
        elif show:
            return show_file(show)

        # コンソールログの表示
        else:
            return get_console_log()

    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

def execute_and_log_command(command: str) -> dict:
    """コマンドを実行し、結果をconsole.logに保存します。"""
    result = os.popen(command).read()
    with open('console.log', 'a') as f:
        f.write(result)
    return {"message": f"コマンド '{command}' を実行しました。"}

def rename_file_or_folder(old_name: str, new_name: str) -> dict:
    """ファイルまたはフォルダの名前を変更します。"""
    if os.path.splitext(old_name)[1] != os.path.splitext(new_name)[1]:
        raise HTTPException(status_code=400, detail="拡張子の変更は許可されていません")
    os.rename(old_name, new_name)
    return {"message": f"{old_name} を {new_name} に変更しました。"}

def show_file(file_name: str) -> str:
    """ファイルを読み込み、内容を文字列として返します。"""
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        return {"error": "指定されたファイルは存在しません。"}
def get_console_log():
    """コンソールログを表示します。"""
    try:
        with open('console.log', 'r') as f:
            console_log = f.readlines()
        return {"console_log": console_log}
    except FileNotFoundError:
        return {"error": "console.log が見つかりません。"}


def read_json_file(file_name):
    """JSONファイルを読み込みます。"""
    file_path = os.path.join(os.path.dirname(__file__), file_name)  # ファイルパスを生成
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"ファイル '{file_name}' が見つかりません。")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail=f"ファイル '{file_name}' のJSON形式が正しくありません。")

def write_json_file(file_name, data):
    """JSONファイルを書き込みます。"""
    file_path = os.path.join(os.path.dirname(__file__), file_name)  # ファイルパスを生成
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ファイル '{file_name}' への書き込み中にエラーが発生しました: {str(e)}")

@app.get("/antibot")
async def antibot_page(request: Request):
    return templates.TemplateResponse("antibot.html", {"request": request})

print(ADMIN_PASSWORD_HASH)
@app.post("/antibot")
async def antibot_login(request: Request):
    form = await request.form()  # JSONデータを取得
    password = form.get("password")  # JSONデータからパスワードを取得

    print(password)

    if pwd_context.verify(password, ADMIN_PASSWORD_HASH):
        # ログイン成功
        # セッショントークンなどを発行する場合はここで行う
        raise HTTPException(status_code=200, detail="OK")
    else:
        # ログイン失敗
        raise HTTPException(status_code=401, detail="Unauthorized")





@app.post("/admin/restart")
async def admin_restart(request: Request):
    form = await request.json()
    password = form.get("password")

    if pwd_context.verify(password, ADMIN_PASSWORD_HASH):
        # サーバーを再起動する代わりに、別のプロセスで実行する
        # 例：`uvicorn main:app --reload`
        subprocess.Popen(['python', 'combined_server.py'], close_fds=True)  # 独立したプロセスで実行 combined_server.pyに変更
        return {"message": "FastAPI を再起動しました。"}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.post("/admin/shutdown")
async def admin_shutdown(request: Request):
    form = await request.json()
    password = form.get("password")

    if pwd_context.verify(password, ADMIN_PASSWORD_HASH):
        # サーバーを停止する代わりに、現在のプロセスを終了する
        # 例：`sys.exit(0)`
        # 適切な方法でプロセスを終了する必要がある
        os._exit(0)  # 現在のプロセスを終了
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.post("/admin/update_json")
async def update_json(request: Request):
    """JSONファイルを更新します。"""
    form = await request.json()  # showfile 関数と同様に JSON をパース
    password = form.get("password")
    file_path = form.get("file_path")  # JSON から file_path を取得
    data = form.get("data")          # JSON から data を取得

    if not pwd_context.verify(password, ADMIN_PASSWORD_HASH):
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        # JSONファイルを読み込み
        file_data = read_json_file(file_path)
        # データを更新
        file_data.update(data)
        # JSONファイルを書き込み
        write_json_file(file_path, file_data)

        return {"message": f"ファイル '{file_path}' を更新しました。"}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JSONファイルの更新中にエラーが発生しました: {str(e)}")
    
@app.post("/admin/showfile")
async def admin_showfile(request: Request):
    """管理者用ファイル表示（リクエストボディからパスワードを取得）"""
    form = await request.json()
    file_name = form.get("file_name")  # form から file_name を取得
    password = form.get("password")

    if pwd_context.verify(password, ADMIN_PASSWORD_HASH):
        file_content = show_file(file_name)
        if isinstance(file_content, dict):  # エラーの場合
            return JSONResponse(content=file_content)
        else:
            return Response(content=file_content, media_type="text/plain")  # ファイル内容をテキストとして返す
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
@app.post("/admin/update_server_status")
async def update_server_status(request: Request, status: str = Form(...)):
    """サーバーのステータスを更新します。"""
    form = await request.form()
    password = form.get("password")
    if not pwd_context.verify(password, ADMIN_PASSWORD_HASH):
        raise HTTPException(status_code=401, detail="Unauthorized")

    global server_status
    if status == "stop":
        server_status["running"] = False
        # service.json から stop_message を取得
        server_status["stop_message"] = read_json_file("loads.json").get("stop_message", "サーバーは停止中です。") 
    elif status == "start":
        server_status["running"] = True
        server_status["stop_message"] = ""  # 稼働中は空文字列
    else:
        raise HTTPException(status_code=400, detail="無効なステータスです。")

    # service.json にサーバーのステータスを書き込む
    with open(os.path.join(os.path.dirname(__file__), "loads.json"), 'w', encoding='utf-8') as f:
        json.dump(server_status, f, indent=4, ensure_ascii=False)

    return {"message": f"サーバーのステータスを{status}に更新しました。"}

@app.post("/antibot")
async def antibot_login(password: str = Form(...)):
    if pwd_context.verify(password, ADMIN_PASSWORD_HASH):
        return {"success": True}
    else:
        return {"success": False}

@app.post("/antibot/unban")
async def antibot_unban(request: Request):
    unban = await request.json()  # JSON データを取得
    user_id = unban.get("user_id")  # JSON から user_id を取得

    if user_id:
        unban_user(user_id)  # antibot.py の関数を呼び出す
        return {"success": True}
    else:
        return {"success": False, "error": "user_id が見つかりません"} 

@app.get("/antibot/history")
async def antibot_history():
    return {"banHistory": get_ban_history(), "bannedCount": get_banned_count()}




# リソース情報の取得
async def get_system_resources_async():
    """システムリソース情報をPusher経由で送信します。"""
    cpu_usage = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    memory_usage = memory.percent
    pusher_client.trigger("private-my-channel", "resources", {'cpu_usage': cpu_usage, 'memory_usage': memory_usage})



@app.post("/admin/console_log")
async def admin_console_log(request: Request):
    """コンソールログをPOSTで返します。"""
    form = await request.json()
    password = form.get("password")

    if pwd_context.verify(password, ADMIN_PASSWORD_HASH):
        console_log = get_console_log()
        if 'error' in console_log:  # エラーがある場合
            return console_log  # エラーメッセージをそのまま返す
        else:
            return JSONResponse(console_log)  # コンソールログをJSONとして返す
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")
    



@app.post("/admin/status")
async def admin_status(request: Request, background_tasks: BackgroundTasks):
    """サーバーの稼働状態とステータス情報をPusher経由で送信します。"""
    form = await request.json()
    password = form.get("password")

    if pwd_context.verify(password, ADMIN_PASSWORD_HASH):
        status_info = show_status() 
        background_tasks.add_task(pusher_client.trigger, "private-my-channel", "server_status", {"data": status_info})
        return JSONResponse({"message": "Server status fetched successfully.", "data": status_info}) # レスポンスにデータを追加
    else:
        raise HTTPException(status_code=401, detail="Unauthorized") 

async def admin_status_server():
    """サーバーの稼働状態とステータス情報をPusher経由で送信します。"""
    status = show_status()
    pusher_client.trigger("private-my-channel", "server_status", {"data": status}) 



async def admin_console():
    consolelog =get_console_log()
    pusher_client.trigger("private-my-channel", "consolelog", {"message": consolelog})  # privateチャンネルに変更


# 定期的にリソース情報を取得・送信
async def periodic_resource_update():
    while True:
        await get_system_resources_async()
        await admin_status_server()
        await asyncio.sleep(2)  # 2秒ごとに更新

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(periodic_resource_update())
# Pusher のインスタンスを作成
pusher_client = Pusher(
  app_id='1820345',
  key='4cbc3c15bfd521142b7a',
  secret='e2c6238a65b9b7ae8603',
  cluster='ap3',
)




# ロガーの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)


@app.post("/pusher/auth")
async def pusher_authenticate(request: Request):
    form = await request.form()
    socket_id = form.get('socket_id')
    channel_name = form.get('channel_name')

    if not socket_id or not channel_name:
        raise HTTPException(status_code=400, detail="Missing socket_id or channel_name")

    # 認証が必要な場合、ここでユーザー認証を行う
    # ...

    # privateチャンネルの場合、認証を行う
    if channel_name.startswith("private-"):
        auth = pusher_client.authenticate(channel=channel_name, socket_id=socket_id)
        return JSONResponse(auth)
    else:
        raise HTTPException(status_code=403, detail="Authentication failed")