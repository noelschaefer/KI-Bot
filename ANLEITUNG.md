# KI-Musikbot für Discord – Anleitung (Windows)

Ein kostenloser Discord-Bot, der in deinem Sprachkanal Musik abspielt und mit einer **lokalen KI** passende Songs zu deinem Wunsch aussucht. Er kann auch normale Fragen beantworten.

- `/dj was Entspanntes zum Lernen` → die KI wählt Songs aus und sagt sie wie ein Radio-DJ an
- `/frage Was ist ein guter Name für unseren Server?` → normale KI-Antwort

**Kosten: 0 €.** Die KI läuft auf deinem PC (Ollama), die Musik kommt aus deinem eigenen Ordner.

---

## 1. So funktioniert der Bot

```
 Du in Discord            Dein PC
 ─────────────            ──────────────────────────────────────────
  /dj "Party"   ──────▶   bot.py  ──(Songliste + Wunsch)──▶  Ollama (KI)
                            │      ◀──(Song-Nummern + Ansage)──┘
                            │
                            ├─▶ musik.py: holt die Dateien aus dem Ordner "musik"
                            │
  🔊 Sprachkanal ◀────────  └─▶ FFmpeg: wandelt die MP3 in Discord-Audio um
```

| Datei | Aufgabe |
|---|---|
| `bot.py` | Das Herzstück: Anmeldung bei Discord, Slash-Befehle, Sprachkanal, Warteschlange |
| `ki.py` | Spricht mit Ollama: Chat-Antworten und Song-Auswahl |
| `musik.py` | Liest deine Musikdateien und die Infos aus `songs.json` ein |
| `musik/songs.json` | Titel, Künstler und Stichworte (Tags) zu deinen Songs |
| `.env` | Deine geheimen Einstellungen (Token). Legst du selbst an. |
| `requirements.txt` | Liste der Python-Pakete, die installiert werden |
| `starten.bat` | Startet den Bot per Doppelklick |

Der Code ist ausführlich kommentiert. Am besten liest du ihn in der Reihenfolge `musik.py` → `ki.py` → `bot.py`.

---

## 2. Vorbereitung: Wie stark ist dein PC?

**Arbeitsspeicher prüfen:** `Strg + Umschalt + Esc` → Task-Manager → Reiter **Leistung** → **Arbeitsspeicher**. Oben rechts steht die Größe, z. B. „16,0 GB“.

| Arbeitsspeicher | Empfohlenes Modell | In `.env` eintragen |
|---|---|---|
| 8 GB | Llama 3.2 (klein, 3B) | `OLLAMA_MODELL=llama3.2` |
| 16 GB | Qwen 2.5 (7B) – klüger | `OLLAMA_MODELL=qwen2.5:7b` |
| 32 GB+ | Qwen 2.5 (14B) – noch besser | `OLLAMA_MODELL=qwen2.5:14b` |

Im Zweifel fängst du mit `llama3.2` an. Das läuft fast überall.

---

## 3. Einrichtung Schritt für Schritt

### Schritt 1: Programme installieren

