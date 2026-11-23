"""
ki.py – Verbindung zur lokalen KI (Ollama)
==========================================

Ollama ist ein kostenloses Programm, das KI-Modelle auf deinem eigenen PC
ausführt. Es startet im Hintergrund einen kleinen Webserver unter
http://localhost:11434. Unser Bot schickt dort Text hin und bekommt die
Antwort der KI zurück – ganz ohne Internet und ohne Kosten.

Diese Datei hat zwei Aufgaben:
1. frage()            -> normale Chat-Antwort (für den Befehl /frage)
2. songs_auswaehlen() -> die KI sucht zu einem Wunsch passende Songs aus
"""

import json

import aiohttp  # wird mit discord.py automatisch mitinstalliert


class KI:
    def __init__(self, url: str, modell: str):
        self.url = url.rstrip("/")  # z. B. "http://localhost:11434"
        self.modell = modell        # z. B. "llama3.2"

    async def _anfrage(self, nachrichten: list[dict], json_format: bool = False) -> str:
        """Schickt einen Chatverlauf an Ollama und gibt die Antwort als Text zurück.

        nachrichten sieht so aus:
            [{"role": "system", "content": "Anweisungen an die KI"},
             {"role": "user",   "content": "Frage des Nutzers"}]
        """
        daten = {
            "model": self.modell,
            "messages": nachrichten,
            "stream": False,  # komplette Antwort auf einmal statt Wort für Wort
        }
        if json_format:
            # Zwingt die KI, gültiges JSON zu liefern – das kann unser Programm
            # zuverlässig auslesen (wichtig für die Song-Auswahl).
            daten["format"] = "json"

        # Lokale Modelle können auf schwächeren PCs etwas brauchen -> 2 Minuten Zeit
        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(f"{self.url}/api/chat", json=daten) as antwort:
                antwort.raise_for_status()  # Fehler, falls Ollama z. B. das Modell nicht kennt
                ergebnis = await antwort.json()

        return ergebnis["message"]["content"]

    async def frage(self, text: str) -> str:
        """Ganz normale Chat-Frage an die KI."""
        system = (
            "Du bist DJ Byte, ein lockerer, freundlicher Musik-Bot auf einem "
            "Discord-Server. Antworte immer auf Deutsch, kurz und gut gelaunt "
            "(höchstens ein paar Sätze)."
        )
        return await self._anfrage([
            {"role": "system", "content": system},
            {"role": "user", "content": text},
        ])

    async def songs_auswaehlen(self, wunsch: str, songs: list, anzahl: int = 5):
        """Lässt die KI passende Songs aus der Bibliothek auswählen.

        Ablauf:
        1. Wir geben der KI eine nummerierte Liste aller Songs (mit Stichworten).
        2. Die KI antwortet im JSON-Format, z. B.:
               {"songs": [3, 0, 7], "ansage": "Hier kommt was Entspanntes!"}
        3. Wir prüfen die Nummern und machen daraus wieder Song-Objekte.

        Rückgabe: (liste_der_songs, ansagetext)
        """
        liste = "\n".join(f"{nr}: {song.beschreibung()}" for nr, song in enumerate(songs))

        system = (
            "Du bist ein DJ und wählst Songs aus einer Bibliothek aus. "
            "Antworte NUR mit JSON in genau diesem Format: "
            '{"songs": [Nummern der Songs], "ansage": "kurze, lockere DJ-Ansage auf Deutsch"}. '
            f"Wähle höchstens {anzahl} Songs, die am besten zum Wunsch passen. "
            "Verwende ausschließlich Nummern aus der Liste."
        )
        nutzer = f"Wunsch: {wunsch}\n\nBibliothek:\n{liste}"

        roh = await self._anfrage(
            [{"role": "system", "content": system}, {"role": "user", "content": nutzer}],
            json_format=True,
        )

        # Antwort der KI auslesen – kleine Modelle machen manchmal Fehler,
        # deshalb prüfen wir alles vorsichtig.
        try:
            daten = json.loads(roh)
        except json.JSONDecodeError:
            return [], ""

        auswahl = []
        for nummer in daten.get("songs", []):
            try:
                nummer = int(nummer)  # falls die KI "3" statt 3 schreibt
            except (TypeError, ValueError):
                continue
            if 0 <= nummer < len(songs) and songs[nummer] not in auswahl:
                auswahl.append(songs[nummer])

        return auswahl[:anzahl], str(daten.get("ansage", ""))
