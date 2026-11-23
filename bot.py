"""
bot.py – Das Herzstück: der Discord-Bot
=======================================

Hier passiert alles, was mit Discord zu tun hat:
- Der Bot meldet sich mit deinem Token bei Discord an.
- Er registriert Slash-Befehle (/dj, /play, /skip ...).
- Er betritt Sprachkanäle und spielt Musik über FFmpeg ab.
- Für KI-Aufgaben ruft er die Klasse KI aus ki.py auf.

Starten mit:  python bot.py   (oder Doppelklick auf starten.bat)
"""

import asyncio
import os
from pathlib import Path

import discord
from discord import app_commands
from dotenv import load_dotenv

from ki import KI
from musik import Song, bibliothek_laden, suche

# ---------------------------------------------------------------------------
# 1. Einstellungen aus der Datei ".env" laden
#    (dort stehen Token & Co., damit sie nicht im Code stehen)
# ---------------------------------------------------------------------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")  # optional: deine Server-ID für sofortige Befehle
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODELL = os.getenv("OLLAMA_MODELL", "llama3.2")
FFMPEG_PFAD = os.getenv("FFMPEG_PFAD") or "ffmpeg"  # falls FFmpeg nicht im PATH ist

MUSIK_ORDNER = Path(__file__).parent / "musik"


def kuerzen(text: str, maximal: int = 1900) -> str:
    """Discord erlaubt max. 2000 Zeichen pro Nachricht – sicherheitshalber kürzen."""
    return text if len(text) <= maximal else text[:maximal] + " …"


# ---------------------------------------------------------------------------
# 2. Zustand pro Server: Jeder Discord-Server hat seine eigene Warteschlange
# ---------------------------------------------------------------------------
class ServerZustand:
    def __init__(self):
        self.warteschlange: list[Song] = []   # Songs, die noch kommen
        self.aktuell: Song | None = None      # Song, der gerade läuft
        self.textkanal = None                 # Kanal für "Jetzt läuft ..."-Meldungen


# ---------------------------------------------------------------------------
# 3. Der Bot selbst
# ---------------------------------------------------------------------------
class MusikBot(discord.Client):
    def __init__(self):
        # "Intents" legen fest, welche Ereignisse der Bot von Discord bekommt.
        # Die Standard-Intents reichen hier (inkl. Sprachkanäle).
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)  # verwaltet die Slash-Befehle
        self.ki = KI(OLLAMA_URL, OLLAMA_MODELL)
        self.songs = bibliothek_laden(MUSIK_ORDNER)
        self.zustaende: dict[int, ServerZustand] = {}

    async def setup_hook(self):
        """Wird einmal beim Start ausgeführt: Slash-Befehle bei Discord anmelden."""
        if GUILD_ID:
            # Nur für deinen Server -> Befehle sind sofort sichtbar (gut zum Testen)
            server = discord.Object(id=int(GUILD_ID))
            self.tree.copy_global_to(guild=server)
            await self.tree.sync(guild=server)
        else:
            # Für alle Server -> kann etwas dauern, bis die Befehle erscheinen
            await self.tree.sync()

    async def on_ready(self):
        print(f"✅ Eingeloggt als {self.user} – {len(self.songs)} Songs in der Bibliothek")

    def zustand(self, guild_id: int) -> ServerZustand:
        """Gibt den Zustand eines Servers zurück (legt ihn beim ersten Mal an)."""
        return self.zustaende.setdefault(guild_id, ServerZustand())

    async def naechster_song(self, guild: discord.Guild):
        """Spielt den nächsten Song aus der Warteschlange ab."""
        z = self.zustand(guild.id)
        vc = guild.voice_client  # die Verbindung zum Sprachkanal

        if vc is None or not vc.is_connected():
            z.warteschlange.clear()
            z.aktuell = None
            return

        if not z.warteschlange:
            z.aktuell = None
            if z.textkanal:
                await z.textkanal.send("📭 Die Warteschlange ist leer. Wünsch dir was mit `/dj`!")
            return

        song = z.warteschlange.pop(0)
        z.aktuell = song

        # FFmpeg wandelt die Musikdatei in das Audioformat um, das Discord braucht
        quelle = discord.FFmpegPCMAudio(str(song.datei), executable=FFMPEG_PFAD)

        def danach(fehler):
            # Wird automatisch aufgerufen, wenn der Song zu Ende ist (oder übersprungen wurde).
            # Diese Funktion läuft in einem anderen "Thread", deshalb übergeben wir den
            # nächsten Schritt mit run_coroutine_threadsafe sicher an den Bot zurück.
            if fehler:
                print(f"Fehler beim Abspielen: {fehler}")
            asyncio.run_coroutine_threadsafe(self.naechster_song(guild), self.loop)

        vc.play(quelle, after=danach)

        if z.textkanal:
            await z.textkanal.send(f"▶️ Jetzt läuft: **{song.anzeige()}**")


