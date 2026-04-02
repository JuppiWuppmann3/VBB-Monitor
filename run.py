from flask import Flask
import threading
import main  # dein Bot

app = Flask(__name__)

@app.route("/")
def home():
    return "VBB Bot läuft 🚀"

# Bot in eigenem Thread starten
threading.Thread(target=main.main_loop, daemon=True).start()

if __name__ == "__main__":
    # Port von Render verwenden
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
