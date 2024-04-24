from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Optional
from g4f.image import ImageResponse
from sydney import SydneyClient
from bingart import BingArt
from g4f.client import AsyncClient
from g4f.Provider import BingCreateImages, OpenaiChat, Gemini



import g4f, json,os
import logging
import shutil
import threading
import time
import re
import uvicorn
import aiohttp
import requests
import base64






g4f.debug.logging = True  # Enable debug logging
g4f.debug.version_check = False  # Disable automatic version checking


logging.basicConfig(level=logging.INFO)

Token = "1kq8Cw0JJczZOGPVBoG1emr07Kdvt1i0Y41AB1w8W9Adu4Wq_4Drw-6YWdTW3Uaa0Zo8kxPyKGdJ2fCYH9D8MdV1Omuk7sn5bfE17KgTPUv2PpOrtPEOgUbvItPazK0LBKmRnnMfmjHHfWLnmXN1fkrsyTx66eoYNXYRAl5mynl89qW3UMjgaFRgF6G3gSlfjPU076cCezjG055Lfo3XOPw"
os.environ["BING_COOKIES"] = Token
Kiev_cookies = 'FABiBBRaTOJILtFsMkpLVWSG6AN6C/svRwNmAAAEgAAACPH/YHuWsJZPIAT98NjQvd0xcUUZHgyZki9koQDZHALHT325kvDP9lWO0oHex5Buu8UM3DsM/7CAwldWx5IkxO0OJD72+gpqEmPTz5BcCF4IEiqyg20MNcmQaGzMWM+pcLFLpWlWa6rn3/NhCkvPD6gUBAjGSMmhL0XOUmnopznBl8lHFaG9Db66Q8kjFDORbQgx12hn8SqKkcdkmVuifMpJw2xYGkvV/F48WSo0fC7Ma+F649QI6h86Xw8uuC0bWV0niufLnUT1UttC9k2QjsfR/RKcIPAeO4iDfJ8E9BhOesq1kKpsg/YTZK0cjvgYgXnJZlSPkjHgT/Ay2YZpLDYdxFq9gM0Cy4d6c37Bi7z29dqV8jRrYlIt78qTQS3bxRSyzTMDujqXcOLPz0slQjmxKooc/6WBxVtEtrruab9hjdDVPPkT6+ByeBizuHLrgMW0RK4sYbYUWEURu6FG8lIOeWaAUuF6fNC0KK4MTZm28ZIYrMDYZHvtya37UIQ0s5C9vm27Oogy1y/2wVd/GE+T/gBxaZK2gEDAF87tu6Wi4l1xd7o9vFrGfg0MrsCLJF/UZ2A3GQ+u9gd4/38FssQH6rBm09cX1yTqrOa5zRSRyzL8Ga75+nbutQ7Q8qa7pmDCv35C6goNzfdmoxV24ngAIwQ5BFcvYTAtwqILclHsw8A3M+H4i2BP1lvKgPf2MxT4BACxovmDnDCfzhn2m4muT/l54vrEj4QW5TvsW/gSEdh41P84+Qa2Cu961WGgGlbXT7GPlNvHtmWltuJoX8JQl/CmGfYQLu3xNmCGGxf0krf814bTOaTuBt4iLMpB7A8AnnyfU2vOBIRRWYpvsK4CVFyb29XbTataPI72KQdC1KxAvTfV/pygcuIM8VhqBNsGpuZKLHV3bBom7X+3nI7kZ3Vub0Mh3wZTtcLDzxCOmULqXNIPhtKoeRFsini7C65w4xYq7sMnWKfNOXiE7tIIMrrn1nx0aBrHIFEj6JzhqXRwVqopMIqt4Z/MCTF7fhtxqkwak9h1NqkvucfVDRqNnE5cr96KA/loPRozGUF08TyyOsAm16b9O0hi9bcMMXnrhrJ6WmNXtjujgfZhRPtpdjDBZOXjsB7//qbitrtfPPghb5KEBUP3uD/03mB35DMYk0ytw32l0EcFAPKFrfvgYakycSPwqB3PrqK6YhcCyrBVxbtRcF7rdhszDeCLBn4gj+arO+p3hCrU7LHy2uW3Npav5eEmUai8j5W+JLsnWEniTFDdsxTHv3olFcNM3QGDKMEqdOlb92LiJReLtqZxY+K1Q0a3RHMAtkF1npLAKU3R3P7K9+cxoUVYqNvSAMlooDxI6dKkIkJ5iiRGmDnyZVCd4vwQ0OdkiRum2s/I9VNfCK4P9hQrBzjCNPq9n3QAsg2X5eiFb3MUANSUxObIAahQX/q96X0INmxtBGRx'


app = FastAPI()

app.mount("/home", StaticFiles(directory="home"), name="home")

with open('cookies.json', 'r') as file:
    data = json.load(file)

cookies={}
for cookie in data:
    cookies[cookie["name"]] = cookie["value"]




# Initialize the conversation history
    




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

    if user_id not in conversations:
        conversations[user_id] = []

    conversations[user_id].append({"role":"user", "content": text})
    
    # Limit the conversation history to the last 5 messages
    conversations[user_id] = conversations[user_id][-5:]
    
    messages = conversations[user_id]
    try:
        response = await g4f.ChatCompletion.create_async(
            model="gemini-pro",
            messages=messages,
            provider=g4f.Provider.GeminiPro,
            api_key="AIzaSyBW0t8wOZ5n59RmO0n_NF8zAww-uhBaWnU"
        )
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        # If the ask function fails, call the chat function
        response = await chat_with_sydney(text)
        return JSONResponse(content={"response": response}, status_code=200)

    try:
        decoded_response = json.loads(json.dumps(response))
    except json.decoder.JSONDecodeError:
        error_message = "Invalid JSON response"
        logging.error(f"{error_message}: {response.text}")
        return JSONResponse(content={"error": error_message}, status_code=500)

    return JSONResponse(content=decoded_response, status_code=200)


async def chat_with_sydney(prompt: str):
    async with SydneyClient() as sydney:
        response = ""
        async for res in sydney.ask_stream(prompt):
            response += res
        return response

@app.get("/chat")
async def chat(prompt: str):
    response = await chat_with_sydney(prompt)
    return {"response": response}








    
@app.get("/generate_image")
async def generate_image(prompt: Optional[str] = None):
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




