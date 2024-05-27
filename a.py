from g4f.local import LocalClient

client   = LocalClient()
response = client.chat.completions.create(
    model    = 'orca-mini-3b',
    messages = [{"role": "user", "content": "hi"}],
    stream   = True
)

for token in response:
    print(token.choices[0].delta.content or "")
