import requests
import json
import os

API_URL = "https://fahrinfo.vbb.de/restproxy/latest/disruptions"
STATE_FILE = "state.json"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram(msg):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Telegram nicht konfiguriert")
        return

    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": msg,
                "parse_mode": "HTML"
            },
            timeout=10
        )
    except Exception as e:
        print("Telegram Fehler:", e)


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}

    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
            return {d["id"]: d for d in data if "id" in d}
    except:
        return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(list(state.values()), f, indent=2)


def fetch_disruptions():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }

        res = requests.get(API_URL, headers=headers, timeout=10)

        print("Status Code:", res.status_code)

        # Debug: falls keine JSON Antwort
        if res.status_code != 200:
            print("Antwort:", res.text[:200])
            return []

        return res.json()

    except Exception as e:
        print("API Fehler:", e)
        return []


def format_message(prefix, disruption):
    title = disruption.get("title", "Keine Beschreibung")
    desc = disruption.get("description", "")
    return f"<b>{prefix}</b>\n{title}\n{desc}"


def main():
    old_state = load_state()
    disruptions = fetch_disruptions()

    current_state = {d["id"]: d for d in disruptions if "id" in d}

    old_ids = set(old_state.keys())
    current_ids = set(current_state.keys())

    new_ids = current_ids - old_ids
    resolved_ids = old_ids - current_ids

    if new_ids:
        print("Neue Störungen gefunden")

    for nid in new_ids:
        msg = format_message("🆕 Neue Störung", current_state[nid])
        print(msg)
        send_telegram(msg)

    if resolved_ids:
        print("Behobene Störungen gefunden")

    for rid in resolved_ids:
        msg = format_message("✅ Behoben", old_state[rid])
        print(msg)
        send_telegram(msg)

    if not new_ids and not resolved_ids:
        print("Keine Änderungen")

    save_state(current_state)


if __name__ == "__main__":
    main()
