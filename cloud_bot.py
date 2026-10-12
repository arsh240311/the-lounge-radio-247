"""
The Lounge | 24/7 Tamil Radio — Dedicated Cloud Stage Bot (DJ DUDE official#2443).
Streams 24/7 Tamil Indie & Kollywood Bangers + TN Blockbusters on Discord Stage Channel.
Runs on GitHub Actions Cloud Runner (Zero PC dependency).
"""

import asyncio
import json
import os
import random
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Optional

import discord

BASE_DIR = Path(__file__).resolve().parent
DNA_PATH = BASE_DIR / "music_dna_public.json"
FFMPEG_EXE = shutil.which("ffmpeg") or "ffmpeg"

PUBLIC_GUILD_ID = 1558929350613667911
STAGE_CHANNEL_ID = 1558932434211442769
MAX_RUNTIME_SEC = int(os.environ.get("MAX_RUNTIME_SEC", "19200"))  # 5h 20m per relay leg

CURATED_PUBLIC_TRACKS: list[str] = [
    "Sai Abhyankkar - Radhimaa Official Audio",
    "Sai Abhyankkar - Katchi Sera Official Audio",
    "Sai Abhyankkar - Aasa Kooda Official Audio",
    "Asal Kolaar - Jorthaale Official Audio",
    "Asal Kolaar - Champagini Official Audio",
    "Paal Dabba - 170CM Official Audio",
    "Paal Dabba - Galatta Aavesham Sushin Shyam Official Audio",
    "Makkamishi Brother Harris Jayaraj Paal Dabba Official Audio",
    "Sushin Shyam - Illuminati Aavesham Official Audio",
    "Sushin Shyam - Jaada Aavesham Official Audio",
    "Sushin Shyam - Kuthanthram Manjummel Boys Official Audio",
    "Pradeep Kumar - Nebulakal Manjummel Boys Official Audio",
    "Anirudh - Hukum Jailer Official Audio",
    "Anirudh - One Sun One Moon Jailer 2 Lyric Video",
    "Anirudh - Lokiverse Background Score Official",
    "Anirudh - Badass Leo Official Audio",
    "Anirudh - Naa Ready Leo Official Audio",
    "Anirudh - Vaathi Coming Master Official Audio",
    "Anirudh - Vikram Title Track Official Audio",
    "Anirudh - Pathala Pathala Vikram Official Audio",
    "Anirudh - Arabic Kuthu Halamithi Habibo Official Audio",
    "Anirudh - Kaavaalaa Jailer Official Audio",
    "Anirudh - Dippam Dappam Official Audio",
    "G.V. Prakash - Golden Sparrow Nilavuku En Mel Ennadi Kobam",
    "Sean Roldan - Chillanjirukkiye Lubber Pandhu Official Audio",
    "Santhosh Narayanan - Pottala Muttaye Thalaivan Thalaivii",
    "A.R. Rahman - Water Packet Raayan Official Audio",
    "Yuvan Shankar Raja - Matta GOAT Official Audio",
    "Hiphop Tamizha - Achacho Aranmanai 4 Official Audio",
    "G.V. Prakash - Otha Sollaala Aadukalam Official Audio",
]

BLACKLIST = [
    "1 hour",
    "slowed",
    "reverb",
    "mashup",
    "karaoke",
    "nightcore",
    "8d audio",
    "jukebox",
    "non stop",
    "nonstop",
    "shape of you",
    "ed sheeran",
]


