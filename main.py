from flask import Flask, request, jsonify, render_template
import g4f
import json
import asyncio
import logging

g4f.debug.logging = True  # Enable debug logging
g4f.debug.version_check = False  # Disable automatic version checking

app = Flask(__name__)

# Initialize the conversation history
conversation_history = {}

# Set up logging
logging.basicConfig(filename='flask.log', level=logging.DEBUG)

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
        response = loop.run_until_complete(g4f.ChatCompletion.create_async(model= g4f.models.default, provider=g4f.Provider.Liaobots, messages=conversation_history[ip_address]))
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        try:
            response = loop.run_until_complete(g4f.ChatCompletion.create_async(model= g4f.models.default, messages=conversation_history[ip_address]))
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

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000, debug=True)
￥