1. **Python**: von [python.org](https://www.python.org/downloads/) herunterladen und installieren. **Wichtig:** Im ersten Fenster den Haken bei **„Add python.exe to PATH“** setzen.
2. **FFmpeg**: Öffne die Eingabeaufforderung (Windows-Taste → `cmd`) und gib ein:
   ```
   winget install Gyan.FFmpeg
   ```
   Danach die Eingabeaufforderung schließen und neu öffnen. Mit `ffmpeg -version` prüfen, ob es klappt.
3. **Ollama**: von [ollama.com](https://ollama.com/download) herunterladen und installieren. Dann in der Eingabeaufforderung das Modell laden (einmalig, einige GB groß):
   ```
   ollama pull llama3.2
   ```
   Kurz testen: `ollama run llama3.2` → etwas eintippen → mit `/bye` beenden.

### Schritt 2: Bot bei Discord anlegen

1. Gehe zum [Discord Developer Portal](https://discord.com/developers/applications) → **New Application** → Namen vergeben, z. B. „DJ Byte“.
2. Links auf **Bot** → **Reset Token** → Token kopieren. Er wird nur einmal angezeigt, behandle ihn wie ein Passwort.
3. Links auf **OAuth2** → **URL Generator**:
   - Scopes: `bot` und `applications.commands`
   - Bot Permissions: `Send Messages`, `Connect`, `Speak`
4. Den Link unten öffnen und deinen Server auswählen.

Für diesen Bot brauchst du keinen „Message Content Intent“, weil er nur Slash-Befehle nutzt.

### Schritt 3: Projekt einrichten

1. Entpacke den Projektordner, z. B. nach `C:\Users\DeinName\ki-musikbot`.
2. Öffne die Eingabeaufforderung **in diesem Ordner**: Im Explorer in die Adresszeile `cmd` tippen und Enter drücken.
3. Virtuelle Umgebung anlegen und Pakete installieren:
   ```
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
   Eine *virtuelle Umgebung* ist ein eigener Python-Bereich nur für dieses Projekt. So kommen sich verschiedene Projekte nicht in die Quere.
4. Kopiere `.env.example`, benenne die Kopie in `.env` um und trage deinen Token ein. Optional auch deine Server-ID (`GUILD_ID`), dann erscheinen die Befehle sofort. Die Server-ID bekommst du so: Discord → Einstellungen → Erweitert → **Entwicklermodus** an, dann Rechtsklick auf deinen Server → **Server-ID kopieren**.

> Tipp: Falls Windows die Datei als `.env.txt` speichert, im Explorer unter **Ansicht → Einblenden → Dateinamenerweiterungen** aktivieren und umbenennen.

### Schritt 4: Musik hinzufügen

1. Lege deine Musikdateien (`.mp3`, `.wav`, `.ogg`, `.flac`, `.m4a`) in den Ordner `musik`.
2. Trage sie in `musik/songs.json` ein. Die Beispiel-Einträge kannst du ersetzen:
   ```json
   {
     "datei": "mein-song.mp3",
     "titel": "Mein Song",
     "kuenstler": "Künstlername",
     "tags": ["entspannt", "lernen"]
   }
   ```
   **Die Tags sind entscheidend:** Daran erkennt die KI, welcher Song zu einem Wunsch passt. Je besser die Tags, desto besser die Auswahl.
   Songs ohne Eintrag funktionieren auch, dann sieht die KI aber nur den Dateinamen.

Kostenlose, legale Musik gibt es z. B. bei **Pixabay Music**, im **Free Music Archive** oder bei **Jamendo**. Prüf bei jedem Song kurz die Lizenz.

### Schritt 5: Starten

1. Ollama muss laufen. Nach der Installation startet es meist automatisch, erkennbar am Lama-Symbol unten rechts in der Taskleiste.
2. Doppelklick auf **`starten.bat`**.
3. Wenn `✅ Eingeloggt als ...` erscheint, ist der Bot online.
4. In Discord: in einen Sprachkanal gehen und `/dj was Entspanntes` eingeben.

Das Fenster muss offen bleiben, solange der Bot laufen soll. Schließt du es, geht der Bot offline.

---

## 4. Alle Befehle

| Befehl | Was er macht |
|---|---|
| `/dj <wunsch>` | KI wählt passende Songs aus und stellt sie in die Warteschlange |
| `/play <titel>` | Bestimmten Song suchen und abspielen (ohne KI) |
| `/skip` | Aktuellen Song überspringen |
| `/pause` / `/weiter` | Pausieren / fortsetzen |
| `/stop` | Alles stoppen und Sprachkanal verlassen |
| `/warteschlange` | Zeigt, was läuft und was als Nächstes kommt |
| `/bibliothek` | Musikordner neu einlesen und alle Songs anzeigen |
| `/frage <text>` | Normale Frage an die KI |

---

## 5. Was im Code passiert (die wichtigsten Ideen)

**Slash-Befehle:** Jede Funktion mit `@bot.tree.command(...)` wird zu einem Befehl in Discord. Die Parameter der Funktion (z. B. `wunsch: str`) werden automatisch zu Eingabefeldern.

**`async` / `await`:** Der Bot muss viele Dinge gleichzeitig können, etwa Musik spielen, während die KI nachdenkt. `await` heißt: „Warte auf das Ergebnis, aber blockiere in der Zwischenzeit nicht den ganzen Bot.“

**`defer`:** Discord erwartet innerhalb von 3 Sekunden eine Reaktion. Die KI braucht oft länger. Mit `interaction.response.defer()` zeigt der Bot „denkt nach …“ und antwortet später mit `followup.send()`.

**Die Song-Auswahl durch die KI** (`ki.py → songs_auswaehlen`):
1. Der Bot schickt der KI eine nummerierte Liste: `0: Sunset Lounge [entspannt, lernen]`, `1: Neon Nights [party] ...`
2. Er verlangt eine Antwort im JSON-Format: `{"songs": [0, 4], "ansage": "Zeit zum Chillen!"}`
3. JSON kann das Programm zuverlässig auslesen. Ungültige Nummern werden aussortiert, weil kleine Modelle manchmal Fehler machen.

**Die Warteschlange** (`bot.py → naechster_song`): `vc.play(..., after=danach)` spielt einen Song ab. Ist er zu Ende, ruft Discord automatisch `danach` auf, und das startet den nächsten Song. Auch `/skip` nutzt das: Es stoppt einfach den aktuellen Song, und `danach` übernimmt den Rest.

**`.env`:** Geheimnisse wie der Token stehen nie im Code. `load_dotenv()` liest sie beim Start aus der Datei `.env`.

---

## 6. Häufige Probleme

| Problem | Lösung |
|---|---|
| `Kein DISCORD_TOKEN gefunden` | Datei heißt nicht genau `.env` (evtl. `.env.txt`) oder liegt im falschen Ordner |
| Befehle erscheinen nicht in Discord | `GUILD_ID` in `.env` eintragen und Bot neu starten. Discord ggf. mit `Strg + R` neu laden |
| „Die KI ist nicht erreichbar“ | Ollama läuft nicht, oder das Modell aus `.env` wurde nicht mit `ollama pull` geladen |
| Bot betritt den Kanal, aber man hört nichts | FFmpeg fehlt → `ffmpeg -version` testen, sonst Pfad in `FFMPEG_PFAD` eintragen |
| `PyNaCl library needed` | `pip install -r requirements.txt` in der aktivierten `.venv` erneut ausführen |
| KI-Antworten sind sehr langsam | Kleineres Modell nehmen (`llama3.2`) und andere Programme schließen |
| KI wählt unpassende Songs | Bessere Tags in `songs.json` vergeben oder ein größeres Modell nutzen |

---

## 7. Ideen zum Weiterbauen

- **Lautstärke-Befehl** mit `discord.PCMVolumeTransformer`
- **Zufallsmodus** (`/shuffle`) mit `random.shuffle(warteschlange)`
- **Automatischer Rauswurf:** Bot verlässt den Kanal, wenn er allein ist
- **Tags automatisch erstellen:** Die KI schlägt anhand des Titels Tags für neue Songs vor
