import requests
import json
import os

# 🔹 API URL für VBB
VBB_URL = "https://fahrinfo.vbb.de/restproxy/latest/himsearch?accessId=lipsius-4f41-ab9c-1d54b21c347a&format=json"

# 🔹 Telegram Secrets
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 🔹 Datei zum Speichern alter Meldungen
DATA_FILE = "data.json"


def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            # Alte Liste → Dict konvertieren
            if isinstance(data, list):
                print("⚠️ Alte Datenstruktur erkannt → wird konvertiert")
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
        print("🌐 Status Code:", res.status_code)
        data = res.json()
        print("🔍 Keys:", data.keys())

        if "HIMMessage" in data:
            return data["HIMMessage"]
        elif "Message" in data:
            return data["Message"]
        else:
            print("⚠️ Unbekannte API Struktur")
            return []
    except Exception as e:
        print("❌ API Fehler:", e)
        return []


def format_message(item, new=True):
    title = item.get("head", "Keine Überschrift")
    desc = item.get("text", "")
    if not desc and "messageText" in item:
        try:
            desc = item["messageText"][0]["text"][0]
        except:
            desc = ""

    # Linien extrahieren
    lines = [prod.get("name") for prod in item.get("affectedProduct", []) if prod.get("name")]
    line_info = f"Linien: {', '.join(lines)}\n" if lines else ""

    if new:
        prefix = "🚧 *Neue Störung*\n\n"
    else:
        prefix = "✅ *Störung behoben*\n\n"

    return f"{prefix}*{title}*\n{line_info}{desc}"


def send_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ Telegram Token oder Chat ID nicht gesetzt!")
        return
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
        current_data[item_id] = item  # ganze Meldung speichern

        if item_id not in old_data:
            print("➡️ Neue Störung:", item.get("head"))
            send_telegram(format_message(item, new=True))

    # entfernte Meldungen
    for old_id, old_item in old_data.items():
        if old_id not in current_data:
            print("➡️ Entfernt:", old_item.get("head"))
            send_telegram(format_message(old_item, new=False))

    save_data(current_data)
    print("💾 Gespeichert:", len(current_data))


if __name__ == "__main__":
    main()
