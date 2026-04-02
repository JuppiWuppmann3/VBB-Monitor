import requests
import json
import os

VBB_URL = "https://fahrinfo.vbb.de/restproxy/latest/himsearch?accessId=lipsius-4f41-ab9c-1d54b21c347a&format=json"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

DATA_FILE = "data.json"


def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            # Alte Listen in Dict konvertieren
            if isinstance(data, list):
                print("⚠️ Alte Datenstruktur erkannt → konvertiert")
                return {}
            return data
    except FileNotFoundError:
        return {}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def get_disruptions():
    try:
        res = requests.get(VBB_URL, timeout=10)
        print("🌐 Status Code:", res.status_code)
        data = res.json()
        # unterschiedliche Key-Varianten abfangen
        if "HIMMessage" in data:
            return data["HIMMessage"]
        elif "Message" in data:
            return data["Message"]
        else:
            print("⚠️ Unbekannte API-Struktur")
            return []
    except Exception as e:
        print("❌ API Fehler:", e)
        return []


def format_new(item):
    title = item.get("head", "Keine Überschrift")
    desc = item.get("text", "")

    # fallback auf messageText
    if not desc and "messageText" in item:
        try:
            desc = item["messageText"][0]["text"][0]
        except:
            desc = ""

    # Linien extrahieren
    lines = []
    for prod in item.get("affectedProduct", []):
        name = prod.get("name")
        if name:
            lines.append(name)

    line_info = f"Linien: {', '.join(lines)}\n" if lines else ""
    company = item.get("company", "")
    return f"🚧 *Neue Störung*\n\n*{title}*\n{line_info}{desc}\n{company}"


def format_removed(title):
    return f"✅ *Störung behoben*\n\n*{title}*"


def send_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ TELEGRAM_TOKEN oder CHAT_ID fehlt")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
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
        if not item.get("act", False):
            continue
        item_id = str(item.get("id"))
        title = item.get("head", "Keine Überschrift")
        current_data[item_id] = title

        if item_id not in old_data:
            print("➡️ Neue Störung:", title)
            send_telegram(format_new(item))

    # entfernte Meldungen
    for old_id, old_title in old_data.items():
        if old_id not in current_data:
            print("➡️ Entfernt:", old_title)
            send_telegram(format_removed(old_title))

    save_data(current_data)
    print("💾 Gespeichert:", len(current_data))


if __name__ == "__main__":
    main()