bot = MusikBot()


# ---------------------------------------------------------------------------
# 4. Hilfsfunktion: dem Sprachkanal des Nutzers beitreten
# ---------------------------------------------------------------------------
async def verbinden(interaction: discord.Interaction) -> discord.VoiceClient | None:
    """Verbindet den Bot mit dem Sprachkanal, in dem der Nutzer gerade ist."""
    nutzer = interaction.user
    if not isinstance(nutzer, discord.Member) or nutzer.voice is None or nutzer.voice.channel is None:
        return None  # Nutzer ist in keinem Sprachkanal

    kanal = nutzer.voice.channel
    vc = interaction.guild.voice_client
    if vc is None:
        vc = await kanal.connect()
    elif vc.channel != kanal:
        await vc.move_to(kanal)
    return vc


async def starten_falls_still(interaction: discord.Interaction, vc: discord.VoiceClient):
    """Startet die Wiedergabe, falls gerade nichts läuft."""
    if not vc.is_playing() and not vc.is_paused():
        await bot.naechster_song(interaction.guild)


# ---------------------------------------------------------------------------
# 5. Die Slash-Befehle
#    @bot.tree.command registriert eine Funktion als Befehl in Discord.
#    @app_commands.describe beschreibt die Eingabefelder.
#    @app_commands.guild_only verhindert die Nutzung in Direktnachrichten.
# ---------------------------------------------------------------------------
@bot.tree.command(name="dj", description="Die KI sucht passende Musik zu deinem Wunsch aus")
@app_commands.describe(wunsch="z. B. 'was Entspanntes zum Lernen' oder 'Party!'")
@app_commands.guild_only()
async def dj(interaction: discord.Interaction, wunsch: str):
    # defer = "Bot denkt nach ..." – nötig, weil die KI länger als 3 Sekunden brauchen kann
    await interaction.response.defer(thinking=True)

    if not bot.songs:
        await interaction.followup.send("🎵 Die Bibliothek ist leer. Leg Musikdateien in den Ordner `musik`.")
        return

    vc = await verbinden(interaction)
    if vc is None:
        await interaction.followup.send("🔇 Geh zuerst in einen Sprachkanal.")
        return

    try:
        auswahl, ansage = await bot.ki.songs_auswaehlen(wunsch, bot.songs)
    except Exception as fehler:
        print(f"KI-Fehler: {fehler}")
        await interaction.followup.send("🤖 Die KI ist nicht erreichbar. Läuft Ollama?")
        return

    if not auswahl:
        await interaction.followup.send("🤔 Dazu habe ich nichts Passendes gefunden. Versuch's anders formuliert!")
        return

    z = bot.zustand(interaction.guild.id)
    z.textkanal = interaction.channel
    z.warteschlange.extend(auswahl)

    liste = "\n".join(f"• {s.anzeige()}" for s in auswahl)
    await interaction.followup.send(kuerzen(f"🎧 {ansage}\n\n**Neu in der Warteschlange:**\n{liste}"))
    await starten_falls_still(interaction, vc)


