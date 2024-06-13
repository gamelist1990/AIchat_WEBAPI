import requests
import json
import os
import base64
import logging

logging.basicConfig(level=logging.INFO)

class HuggingChat_RE:
    def __init__(self, hf_chat: str, model: str) -> None:
        self.hf_chat = hf_chat
        self.model = model
        self.headers = {"Cookie": f"hf-chat={self.hf_chat}"}
        self.conversationId = self.find_conversation_id()

    def find_conversation_id(self) -> str:
        url = "https://huggingface.co/chat/conversation"
        payload = {"model": self.model}
        response = requests.post(url, json=payload, headers=self.headers).json()
        logging.info(f"Conversation ID: {response['conversationId']}")
        return response['conversationId']

    def generate(self, query: str) -> str:
        url = f"https://huggingface.co/chat/conversation/{self.conversationId}"
        payload = {"inputs": query, "is_retry": False, "is_continue": False}
        response = requests.post(url, json=payload, headers=self.headers)
        complete_response = ""
        for chunk in response.iter_lines(chunk_size=1, decode_unicode=True):
            if chunk:
                try:
                    json_data = json.loads(chunk.strip())
                    if json_data['type'] == "stream":
                        complete_response += json_data['token']
                except:
                    continue
        logging.info(f"Generated response: {complete_response}")
        return complete_response

if __name__ == "__main__":
    hf_api = HuggingChat_RE(hf_chat="c1f93d9f-505b-45a1-b977-5b63ff0d17f2; Path=/; Expires=Tue, 25 Jun 2024 18:02:47 GMT; HttpOnly; Secure; SameSite=None", model="google/gemma-1.1-7b-it")
    while True:
        query = input("\n> ")
        response = hf_api.generate(query)
        print(response)
