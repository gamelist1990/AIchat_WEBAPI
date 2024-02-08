import requests

url = "https://webapi-8trs.onrender.com/ask"

while True:
    user = input("comment :")
    ask = {"text": user}

    try:
        response = requests.get(url, ask)
        print(response.json())
    except Exception as err:
        print(f'Error occurred: {err}')
