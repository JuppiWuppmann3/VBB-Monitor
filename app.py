import requests
import time
import json
import os
from datetime import datetime

API_URL = "https://fahrinfo.vbb.de/restproxy/latest/disruptions"
STATE_FILE = "state.json"
CHECK_INTERVAL = 300  # 5 Minuten

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def send_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        log("⚠️ Telegram nicht konfiguriert")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        log(f"Telegram Fehler: {e}")


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
    res = requests.get(API_URL, timeout=10)
    res.raise_for_status()
    return res.json()


def format_message(prefix, disruption):
    title = disruption.get("title", "Keine Beschreibung")
    desc = disruption.get("description", "")
    return f"<b>{prefix}</b>\n{title}\n{desc}"


def main():
    log("🚀 Monitor gestartet")

    old_state = load_state()

    while True:
        try:
            disruptions = fetch_disruptions()
            current_state = {d["id"]: d for d in disruptions if "id" in d}

            old_ids = set(old_state.keys())
            current_ids = set(current_state.keys())

            new_ids = current_ids - old_ids
            resolved_ids = old_ids - current_ids

            # Neue Störungen
            for nid in new_ids:
                msg = format_message("🆕 Neue Störung", current_state[nid])
                log(msg)
                send_telegram(msg)

            # Behobene Störungen
            for rid in resolved_ids:
                msg = format_message("✅ Behoben", old_state[rid])
                log(msg)
                send_telegram(msg)

            if not new_ids and not resolved_ids:
                log("😴 Keine Änderungen")

            save_state(current_state)
            old_state = current_state

        except Exception as e:
            log(f"❌ Fehler: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
