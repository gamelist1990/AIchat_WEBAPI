from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import g4f
import json
import asyncio
import logging
import subprocess
import os
import base64
import uuid
import shutil
from PIL import Image
import threading
import time
import shutil
from pathlib import Path
import re
import logging
import glob
from concurrent.futures import ThreadPoolExecutor
import uvicorn

# Load cookies from a JSON file
with open('cookies.json', 'r') as f:
    cookies = json.load(f)

g4f.debug.logging = True  # Enable debug logging
g4f.debug.version_check = False  # Disable automatic version checking


logging.basicConfig(level=logging.INFO)

Token = "15VBs_g92c5WcLeDh7F058OJrZOFeV0IsKBevB65QZsGCHX4eBXFAMm9HBHLnxXurk9PR0FMyN-aIUFx9aOYSDcCC6SUWjFMpz83jsmjmDCqiU9uyITa4z-xzu5BdxPp8zVNIj4o9nAnJTVQSFGeDhRC7r1Ge5t2xA_h946daH1GEfe9XCpHIawXez3RMokifNtyDXMgnPD-nPJnNxO-qXA"

app = FastAPI()

app.mount("/home", StaticFiles(directory="home"), name="home")



# Initialize the conversation history
conversation_history = {}

geminis = {}

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

@app.get('/ask')
async def ask(request: Request):
    global conversation_history
    global geminis
    text = request.query_params.get('text')
    user_id = request.query_params.get('user_id')  # Get the user ID from the request
    

    # If no user_id is provided, use the IP address as the identifier
    if not user_id:
        user_id = request.client.host

    if not text:
        return JSONResponse(content={"response": "No question asked"}, status_code=200)

    # If this user ID is new, initialize a new conversation history for it
    if user_id not in conversation_history:
        conversation_history[user_id] = []

    # Add the new message to the conversation history
    conversation_history[user_id].append({"role": "user", "content": text})

    if user_id not in geminis:
        geminis[user_id] = []

    geminis[user_id].append({"role":"user", "content": text})

    # If the conversation history exceeds 5 messages, remove the oldest message
    if len(conversation_history[user_id]) > 5:
        conversation_history[user_id].pop(0)

    try:
        response = await g4f.ChatCompletion.create_async(model= g4f.models.default, provider=g4f.Provider.Gemini, messages=geminis[user_id],set_cookies=cookies)
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        try:
            response = await g4f.ChatCompletion.create_async(model= g4f.models.default, provider=g4f.Provider.ChatForAi,  messages=conversation_history[user_id])
        except Exception as e:
            logging.error(f"Error occurred: {str(e)}")
            return JSONResponse(content={"error": str(e)}, status_code=500)

    # Decode the Unicode escaped string
    try:
        decoded_response = json.loads(json.dumps(response))
    except json.decoder.JSONDecodeError:
        error_message = "Invalid JSON response"
        logging.error(f"{error_message}: {response.text}")
        return JSONResponse(content={"error": error_message}, status_code=500)
    else:
        return JSONResponse(content=decoded_response, status_code=200)


@app.get('/generate_image')
async def generate_image(request: Request):
    logging.info('generate_image function called')
    # Get the prompt from the request parameters
    prompt = request.query_params.get('prompt')

    if not prompt:
        logging.error('No prompt provided')
        return JSONResponse(content={"error": "No prompt provided"}, status_code=400)

    # Generate a unique ID for this request
    request_id = str(uuid.uuid4())
    logging.info(f'Generated request_id: {request_id}')

    # Create a new directory for this request
    os.makedirs(request_id, exist_ok=True)
    logging.info(f'Created directory: {request_id}')

    base64_images = []
    try:
        # Run the BingImageCreator command as a new process
        logging.info('Starting BingImageCreator process')
        with ThreadPoolExecutor() as executor:
            future = executor.submit(subprocess.run, ["python", "-m", "BingImageCreator", "-U", Token, "--prompt", prompt], cwd=request_id, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            process = future.result()

        # Wait for the process to finish and get the stdout and stderr
        stdout, stderr = process.stdout, process.stderr
        logging.info(f'BingImageCreator process finished with stdout: {stdout}, stderr: {stderr}')

        # Check the files containing '1' and '0' in the UUID/output directory
        for number in ['1', '0']:
            # Construct the file pattern
            file_pattern = os.path.join(request_id, 'output', f'*{number}*.*')

            # Get the list of files matching the pattern
            files = glob.glob(file_pattern)

            for file in files:
                logging.info(f'Checking file: {file}')

                if not os.path.exists(file):
                    logging.warning(f'File does not exist: {file}')
                    continue

                try:
                    # Open the image file with PIL to check if it's broken
                    img = Image.open(file)
                    img.verify()
                    logging.info(f'Image file is not broken: {file}')

                    # If the image is not broken, convert it to base64
                    with open(file, 'rb') as f:
                        image_data = f.read()
                    base64_image = base64.b64encode(image_data).decode('utf-8')
                    logging.info(f'Converted image to base64: {file}')

                    # Add the base64 image to the list
                    base64_images.append(base64_image)
                except (IOError, SyntaxError):
                    # If the image is broken, continue to check the next one
                    logging.error(f'Image file is broken: {file}')
                    continue

    except Exception as e:
        logging.error(f'Exception occurred: {str(e)}')
        return JSONResponse(content={"error": str(e)}, status_code=500)
    finally:
        # Remove the directory for this request
        shutil.rmtree(request_id)
        logging.info(f'Removed directory: {request_id}')

    # Return the base64 encoded images
    if base64_images:
        logging.info('Returning base64 encoded images')
        return JSONResponse(content={"images": base64_images}, status_code=200)
    else:
        logging.error('Failed to generate images')
        return JSONResponse(content={"error": "画像生成ができませんでした(画像生成側エラーもしくはリクエストの送りすぎです[一日最大でも100枚])"}, status_code=500)
# ここにエンドポイントを定義します

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)