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
            data = json.load(f)

            # 🔥 FIX: alte Liste → Dict konvertieren
            if isinstance(data, list):
                print("⚠️ Alte Datenstruktur erkannt (Liste) → wird konvertiert")
                return {}

            return data
    except:
        return {}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def get_disruptions():
    try:
        res = requests.get(VBB_URL, timeout=10)
        res.raise_for_status()
        data = res.json()

        # ✅ KORREKTES FELD
        return data.get("HIMMessage", [])
    except Exception as e:
        print("❌ API Fehler:", e)
        return []


def format_new(item):
    # ✅ KORREKTE FELDER
    title = item.get("head", "Keine Überschrift")
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

    try:
        r = requests.post(url, json=payload)
        print("📤 Telegram:", r.status_code, r.text)
    except Exception as e:
        print("❌ Telegram Fehler:", e)


def main():
    print("🚀 Starte Bot...")

    old_data = load_data()
    print("📦 Alte Daten:", len(old_data))

    current_items = get_disruptions()
    print("📡 API liefert:", len(current_items), "Einträge")

    current_data = {}

    for item in current_items:
        # nur aktive Meldungen
        if not item.get("act", False):
            continue

        item_id = str(item.get("id"))
        title = item.get("head", "Keine Überschrift")

        current_data[item_id] = title

        # 🆕 neue Störung
        if item_id not in old_data:
            print("➡️ Neue Störung:", title)
            send_telegram(format_new(item))

    # ❌ entfernte Störungen
    for old_id, old_title in old_data.items():
        if old_id not in current_data:
            print("➡️ Entfernt:", old_title)
            send_telegram(format_removed(old_title))

    save_data(current_data)
    print("💾 Gespeichert:", len(current_data))


if __name__ == "__main__":
    main()
