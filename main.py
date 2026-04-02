import requests
import json
import os

# 🌐 API URL VBB
VBB_URL = "https://fahrinfo.vbb.de/restproxy/latest/himsearch?accessId=lipsius-4f41-ab9c-1d54b21c347a&format=json"

# 🔒 Secrets aus GitHub Actions
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

DATA_FILE = "data.json"


# -------------------
# Daten laden / speichern
# -------------------
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            # alte Liste → Dict konvertieren
            if isinstance(data, list):
                print("⚠️ Alte Datenstruktur erkannt (Liste) → wird konvertiert")
                return {}
            return data
    except FileNotFoundError:
        return {}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


# -------------------
# API Abfrage
# -------------------
def get_disruptions():
    try:
        res = requests.get(VBB_URL, timeout=10)
        print("🌐 Status Code:", res.status_code)
        data = res.json()
        print("🔍 Keys:", data.keys())

        # verschiedene API-Strukturen abfangen
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


# -------------------
# Meldungen formatieren
# -------------------
def format_new(item):
    title = item.get("head", "Keine Überschrift")
    
    # 1️⃣ ausführlicher Text
    desc = item.get("text", "")
    if not desc and "messageText" in item:
        try:
            desc = "\n".join([t for mt in item["messageText"] for t in mt.get("text", [])])
        except:
            desc = ""

    # 2️⃣ betroffene Linien/Produkte
    lines = []
    for prod in item.get("affectedProduct", []):
        if prod.get("name"):
            lines.append(prod["name"])
    line_info = f"Linien: {', '.join(lines)}\n" if lines else ""

    # 3️⃣ Start- und Endhaltestellen
    start_stop = item.get("validFromStop", {}).get("name")
    end_stop = item.get("validToStop", {}).get("name")
    stop_info = f"Von: {start_stop}\nBis: {end_stop}\n" if start_stop and end_stop else ""

    # 4️⃣ Start- und Endzeit
    s_date = item.get("sDate")
    s_time = item.get("sTime")
    e_date = item.get("eDate")
    e_time = item.get("eTime")
    time_info = ""
    if s_date and s_time and e_date and e_time:
        time_info = f"⏰ {s_date} {s_time} – {e_date} {e_time}\n"

    # 5️⃣ Betreiber
    company = item.get("company")
    company_info = f"🚋 Betreiber: {company}\n" if company else ""

    # fertige Meldung
    message = f"🚧 *Neue Störung*\n\n*{title}*\n{line_info}{stop_info}{time_info}{company_info}{desc}"
    return message


def format_removed(title):
    return f"✅ *Störung behoben*\n\n*{title}*"


# -------------------
# Telegram Nachricht senden
# -------------------
def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Telegram Token oder Chat-ID fehlt!")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": str(TELEGRAM_CHAT_ID),
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        r = requests.post(url, json=payload)
        print("📤 Telegram:", r.status_code, r.text)
    except Exception as e:
        print("❌ Telegram Fehler:", e)


# -------------------
# Hauptprogramm
# -------------------
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
