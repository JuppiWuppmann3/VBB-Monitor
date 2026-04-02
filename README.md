# 🚇 VBB Störungs-Bot

Telegram-Bot der VBB-Störungen überwacht und Nachrichten schickt wenn eine neue Störung auftritt oder behoben wird.

**Läuft als Dauerloop auf Render (kostenlos) und speichert Daten in Supabase (kostenlos).**

---

## Was du brauchst

- GitHub-Account (hast du bereits)
- [Render-Account](https://render.com) (kostenlos)
- [Supabase-Account](https://supabase.com) (kostenlos)
- Deinen Telegram Bot Token + Chat ID (hast du bereits)

---

## Schritt 1 – Supabase einrichten

1. Geh auf [supabase.com](https://supabase.com) → **Start for free** → mit GitHub einloggen
2. Klick auf **New Project** → gib einen Namen ein (z.B. `vbb-bot`) → Passwort vergeben → **Create new project**
3. Warte ~1 Minute bis das Projekt bereit ist
4. Geh links auf **Table Editor** → **New Table**
   - Name: `stoerungen`
   - **Row Level Security (RLS) ausschalten** (Regler auf OFF)
   - Spalten so anlegen:

   | Name | Type | Default |
   |------|------|---------|
   | `id` | int8 | (automatisch, Primary Key) |
   | `stoerung_id` | text | – |
   | `data` | jsonb | – |

   → Klick auf **Save**

5. Geh links auf **Project Settings** → **API**
   - Kopiere die **Project URL** → das ist dein `SUPABASE_URL`
   - Kopiere den **anon / public** Key → das ist dein `SUPABASE_KEY`

---

## Schritt 2 – Code auf GitHub hochladen

1. Erstelle ein neues **privates** Repository auf GitHub (z.B. `vbb-bot`)
2. Lade alle Dateien aus diesem Ordner hoch:
   - `main.py`
   - `requirements.txt`
   - `render.yaml`
   - `.gitignore`

> Tipp: Einfach auf GitHub → **Add file** → **Upload files** und alle 4 Dateien reinziehen.

---

## Schritt 3 – Render einrichten

1. Geh auf [render.com](https://render.com) → einloggen → **New** → **Background Worker**
2. Verbinde dein GitHub-Konto und wähle dein `vbb-bot` Repository aus
3. Render erkennt die `render.yaml` automatisch – einfach bestätigen
4. Geh auf **Environment** und trage folgende Variablen ein:

   | Key | Wert |
   |-----|------|
   | `VBB_ACCESS_ID` | dein VBB Access Key (aus der alten URL) |
   | `TELEGRAM_TOKEN` | dein Bot Token |
   | `TELEGRAM_CHAT_ID` | deine Chat ID |
   | `SUPABASE_URL` | die URL aus Schritt 1 |
   | `SUPABASE_KEY` | der anon Key aus Schritt 1 |

5. Klick auf **Deploy** → fertig! 🎉

---

## Was passiert jetzt?

- Render startet den Bot und er läuft **dauerhaft** im Hintergrund
- Alle **5 Minuten** fragt er die VBB API ab
- Neue Störungen → Telegram-Nachricht 🚧
- Behobene Störungen → Telegram-Nachricht ✅
- Die aktiven Störungen werden in Supabase gespeichert – du kannst sie dort jederzeit live einsehen

---

## Logs anschauen

Im Render-Dashboard → dein Service → **Logs** – dort siehst du jeden Durchlauf live.

---

## Häufige Probleme

**Bot schickt keine Nachrichten**
→ Logs in Render prüfen. Meist fehlt eine Umgebungsvariable (wird beim Start mit Fehlermeldung angezeigt).

**Supabase Fehler**
→ Prüfen ob RLS (Row Level Security) wirklich ausgeschaltet ist bei der Tabelle.

**Render stoppt den Bot nach einer Weile**
→ Beim kostenlosen Plan kann Render den Worker nach Inaktivität stoppen. Einfach im Dashboard neu starten. Für Dauerbetrieb reicht der Free Plan aber normalerweise aus.
