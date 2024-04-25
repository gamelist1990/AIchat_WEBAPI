from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Optional
from g4f.image import ImageResponse
from sydney import SydneyClient
from bingart import BingArt
import uuid



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

Token = "1fLiqsoxS1kQ2nqDgwS1sYdWQcyNWDADy63_OEuf5QenAxE7Gg0iu9YYoMHVgPDXbpn4gJez8ke2nOqhifrv2cO6o833JNpQcxxjxpel_5UpdkbhkBKvrdVQyK-gjLY70lFZmPCTxgp-1ADoR0eWh8RAv-6s7OpJXPUOvdct1nppQ-x4x6gFuEjhEyph-Xhn1IJgTxsoK-Wy2gC_OhaW1yg"
os.environ["BING_COOKIES"] = Token
Kiev_cookies = 'FABaBBRaTOJILtFsMkpLVWSG6AN6C/svRwNmAAAEgAAACD1+oAq+j1C3GARTMaPEYoMT8s1UgavpEQPQyIR7wpqbqajGLOyLIQyyTkjly+nOyVpPjIsV5yPYsWD1eP9viiiNLZxs/FN35U1G4DyIy1y9B6/XVG8s32Epr76fehg+6gdIHKfqKjs7I+4hlSrWvggd299+iA6XOfo2ehrETPoSX1ho0VeD5YZ9ZKLv/SsMQmYigqLXQksNynmNG/Z+8fslP2Y2GsG0tZmlDEMaizixQ+Fgq2ACo9wapmDVbGv43jEjCSM9UM8W6R+WV2ACYYfOqbQPQ3R68RfH2qekX/qJNHf7YDo45zyN0Eo7LxoxeWvxAkFJxRHqhU2Q/P5QoCzOgb8I6/Pwy0J65VRLAoyz17N1HBxeBEhO2RNDe7fmHReTPiew2KtrHXOYa+MoLSvMn40PbSdG17V4HObZXcFPTz+PWpmzNvldWbkbtaryReyqswP1TK0QxS5OFders4B9+K8IRcKvd0b4YPagDuMsxAsgWGdiITkCzLodrJHnz6ExSq+PCGuvOHn8bQaRoqpTEG05tkM+thNpA3yjVxCe841gLEdi2++SRMOyDCURS/XlNxYtDsFpfSmk5xQvxn/AZHNzmlpLiNCnKwSEjQcYrf7s5v4UhKi71uavuHU07cJSiQoS0P0I/0BHH9fte7Urss0/i6LhIqu4fg0brN2awkWiUbHKXDrwVa1pclEugJR3up0VOgA5+EDC0HlkD/kECU4Rw7up9zYtd3ejrtyi9Cb+iTYqrQbUqddtMZ9bD3SXN4zdtAaPN1xEPgafXbEHZ6r63qr4itwQzMKMhi9oZFS6DJWxAw7sptXSTGGM90nCEr5VEIzhTauQDFDYqvLYsm70F48nBTmSHOvI9ZHXKS8v8RfRsjTzPOd7B1M/rIEONNq41iNbq04hzB7vLZPErzTjV7cJjSkjZKTkk/UHCX65cpLT4DnPKzjz64TBfb3/lqDf/2jkRwY7CWWuf3emWmDnyl2JdY7KIT5qc1bCz0CoMwV1nOGUbdTojkun/9jHeiRJhotjLqj0hTQS+xjci493ULgaIQegcdT2vraT7sgzPX4HshtEGXdQZXYncgzhYRN+DJaMUviuf58PCpTVatvMMz2kEuv9Gb0dbRj6lTZzwdJDJ6KN5zOx7AQLCqnKSGjKqYJtc+9FaTOa++BjqpiEjeT/iFCB95PFK2Mw8r1Uof16vpkhAIh+KkGxqPYZlwH2QA6zNsK/yNmfq+8GzuG6ImEhmd9pa+q+HAR3VAz/9YBKujNwuZf13cphL8GVWLzsciDJU0U5751XPUQykDvHakgmBol4nHNUdkyAyvSvdkK4ibN/WMO075WG3NeE+ZBLl5l3IruWPe0Tc5mbG6iWa9Ogojk9VF/rBN1GMwBUJ/0BmqXyQT1rM2/ot0EsFAA+5wBls+EEmkVpUsjScKYCajUwkw=='


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
    dev = request.query_params.get('dev') == 'true'

    if not text:
        return JSONResponse(content={"response": "No question asked"}, status_code=200)

    # If dev mode is true or user_id is not detected, generate a unique id
    if dev or not user_id:
        user_id = str(uuid.uuid4())

    messages = [{"role":"user", "content": text}]

    try:
        response = await g4f.ChatCompletion.create_async(
            model="gemini-pro",
            messages=messages,
            provider=g4f.Provider.GeminiPro,
            api_key="AIzaSyBW0t8wOZ5n59RmO0n_NF8zAww-uhBaWnU"
        )
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        # If the ask function fails, return an error message
        return JSONResponse(content={"response": str(e)}, status_code=500)

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




