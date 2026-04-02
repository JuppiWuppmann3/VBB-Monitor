import requests
import json
import os

VBB_URL = "https://fahrinfo.vbb.de/restproxy/latest/himsearch?accessId=lipsius-4f41-ab9c-1d54b21c347a&format=json"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

DATA_FILE = "data.json"


def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def get_disruptions():
    res = requests.get(VBB_URL)
    res.raise_for_status()
    data = res.json()
    return data.get("himList", [])


def format_new(item):
    title = item.get("headline", "Keine Überschrift")
    desc = item.get("text", "")
    return f"🚧 *Neue Störung*\n\n*{title}*\n{desc}"


def format_removed(title):
    return f"✅ *Störung behoben*\n\n*{title}*"


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)


def main():
    old_data = load_data()
    current_items = get_disruptions()

    current_data = {}

    # aktuelle IDs sammeln
    for item in current_items:
        item_id = str(item.get("id"))
        title = item.get("headline", "Keine Überschrift")
        current_data[item_id] = title

        # neue Störung
        if item_id not in old_data:
            send_telegram(format_new(item))

    # entfernte Störungen erkennen
    for old_id, old_title in old_data.items():
        if old_id not in current_data:
            send_telegram(format_removed(old_title))

    # speichern
    save_data(current_data)


if __name__ == "__main__":
    main()