class CloudStageRadio(discord.Client):
    def __init__(self, *, intents: discord.Intents) -> None:
        super().__init__(intents=intents)
        self.recent_played: list[str] = []
        self.current_track: Optional[dict[str, Any]] = None
        self.play_gen: int = 0
        self.volume: float = 0.65
        self._lock = asyncio.Lock()
        self.boot_ts = time.time()
        self._watchdog_started = False

    def pick_next_query(self) -> str:
        pool = list(CURATED_PUBLIC_TRACKS)
        if DNA_PATH.exists():
            try:
                dna = json.loads(DNA_PATH.read_text(encoding="utf-8"))
                st = dna.get("stations", {}).get("hype", {})
                for t in st.get("tracks", []):
                    if t not in pool and "ed sheeran" not in t.lower():
                        pool.append(t)
            except Exception:
                pass
        candidates = [c for c in pool if c not in self.recent_played[-14:]] or pool
        chosen = random.choice(candidates)
        self.recent_played.append(chosen)
        if len(self.recent_played) > 20:
            self.recent_played.pop(0)
        return chosen

    async def resolve_audio_buffer(self, query: str) -> Optional[dict[str, Any]]:
        search_target = query if query.startswith("http") else f"ytsearch1:{query}"

        def _extract() -> Optional[dict[str, Any]]:
            for old_f in BASE_DIR.glob("cloud_buf_*"):
                try:
                    old_f.unlink()
                except Exception:
                    pass
            out_tmpl = str(BASE_DIR / "cloud_buf_%(id)s.%(ext)s")
            cmd = [
                "yt-dlp",
                "--no-playlist",
                "--no-simulate",
                "--extractor-args",
                "youtube:player_client=android_vr,ios,web",
                "-f",
                "bestaudio[ext=webm]/bestaudio/best",
                "--print",
                "%(id)s|||%(title)s|||%(duration)s|||%(webpage_url)s",
                "-o",
                out_tmpl,
                "--quiet",
                "--no-warnings",
                search_target,
            ]
            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=40,
                    encoding="utf-8",
                    errors="replace",
                )
                lines = [ln.strip() for ln in proc.stdout.splitlines() if "|||" in ln]
                if not lines:
                    print(f"[yt-dlp stderr]: {proc.stderr[:250]}", flush=True)
                    return None
                parts = lines[0].split("|||")
                vid_id = parts[0].strip()
                title = parts[1].strip() if len(parts) > 1 else query
                duration = int(float(parts[2])) if len(parts) > 2 and parts[2].replace(".", "").isdigit() else 0
                if any(bad in title.lower() for bad in BLACKLIST):
                    return None
                if duration > 0 and (duration < 45 or duration > 540):
                    return None
                matches = list(BASE_DIR.glob(f"cloud_buf_{vid_id}.*"))
                if not matches:
                    return None
                return {
                    "query": query,
                    "title": title,
                    "url": str(matches[0]),
                    "duration": duration,
                }
            except Exception as e:
                print(f"[yt-dlp error]: {e}", flush=True)
                return None

        return await asyncio.to_thread(_extract)

    async def ensure_stage_speaker(self, guild: discord.Guild) -> Optional[discord.VoiceClient]:
        target_vc = guild.get_channel(STAGE_CHANNEL_ID)
        if not target_vc:
            stage_channels = getattr(guild, "stage_channels", [])
            target_vc = stage_channels[0] if stage_channels else (guild.voice_channels[0] if guild.voice_channels else None)
        if not target_vc:
            return None

        vc = guild.voice_client
        try:
            if vc:
                if vc.is_connected():
                    if vc.channel != target_vc:
                        await vc.move_to(target_vc)
                else:
                    await vc.disconnect(force=True)
                    vc = await target_vc.connect(reconnect=True, timeout=20)
            else:
                vc = await target_vc.connect(reconnect=True, timeout=20)

            if isinstance(target_vc, discord.StageChannel):
                try:
                    if not getattr(target_vc, "instance", None):
                        await target_vc.create_instance(
                            topic="📻 24/7 Tamil Hits & Indie Bangers | The Lounge FM",
                            privacy_level=discord.StagePrivacyLevel.guild_only,
                        )
                        print("[STAGE CREATED]: Started Live Stage Instance!", flush=True)
                except Exception as e:
                    print(f"[STAGE INSTANCE INFO]: {e}", flush=True)
                try:
                    await guild.me.edit(suppress=False)
                    print("[UPSTAGE SPEAKER]: Unsuppressed DJ DUDE official on Stage!", flush=True)
                except Exception as e:
                    print(f"[UNSUPPRESS INFO]: {e}", flush=True)
            return vc
        except Exception as e:
            print(f"[VC CONNECT ERROR]: {e}", flush=True)
            return None

    async def play_next(self, guild: discord.Guild) -> None:
        async with self._lock:
            vc = await self.ensure_stage_speaker(guild)
            if not vc or not vc.is_connected():
                return

            track_info = None
            for _ in range(4):
                q = self.pick_next_query()
                track_info = await self.resolve_audio_buffer(q)
                if track_info:
                    break
            if not track_info:
                return

            self.current_track = track_info
            gen = self.play_gen = self.play_gen + 1

            ffmpeg_src = discord.FFmpegPCMAudio(
                track_info["url"],
                executable=FFMPEG_EXE,
                before_options="-nostdin",
                options=f'-vn -filter:a "volume={self.volume}"',
            )

            def _after(err: Optional[Exception]) -> None:
                if self.play_gen != gen:
                    return
                if err:
                    print(f"[PLAY ERROR]: {err}", flush=True)
                asyncio.run_coroutine_threadsafe(self.play_next(guild), self.loop)

            if vc.is_playing() or vc.is_paused():
                vc.stop()
            vc.play(ffmpeg_src, after=_after)
            print(f"[THE LOUNGE 24/7 PLAYING]: {track_info['title']}", flush=True)

            try:
                short_title = track_info["title"][:65]
                await self.change_presence(
                    status=discord.Status.online,
                    activity=discord.Activity(
                        type=discord.ActivityType.listening,
                        name=f"🎧 {short_title} | The Lounge FM",
                    ),
                )
            except Exception:
                pass

    async def watchdog_loop(self) -> None:
        while not self.is_closed():
            await asyncio.sleep(15)
            if (time.time() - self.boot_ts) >= MAX_RUNTIME_SEC:
                print("[RELAY HANDOFF]: Max runtime reached, exiting cleanly for next GitHub Actions runner...", flush=True)
                await self.close()
                return
            for guild in self.guilds:
                if guild.id == PUBLIC_GUILD_ID or len(self.guilds) == 1:
                    vc = guild.voice_client
                    if not vc or not vc.is_connected() or not vc.is_playing():
                        print(f"[WATCHDOG]: Reconnecting/starting stream in {guild.name}...", flush=True)
                        await self.play_next(guild)

    async def on_ready(self) -> None:
        print(f"=== [THE LOUNGE 24/7 CLOUD RADIO ONLINE] {self.user} (Guilds: {len(self.guilds)}) ===", flush=True)
        for guild in self.guilds:
            print(f" -> Connected to guild: {guild.name} ({guild.id})", flush=True)
            await self.play_next(guild)
        if not self._watchdog_started:
            self._watchdog_started = True
            asyncio.create_task(self.watchdog_loop())

    async def on_guild_join(self, guild: discord.Guild) -> None:
        print(f"=== [JOINED GUILD] {guild.name} ({guild.id}) ===", flush=True)
        await self.play_next(guild)

    async def on_stage_instance_create(self, stage_instance: discord.StageInstance) -> None:
        try:
            guild = stage_instance.guild
            if guild.me.voice and guild.me.voice.channel == stage_instance.channel:
                await guild.me.edit(suppress=False)
        except Exception:
            pass


if __name__ == "__main__":
    token = (os.environ.get("DISCORD_TOKEN") or "").strip()
    if not token:
        tok_file = BASE_DIR / "bot_token.txt"
        if tok_file.exists():
            token = tok_file.read_text(encoding="utf-8").strip()
    if not token:
        print("Missing DISCORD_TOKEN!", flush=True)
        sys.exit(1)

    intents = discord.Intents.default()
    intents.voice_states = True
    intents.guilds = True
    client = CloudStageRadio(intents=intents)
    client.run(token)
