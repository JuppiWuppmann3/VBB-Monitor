import requests
import json
import os
import time

VBB_URL = "https://fahrinfo.vbb.de/restproxy/latest/himsearch?accessId=lipsius-4f41-ab9c-1d54b21c347a&format=json"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

DATA_FILE = "data.json"
CHECK_INTERVAL = 300  # alle 5 Minuten

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def get_disruptions():
    try:
        res = requests.get(VBB_URL, timeout=10)
        data = res.json()
        if "Message" in data:
            return data["Message"]
        return []
    except Exception as e:
        print("❌ API Fehler:", e)
        return []

def format_new(item):
    title = item.get("head", "Keine Überschrift")
    desc = item.get("text", "")
    if not desc and "messageText" in item:
        try:
            desc = item["messageText"][0]["text"][0]
        except:
            desc = ""
    lines = [prod.get("name") for prod in item.get("affectedProduct", []) if prod.get("name")]
    line_info = f"Linien: {', '.join(lines)}\n" if lines else ""
    return f"🚧 *Neue Störung*\n\n*{title}*\n{line_info}{desc}"

def format_removed(title):
    return f"✅ *Störung behoben*\n\n*{title}*"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        r = requests.post(url, json=payload)
        print("📤 Telegram:", r.status_code, r.text)
    except Exception as e:
        print("❌ Telegram Fehler:", e)

def main_loop():
    print("🚀 Starte Bot im Dauerbetrieb...")
    while True:
        old_data = load_data()
        current_items = get_disruptions()
        current_data = {}

        for item in current_items:
            if not item.get("act", False):
                continue
            item_id = str(item.get("id"))
            title = item.get("head", "Keine Überschrift")
            current_data[item_id] = title
            if item_id not in old_data:
                print("➡️ Neue Störung:", title)
                send_telegram(format_new(item))

        for old_id, old_title in old_data.items():
            if old_id not in current_data:
                print("➡️ Entfernt:", old_title)
                send_telegram(format_removed(old_title))

        save_data(current_data)
        print(f"💾 Gespeichert: {len(current_data)} Einträge")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main_loop()
