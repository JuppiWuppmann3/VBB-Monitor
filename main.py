import requests
import json
import os
import time

# ── Konfiguration ──────────────────────────────────────────────
VBB_ACCESS_ID   = os.getenv("VBB_ACCESS_ID")
TELEGRAM_TOKEN  = os.getenv("TELEGRAM_TOKEN")
CHAT_ID         = os.getenv("TELEGRAM_CHAT_ID")
SUPABASE_URL    = os.getenv("SUPABASE_URL")       # z.B. https://xxxx.supabase.co
SUPABASE_KEY    = os.getenv("SUPABASE_KEY")       # anon/public key

INTERVAL        = 300   # Sekunden zwischen zwei Durchläufen (5 Minuten)
TABLE           = "stoerungen"

VBB_URL = (
    f"https://fahrinfo.vbb.de/restproxy/latest/himsearch"
    f"?accessId={VBB_ACCESS_ID}&format=json"
)

# ── Supabase Hilfsfunktionen ───────────────────────────────────

def _headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }

def load_data():
    """Lädt alle aktiven Störungen aus Supabase. Gibt {id: item} zurück."""
    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/{TABLE}?select=*",
            headers=_headers(),
            timeout=10,
        )
        rows = r.json()
        if isinstance(rows, list):
            return {row["stoerung_id"]: row["data"] for row in rows}
        print("⚠️ Supabase unerwartetes Format:", rows)
        return {}
    except Exception as e:
        print("❌ Supabase Ladefehler:", e)
        return {}

def save_data(current_data: dict):
    """Überschreibt die Tabelle mit den aktuellen Störungen (upsert)."""
    try:
        # Erst alles löschen was nicht mehr aktuell ist
        existing = load_data()
        removed_ids = [k for k in existing if k not in current_data]
        for rid in removed_ids:
            requests.delete(
                f"{SUPABASE_URL}/rest/v1/{TABLE}?stoerung_id=eq.{rid}",
                headers=_headers(),
                timeout=10,
            )

        # Neue / aktualisierte Einträge einfügen
        if current_data:
            rows = [
                {"stoerung_id": k, "data": v}
                for k, v in current_data.items()
            ]
            requests.post(
                f"{SUPABASE_URL}/rest/v1/{TABLE}",
                headers={**_headers(), "Prefer": "resolution=merge-duplicates"},
                json=rows,
                timeout=10,
            )
    except Exception as e:
        print("❌ Supabase Speicherfehler:", e)

# ── VBB API ────────────────────────────────────────────────────

def get_disruptions():
    try:
        res = requests.get(VBB_URL, timeout=10)
        print("🌐 Status Code:", res.status_code)
        data = res.json()

        if "HIMMessage" in data:
            return data["HIMMessage"]
        elif "Message" in data:
            return data["Message"]
        else:
            print("⚠️ Unbekannte API Struktur:", list(data.keys()))
            return []
    except Exception as e:
        print("❌ VBB API Fehler:", e)
        return []

# ── Telegram ───────────────────────────────────────────────────

def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        print("📤 Telegram:", r.status_code)
    except Exception as e:
        print("❌ Telegram Fehler:", e)

def format_message(item: dict, new: bool) -> str:
    title = item.get("head", "Keine Überschrift")
    desc  = item.get("text", "")
    if not desc and "messageText" in item:
        try:
            desc = item["messageText"][0]["text"][0]
        except Exception:
            desc = ""

    lines = [
        prod["name"]
        for prod in item.get("affectedProduct", [])
        if prod.get("name")
    ]
    line_info = f"Linien: {', '.join(lines)}\n" if lines else ""

    if new:
        return f"🚧 *Neue Störung*\n\n*{title}*\n{line_info}{desc}"
    else:
        return f"✅ *Störung behoben*\n\n*{title}*\n{desc}"

# ── Hauptlogik ─────────────────────────────────────────────────

def check_secrets():
    missing = [
        name for name, val in [
            ("VBB_ACCESS_ID",  VBB_ACCESS_ID),
            ("TELEGRAM_TOKEN", TELEGRAM_TOKEN),
            ("TELEGRAM_CHAT_ID", CHAT_ID),
            ("SUPABASE_URL",   SUPABASE_URL),
            ("SUPABASE_KEY",   SUPABASE_KEY),
        ]
        if not val
    ]
    if missing:
        raise EnvironmentError(f"❌ Fehlende Umgebungsvariablen: {', '.join(missing)}")

def run_bot_cycle():
    print("🔄 Starte Durchlauf...")
    old_data     = load_data()
    current_items = get_disruptions()
    print(f"📦 Alt: {len(old_data)} | 📡 Aktuell: {len(current_items)}")

    current_data: dict = {}

    for item in current_items:
        if not item.get("act", False):
            continue
        item_id = str(item.get("id"))
        current_data[item_id] = item

        if item_id not in old_data:
            print("➡️  Neue Störung:", item.get("head"))
            send_telegram(format_message(item, new=True))

    for old_id, old_item in old_data.items():
        if old_id not in current_data:
            if isinstance(old_item, str):
                old_item = {"head": old_item}
            print("➡️  Behoben:", old_item.get("head"))
            send_telegram(format_message(old_item, new=False))

    save_data(current_data)
    print(f"💾 Gespeichert: {len(current_data)} Störungen\n")

def main():
    check_secrets()
    print("🚀 VBB Bot gestartet (Interval: 5 Minuten)\n")
    while True:
        try:
            run_bot_cycle()
        except Exception as e:
            print("❌ Unerwarteter Fehler im Zyklus:", e)
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
