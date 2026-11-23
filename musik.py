"""
musik.py – Deine Musikbibliothek
================================

Der Bot spielt Musikdateien aus dem Ordner "musik" ab.
Damit die KI weiß, welcher Song wozu passt, kannst du in der Datei
"musik/songs.json" für jeden Song Titel, Künstler und Stichworte (Tags)
eintragen, z. B. "entspannt", "party", "lernen", "gaming".

Songs, die NICHT in songs.json stehen, werden trotzdem gefunden –
dann wird einfach der Dateiname als Titel benutzt (ohne Tags).
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

# Dateitypen, die FFmpeg abspielen kann
ERLAUBTE_ENDUNGEN = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}


@dataclass
class Song:
    """Ein Song = eine Datei plus ein paar Infos dazu."""
    datei: Path
    titel: str
    kuenstler: str = ""
    tags: list[str] = field(default_factory=list)

    def anzeige(self) -> str:
        """So wird der Song in Discord angezeigt."""
        return f"{self.titel} – {self.kuenstler}" if self.kuenstler else self.titel

    def beschreibung(self) -> str:
        """So bekommt die KI den Song zu sehen (mit Stichworten)."""
        tags = ", ".join(self.tags) if self.tags else "keine Stichworte"
        return f"{self.anzeige()} [{tags}]"


def bibliothek_laden(ordner: Path) -> list[Song]:
    """Liest alle Musikdateien im Ordner ein und ergänzt die Infos aus songs.json."""
    ordner.mkdir(exist_ok=True)

    # 1. Infos aus songs.json lesen (falls vorhanden)
    infos = {}
    info_datei = ordner / "songs.json"
    if info_datei.exists():
        with open(info_datei, encoding="utf-8") as f:
            for eintrag in json.load(f):
                infos[eintrag["datei"]] = eintrag

    # 2. Alle Musikdateien im Ordner durchgehen
    songs = []
    for datei in sorted(ordner.iterdir()):
        if datei.suffix.lower() not in ERLAUBTE_ENDUNGEN:
            continue  # z. B. songs.json oder Bilder überspringen
        info = infos.get(datei.name, {})
        songs.append(Song(
            datei=datei,
            titel=info.get("titel", datei.stem),  # stem = Dateiname ohne Endung
            kuenstler=info.get("kuenstler", ""),
            tags=info.get("tags", []),
        ))
    return songs


def suche(songs: list[Song], text: str) -> list[Song]:
    """Einfache Suche nach Titel oder Künstler (ohne KI)."""
    text = text.lower()
    return [s for s in songs if text in s.titel.lower() or text in s.kuenstler.lower()]
