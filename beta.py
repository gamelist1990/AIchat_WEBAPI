from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Optional
from g4f.image import ImageResponse



import g4f, json
import logging
import shutil
import threading
import time
import re
import uvicorn

with open('cookies.json', 'r') as file:
    data = json.load(file)

cookies={}
for cookie in data:
    cookies[cookie["name"]] = cookie["value"]



token2 = {
            "__Secure-1PSID": "g.a000gQg8QrMMHaFNt4xrii5g6VL1qTCle2Et6qVnioaet_72wj05BaexUH0IpglZ6YqdKCWSwAACgYKAfASAQASFQHGX2MioH0Ad5GKLx1qf-dA97-DcRoVAUF8yKpLwVs5mpoNBWzTwz0ggi6n0076"
        }

token = {
            "_U": "1Yxs6UfNiQTfZMB9a_0xBTDSU6Y2-AlBDrFNcsxSXpJv7TbNkpmyS3WwVUeO2__NyVfZzCxYni3Zm-nFwBCvnLjWzPjJOb8_bWqbhC0dx80kfMf4LBpUm2Wp1dNiQNL2j0FsZ8sgr84FKm4x4NBkac46t7Ab5kh4kXDyr8wb-ytTnMi9xaX6rChTG-BD9qwGtGsgOghYemnowQaABLZgXKQ"
        }

#set_cookies(".bing.com", {
#  "_U": "1Yxs6UfNiQTfZMB9a_0xBTDSU6Y2-AlBDrFNcsxSXpJv7TbNkpmyS3WwVUeO2__NyVfZzCxYni3Zm-nFwBCvnLjWzPjJOb8_bWqbhC0dx80kfMf4LBpUm2Wp1dNiQNL2j0FsZ8sgr84FKm4x4NBkac46t7Ab5kh4kXDyr8wb-ytTnMi9xaX6rChTG-BD9qwGtGsgOghYemnowQaABLZgXKQ"
#})

#set_cookies(".google.com", {
# "__Secure-1PSID": "g.a000gQg8QrMMHaFNt4xrii5g6VL1qTCle2Et6qVnioaet_72wj05BaexUH0IpglZ6YqdKCWSwAACgYKAfASAQASFQHGX2MioH0Ad5GKLx1qf-dA97-DcRoVAUF8yKpLwVs5mpoNBWzTwz0ggi6n0076"
#})  
    

g4f.debug.logging = True  # Enable debug logging
g4f.debug.version_check = False  # Disable automatic version checking


logging.basicConfig(level=logging.INFO)

#Token = "15VBs_g92c5WcLeDh7F058OJrZOFeV0IsKBevB65QZsGCHX4eBXFAMm9HBHLnxXurk9PR0FMyN-aIUFx9aOYSDcCC6SUWjFMpz83jsmjmDCqiU9uyITa4z-xzu5BdxPp8zVNIj4o9nAnJTVQSFGeDhRC7r1Ge5t2xA_h946daH1GEfe9XCpHIawXez3RMokifNtyDXMgnPD-nPJnNxO-qXA"

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
        cookies={}
        for cookie in data:
            cookies[cookie["name"]] = cookie["value"]
        response = await g4f.ChatCompletion.create_async(
          model=g4f.models.default,
          provider=g4f.Provider.Gemini,
          messages=geminis[user_id],
          cookies={
        "__Secure-1PSID": "g.a000gQg8QrMMHaFNt4xrii5g6VL1qTCle2Et6qVnioaet_72wj05BaexUH0IpglZ6YqdKCWSwAACgYKAfASAQASFQHGX2MioH0Ad5GKLx1qf-dA97-DcRoVAUF8yKpLwVs5mpoNBWzTwz0ggi6n0076"
    }
        )      
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        try:
            response = await g4f.ChatCompletion.create_async(model= g4f.models.default, provider=g4f.Provider.Aura, messages=conversation_history[user_id])
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
    
@app.get("/generate_image")
async def generate_image(prompt: Optional[str] = None):
    # Ensure a prompt was provided
    if prompt is None:
        return JSONResponse(content={"error": "No prompt provided"}, status_code=400)

    # Create the image
    chunks = await g4f.ChatCompletion.create_async(
        model=g4f.models.default, # Using the default model
        provider=g4f.Provider.Bing, # Specifying the provider as OpenaiChat
        messages=[{"role": "user", "content": f"Create images with {prompt}"}],
        cookies=cookies,
    )

    # Get image links from response
    images = []
    for chunk in chunks:
        if isinstance(chunk, ImageResponse):
            images.append({
                "image_links": chunk.images, # Generated image links
                "alt": chunk.alt # Used prompt for image generation
            })

    # Return the images in a JSON response
    return {"images": images}




if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
