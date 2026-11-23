# KI-Musikbot für Discord

Ein Discord-Bot, der Musik aus einer lokalen Musikbibliothek im Sprachkanal abspielt. Die Songauswahl übernimmt eine lokal laufende KI über [Ollama](https://ollama.com): Man beschreibt, worauf man Lust hat, und der Bot sucht passende Songs aus der eigenen Bibliothek heraus.

Beispiel:

```
/dj was Entspanntes zum Lernen
```

Der Bot läuft auf einem Windows-PC und nutzt keine kostenpflichtigen Dienste.

## Funktionen

- Songauswahl durch die KI anhand eines Wunsches, zum Beispiel „Party“, „Lernen“ oder „Gaming“
- Wiedergabe eigener Musikdateien aus dem Ordner `musik/` (`.mp3`, `.wav`, `.ogg`, `.flac`, `.m4a`)
- Stichworte (Tags) pro Song in `musik/songs.json`, an denen die KI erkennt, wozu ein Song passt
- Warteschlange mit Überspringen, Pausieren und Fortsetzen
- Beantwortung allgemeiner Fragen über die KI

## Befehle

| Befehl | Beschreibung |
|---|---|
| `/dj <wunsch>` | Die KI wählt passende Songs aus und stellt sie in die Warteschlange |
| `/play <titel>` | Sucht einen bestimmten Song nach Titel oder Künstler und spielt ihn ab |
| `/skip` | Überspringt den aktuellen Song |
| `/pause` | Pausiert die Wiedergabe |
| `/weiter` | Setzt die Wiedergabe fort |
| `/stop` | Stoppt die Musik, leert die Warteschlange und verlässt den Sprachkanal |
| `/warteschlange` | Zeigt den aktuellen Song und die folgenden Songs |
| `/bibliothek` | Liest den Musikordner neu ein und listet alle Songs auf |
| `/frage <text>` | Stellt der KI eine Frage |

## Aufbau

| Datei | Aufgabe |
|---|---|
| `bot.py` | Anmeldung bei Discord, Slash-Befehle, Sprachkanal und Warteschlange |
| `ki.py` | Kommunikation mit Ollama für Songauswahl und Antworten |
| `musik.py` | Einlesen der Musikdateien und der Angaben aus `songs.json` |
| `musik/songs.json` | Titel, Künstler und Tags der Songs |
| `.env.example` | Vorlage für die Einstellungen (Token, Server-ID, KI-Modell) |
| `starten.bat` | Startet den Bot per Doppelklick |
| `ANLEITUNG.md` | Ausführliche Einrichtungsanleitung und Erklärung des Codes |

Ablauf bei `/dj`: `bot.py` schickt die Songliste mit den Tags und den Wunsch an `ki.py`. Die KI antwortet mit den Nummern der passenden Songs, die dann über FFmpeg im Sprachkanal abgespielt werden.

## Installation (Windows)

Voraussetzungen:

- [Python 3.13](https://www.python.org/downloads/)
- [FFmpeg](https://ffmpeg.org), z. B. über `winget install Gyan.FFmpeg`
- [Ollama](https://ollama.com/download) mit einem Modell, z. B. `ollama pull llama3.2`

Hinweis: Mit Python 3.15 lässt sich das Paket `davey`, das für die Sprachausgabe benötigt wird, derzeit nicht installieren. Deshalb Python 3.13 verwenden.

1. Repository klonen.
2. Im Projektordner die Eingabeaufforderung öffnen und folgende Befehle ausführen:
   ```
   py -3.13 -m venv .venv
   .venv\Scripts\pip install -r requirements.txt
   ```
3. `.env.example` kopieren, die Kopie in `.env` umbenennen und den Token des Discord-Bots eintragen.
4. Musikdateien in den Ordner `musik/` legen und in `musik/songs.json` eintragen.
5. `starten.bat` ausführen.

Eine ausführliche Anleitung, auch zum Anlegen des Bots im Discord Developer Portal, steht in [ANLEITUNG.md](ANLEITUNG.md).

## Geplante Erweiterungen

- Anbindung an Spotify
- Befehl `/download` zum Herunterladen freier Musik von Jamendo
- Lautstärkeregelung
- Zufallswiedergabe (`/shuffle`)
- Automatisches Verlassen des Sprachkanals, wenn niemand mehr darin ist

## Technik

Python 3.13, [discord.py](https://github.com/Rapptz/discord.py) 2.7, Ollama, FFmpeg

## Hinweis zur Musik

Die Musikdateien sind nicht Teil dieses Repositorys. Es sollte nur Musik verwendet werden, für die eine Nutzungserlaubnis besteht, zum Beispiel von Pixabay Music, dem Free Music Archive oder Jamendo.
