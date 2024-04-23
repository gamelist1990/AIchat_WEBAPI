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

Token = "1xbRa-Cd0Qbm-PYnzY3G1jsTlLCo81AHQRcSDm5NmlWIm90lwjkcW4moRohaA5j4pqG8pmo2ac5vh8w-pc4t5IXsJKBTTMiOuRcRNpcjKx6jEygSx9fLz0HnRL1xDV8iUOMlfCENvul28lcgAw2b5nC-Jrq70qHmkVL1Iqnssg31jgHLYpBZ8RMUe28WnaAgmz2Q_QfPOlvAP_4vnKMB2aA"
os.environ["BING_COOKIES"] = Token
Kiev_cookies = 'FABaBBRaTOJILtFsMkpLVWSG6AN6C/svRwNmAAAEgAAACP9aKorbYOIOGAT37RzYWD1UbwgKVAI891Pihn15AoPJ1xoLw6D2uPzD2M54c1RNk7mjzDWh2A0dT+Ch/EFzb21Q8NZlbKxepkoARZbXX3IBzJ1tf0ll5ZXFAjdBUaQPfYjmMHTMGBGR+iwOOEBWD/bL/27egQYk6f6S0tf4TUvCHcjg8Q0YvIysvLFuvN8r9PrJ260HlTETFYDfuBwEranoSrg3R7yZw4qc4yUK2d6h4ttcOfbifBoJjI0oUdMR/OqIjQCKWwC1NZyglFOxxt/thXL0lLPmGRLl27PMFzbtK03j66I6EZgEJ2/0C4OaPkCDw9KLHsfx1lAfpEbSwbi2d+Qz7CMGLNY8PvCjihO1lX78Yrm8mPqZEeTnQPeNG2AEmeqminHivHDKhS3kzv+Ed3/2mG0FNZ9IDbHzqSq6rYPUz/HxQ+PZriA2Jpd/nUTw4kGJffWAWkjIekC9vxygyXixnkmdn/R20MCfC77ESI39+Mi2YQXY2NmQJj/+06sL+zsBs6ZHiR/J2VIAsFAFIgWFffwgPmC0rdOES2IZkcOSk7nH4U/G4pyvdNGpBNN7RDL/MMy06iO9g8jnvGExXKByYz6fMGs7++FTYdM0IzHfj0dnTaSEZTWDumQilaOtFmmReZ+yQKBDtMvV7P4kGEYxg35bKmg3MB94Fj9ecnWA8m3CUwkPjoiVwfL3EGld8aR/d3HEkp08+KaQmo1o6lTB71W/tqWpP0d5DoNYojpRGlaWx1z3mayA9R8NT40FtH9AHHJ9M6E8hMYLgpieOnhggLWYTVOoFq9U3u9HkjMgdsfJ4Wi9J0Zb1m7rhZ1OJHgCIgbVmkwCspQyGDBZwMxCZTTdBWo8bxP8kWh6IEZ9h5H9TOKTaWQRwt6nrDCe6luf7Sr1KrOkiPKyoY+j6WBfQS1lQe6BKxs9PGXBouwCLz1qB9tZ7OD6WlvXzJJtLYHe6txfrEX3WfLd9AhU7yLiHde0nLfBL2a6F7Ov8vzC8+5ThtJ8Uo58N4yWZZ8n+yAui2v5GiEZix6+ptetUnDTDdYnw9FzrwBvS6HAZH9sM3jYoQKK0OjkonZEbwFcSZUJu24gifSS0Xw6wA0dZwGXuup4fJCVFw3Qkrg94EzdYHUvPTCTWiJf/s6+2BzgWE+uCSuyag5p40LKXomVq5l6S522NTM16ZDDObqo6p81WGrdiVXucP0dPtY4mDDY4QgOZXO2q5X4DUgRRCL4fpZx5+QSdYqGtMXUrbH/AT2RkIQIpKZ0qQFf3b5xfVf+uEBkrkwBLf+swDldXqN2rhzuzodvnuTFodIQvGyPu+7GZNo/ve20pZjV/n8NVZTSVxIqOVh697MThMQl0KI7S/Ktfi946CrN1mfdXL6CwtvzVhFTyY51UHfqTO30SprSFAA27x9poqmvgzLmaXvg8VJcnI4/WQ=='


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
    
    client = AsyncClient(
        provider=OpenaiChat,
        image_provider=Gemini,
    )
    
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
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




