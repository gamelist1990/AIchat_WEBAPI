from flask import Flask, redirect

app = Flask(__name__)

@app.route('/')
def redirect_to_another_url():
    return redirect("http://www.another_url.com", code=302)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
