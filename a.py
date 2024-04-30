from g4f.client import Client
from g4f.Provider import OpenaiChat

client = Client(
    provider=OpenaiChat,
)

# Initialize an empty list to hold the conversation history
conversation_history = []

while True:
    prompt = input("COMMENT :")

    # Add the user's message to the conversation history
    conversation_history.append({"role": "user", "content": prompt})

    # Ensure that only the last 5 messages are kept
    conversation_history = conversation_history[-5:]

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=conversation_history,
    )

    # Add the assistant's message to the conversation history
    conversation_history.append({"role": "assistant", "content": response.choices[0].message.content})

    print(response.choices[0].message.content)