@bot.tree.command(name="play", description="Einen bestimmten Song abspielen (Suche nach Titel/Künstler)")
@app_commands.describe(titel="Titel oder Künstler")
@app_commands.guild_only()
async def play(interaction: discord.Interaction, titel: str):
    treffer = suche(bot.songs, titel)
    if not treffer:
        await interaction.response.send_message(f"❌ Kein Song gefunden für „{titel}“.")
        return

    vc = await verbinden(interaction)
    if vc is None:
        await interaction.response.send_message("🔇 Geh zuerst in einen Sprachkanal.")
        return

    z = bot.zustand(interaction.guild.id)
    z.textkanal = interaction.channel
    z.warteschlange.append(treffer[0])
    await interaction.response.send_message(f"➕ **{treffer[0].anzeige()}** kommt in die Warteschlange.")
    await starten_falls_still(interaction, vc)


@bot.tree.command(name="skip", description="Aktuellen Song überspringen")
@app_commands.guild_only()
async def skip(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and (vc.is_playing() or vc.is_paused()):
        vc.stop()  # stop() löst automatisch "danach" aus -> nächster Song startet
        await interaction.response.send_message("⏭️ Übersprungen.")
    else:
        await interaction.response.send_message("Gerade läuft nichts.")


@bot.tree.command(name="pause", description="Musik pausieren")
@app_commands.guild_only()
async def pause(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.pause()
        await interaction.response.send_message("⏸️ Pausiert. Weiter mit `/weiter`.")
    else:
        await interaction.response.send_message("Gerade läuft nichts.")


@bot.tree.command(name="weiter", description="Pausierte Musik fortsetzen")
@app_commands.guild_only()
async def weiter(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_paused():
        vc.resume()
        await interaction.response.send_message("▶️ Weiter geht's!")
    else:
        await interaction.response.send_message("Es ist nichts pausiert.")


@bot.tree.command(name="stop", description="Musik stoppen, Warteschlange leeren und Kanal verlassen")
@app_commands.guild_only()
async def stop(interaction: discord.Interaction):
    z = bot.zustand(interaction.guild.id)
    z.warteschlange.clear()  # zuerst leeren, damit nach stop() nichts nachkommt
    vc = interaction.guild.voice_client
    if vc:
        vc.stop()
        await vc.disconnect()
    await interaction.response.send_message("⏹️ Gestoppt. Bis später! 👋")


@bot.tree.command(name="warteschlange", description="Zeigt, was gerade läuft und was als Nächstes kommt")
@app_commands.guild_only()
async def warteschlange(interaction: discord.Interaction):
    z = bot.zustand(interaction.guild.id)
    text = f"▶️ **Jetzt:** {z.aktuell.anzeige() if z.aktuell else 'nichts'}\n"
    if z.warteschlange:
        text += "\n".join(f"{i}. {s.anzeige()}" for i, s in enumerate(z.warteschlange, start=1))
    else:
        text += "Danach: nichts in der Warteschlange."
    await interaction.response.send_message(kuerzen(text))


@bot.tree.command(name="bibliothek", description="Musikordner neu einlesen und alle Songs anzeigen")
@app_commands.guild_only()
async def bibliothek(interaction: discord.Interaction):
    bot.songs = bibliothek_laden(MUSIK_ORDNER)  # neu einlesen, falls du Songs hinzugefügt hast
    if not bot.songs:
        await interaction.response.send_message("🎵 Die Bibliothek ist leer.")
        return
    liste = "\n".join(f"• {s.beschreibung()}" for s in bot.songs)
    await interaction.response.send_message(kuerzen(f"📚 **{len(bot.songs)} Songs:**\n{liste}"))


@bot.tree.command(name="frage", description="Stell der KI eine Frage")
@app_commands.describe(text="Deine Frage")
async def frage(interaction: discord.Interaction, text: str):
    await interaction.response.defer(thinking=True)
    try:
        antwort = await bot.ki.frage(text)
    except Exception as fehler:
        print(f"KI-Fehler: {fehler}")
        antwort = "🤖 Die KI ist nicht erreichbar. Läuft Ollama?"
    await interaction.followup.send(kuerzen(antwort))


# ---------------------------------------------------------------------------
# 6. Start
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("❌ Kein DISCORD_TOKEN gefunden. Hast du die Datei .env angelegt?")
    bot.run(TOKEN)
