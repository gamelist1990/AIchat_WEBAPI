import logging
import os
import re
import uuid
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
import time

from fastapi.staticfiles import StaticFiles

import g4f
from g4f.client.async_client import AsyncClient
from g4f.cookies import read_cookie_files

app = FastAPI()
app.mount("/home", StaticFiles(directory="home"), name="home")
cookies_dir = os.path.join(os.path.dirname(__file__), "har")

conversation_histories = {}
AI_prompt = "None"


async def chat_with_OpenAI(user_id: str, prompt: str, system: str, streaming: bool = False):
    # ユーザー識別子がなければUUIDで新たに作成
    if not user_id:
        user_id = str(uuid.uuid4())

    # ユーザー識別子に対応する会話履歴を取得、なければ新たに作成
    conversation_history = conversation_histories.get(user_id, [])
    systemmessage = f"System:{system},この内容に従って出力"

    # ユーザーのメッセージを会話履歴に追加
    conversation_history.append({"role": "user", "content": systemmessage + prompt})

    # 最新の5つのメッセージのみを保持
    conversation_history = conversation_history[-5:]
    conversation_histories[user_id] = conversation_history

    try:
        client = AsyncClient(
            provider=g4f.Provider.OpenaiChat,
            api_key=read_cookie_files(cookies_dir),  # 正しい関数名に修正
        )
        if streaming:
            buffer = ""
            async for chunk in client.chat.completions.create(
                model="auto",
                messages=conversation_history,
                stream=True,
            ):
                if chunk.choices[0].delta.content:
                    buffer += chunk.choices[0].delta.content
                    if len(buffer) > 1: # バッファが100文字を超えたらyield
                        buffer = ""
            if buffer: # バッファに残っている文字列があればyield
                yield buffer
        else:
            # 非同期処理
            response = await client.chat.completions.create(
                model="auto",
                messages=conversation_history,
                Stream=True,
            )
            if response.choices[0].delta.content:
                    yield response.choices[0].delta.content  # yield をループ内で実行
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        yield "OpenAIのプロバイダーでエラーが発生しました。何度も起きる場合は他のプロバイダーを使用してください"  # エラーメッセージをyieldします


async def process_chat_stream(provider: str, user_id: str, prompt: str, system: str = AI_prompt):
    streaming = True
    if provider == 'OpenAI':
        async for response in chat_with_OpenAI(user_id, prompt, system, streaming):
            yield f"data: {response}\n\n"  # SSE フォーマットで送信
    else:
        yield JSONResponse(content={"error": "Invalid provider specified"}, status_code=400)


@app.post("/stream")
async def stream(request: Request):
    data = await request.json()
    provider = data.get('provider', "OpenAI")
    prompt = data.get('prompt')
    system = data.get('system', AI_prompt)
    user_id = data.get('user_id', str(uuid.uuid4()))

    if not prompt:
        return JSONResponse(content={"response": "No question asked"}, status_code=200)

    # 文字数制限を設ける
    if len(prompt) > 300:
        return JSONResponse(content={"response": "300文字以内に収めてください"}, status_code=400)

    return StreamingResponse(process_chat_stream(provider, user_id, prompt, system),
                             media_type="text/event-stream")  # media_type を設定