from flask import Flask, request, jsonify, render_template
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


logging.basicConfig(level=logging.INFO)

Token = "15VBs_g92c5WcLeDh7F058OJrZOFeV0IsKBevB65QZsGCHX4eBXFAMm9HBHLnxXurk9PR0FMyN-aIUFx9aOYSDcCC6SUWjFMpz83jsmjmDCqiU9uyITa4z-xzu5BdxPp8zVNIj4o9nAnJTVQSFGeDhRC7r1Ge5t2xA_h946daH1GEfe9XCpHIawXez3RMokifNtyDXMgnPD-nPJnNxO-qXA"

app = Flask(__name__)

# Initialize the conversation history
conversation_history = {}

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




@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/ask', methods=['GET', 'POST'])
def ask():
    global conversation_history
    text = None
    if request.method == 'POST':
        if request.json:
            text = request.json.get('text')
    else:
        text = request.args.get('text')

    if not text:
        return jsonify({"response": "No question asked"}), 200

    # Get the IP address of the client
    ip_address = request.remote_addr

    # If this IP address is new, initialize a new conversation history for it
    if ip_address not in conversation_history:
        conversation_history[ip_address] = []

    # Add the new message to the conversation history
    conversation_history[ip_address].append({"role": "user", "content": text})

    # If the conversation history exceeds 5 messages, remove the oldest message
    if len(conversation_history[ip_address]) > 5:
        conversation_history[ip_address].pop(0)

    try:
        loop = asyncio.new_event_loop()    
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(g4f.ChatCompletion.create_async(model= g4f.models.gpt_4_turbo, provider=g4f.Provider.Bing, messages=conversation_history[ip_address]))
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        try:
            response = loop.run_until_complete(g4f.ChatCompletion.create_async(model= g4f.models.default, provider=g4f.Provider.ChatBase, messages=conversation_history[ip_address]))
        except Exception as e:
            logging.error(f"Error occurred: {str(e)}")
            return jsonify({"error": str(e)}), 500

    # Decode the Unicode escaped string
    try:
        decoded_response = json.loads(json.dumps(response))
    except json.decoder.JSONDecodeError:
        error_message = "Invalid JSON response"
        logging.error(f"{error_message}: {response.text}")
        return jsonify({"error": error_message}), 500
    else:
        return jsonify(decoded_response), 200, {'Content-Type': 'application/json; charset=utf-8'}

@app.route('/generate_image', methods=['GET'])
def generate_image():
    logging.info('generate_image function called')
    # Get the prompt from the request parameters
    prompt = request.args.get('prompt')

    if not prompt:
        logging.error('No prompt provided')
        return jsonify({"error": "No prompt provided"}), 400

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
        process = subprocess.Popen(["python", "-m", "BingImageCreator", "-U", Token, "--prompt", prompt], cwd=request_id, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait for the process to finish and get the stdout and stderr
        stdout, stderr = process.communicate()
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
        return jsonify({"error": str(e)}), 500 
    finally:
        # Remove the directory for this request
        shutil.rmtree(request_id)
        logging.info(f'Removed directory: {request_id}')

    # Return the base64 encoded images
    if base64_images:
        logging.info('Returning base64 encoded images')
        return jsonify({"images": base64_images}), 200, {'Content-Type': 'application/json; charset=utf-8'}
    else:
        logging.error('Failed to generate images')
        return jsonify({"error": "Failed to generate images"}), 500





if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
