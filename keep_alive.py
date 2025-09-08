from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home():
    return "Bot is alive!"
def run_flask():
    try:
        app.run(host="0.0.0.0", port=8080)
    except OSError:
        try:
            app.run(host="0.0.0.0", port=8081)
        except OSError:
            print("Could not start Flask server")
flask_thread = Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()
