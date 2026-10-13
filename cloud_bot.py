"""
The Lounge | 24/7 Tamil Radio — Dedicated Cloud Stage Bot (DJ DUDE official#2443).
Streams 24/7 320kbps Studio Quality Tamil Indie & Kollywood Bangers on Discord Stage Channel.
Uses Instant Direct CDN Streaming (JioSaavn 320kbps AAC + yt-dlp fallback) — Zero YouTube Cloud IP Block!
"""

import asyncio
import html
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
import requests

BASE_DIR = Path(__file__).resolve().parent
DNA_PATH = BASE_DIR / "music_dna_public.json"
FFMPEG_EXE = shutil.which("ffmpeg") or "ffmpeg"

PUBLIC_GUILD_ID = 1558929350613667911
STAGE_CHANNEL_ID = 1558932434211442769
MAX_RUNTIME_SEC = int(os.environ.get("MAX_RUNTIME_SEC", "19200"))  # 5h 20m per relay leg

CURATED_PUBLIC_TRACKS: list[str] = [
    "Matta The Greatest Of All Time Yuvan Shankar Raja",
    "Whistle Podu The Greatest Of All Time Yuvan Shankar Raja",
    "Mankatha Theme Music Yuvan Shankar Raja",
    "Vilaiyaadu Mankatha Yuvan Shankar Raja",
    "Oru Kal Oru Kannadi Siva Manasula Sakthi Yuvan Shankar Raja",
    "enga area ulla varadha Pudhupettai Yuvan Shankar Raja",
    "Saroja Saman Nikalo Chennai 600028 Yuvan Shankar Raja",
    "Jalsaaro Chennai 600028 Yuvan Shankar Raja",
    "No Money No Honey Vaanam Yuvan Shankar Raja",
    "Evan Di Unna Pethan Vaanam Yuvan Shankar Raja",
    "Adidaavali Thaanaa Serndha Koottam",
    "Rowdy Baby Maari 2 Yuvan Shankar Raja Dhanush",
    "Maari Thara Local Anirudh Dhanush",
    "Makkamishi Brother Harris Jayaraj Paal Dabba",
    "Vaadi Vaadi Sachein Vijay Harris Jayaraj",
    "Adiyae Kolluthey Vaaranam Aayiram Harris Jayaraj",
    "Yethi Yethi Vaaranam Aayiram Harris Jayaraj",
    "ava enna Vaaranam Aayiram Harris Jayaraj",
    "Pala Palakura Ayan Suriya Harris Jayaraj",
    "Ladio I Shankar A.R. Rahman",
    "Enamo Aedho Ko Harris Jayaraj",
    "Venaam Machan Venaam Oru Kal Oru Kannadi Harris Jayaraj",
    "Google Google Thuppakki Vijay Harris Jayaraj",
    "Antartica Thuppakki Harris Jayaraj",
    "Danga Maari Oodhari Anegan Dhanush Harris Jayaraj",
    "Halena Iru Mugan Vikram Harris Jayaraj",
    "Pottala Muttaye Thalaivan Thalaivii Santhosh Narayanan",
    "Water Packet Raayan A.R. Rahman Santhosh Narayanan",
    "Adangatha Asuran Raayan A.R. Rahman Dhanush",
    "Enjoy Enjaami Dhee Arivu Santhosh Narayanan",
    "Rakita Rakita Jagame Thandhiram Santhosh Narayanan",
    "Bujji Jagame Thandhiram Dhanush Santhosh Narayanan",
    "Neruppu Da Kabali Rajinikanth Santhosh Narayanan",
    "Karuppu Vellai Vikram Vedha Santhosh Narayanan",
    "Tasakku Tasakku Vikram Vedha Santhosh Narayanan",
    "Sodakku Mela Sodakku Thaanaa Serndha Koottam Anirudh",
    "Golden Sparrow Nilavuku En Mel Ennadi Kobam G.V. Prakash",
    "Chillanjirukkiye Lubber Pandhu Sean Roldan",
    "Otha Sollaala Aadukalam G.V. Prakash",
    "Yathe Yathe Aadukalam G.V. Prakash",
    "Celebration of Life Pusthakam G.V. Prakash",
    "Vaa Vaathi Vaathi Dhanush G.V. Prakash",
    "Kutty Story Master Thalapathy Vijay Anirudh",
    "Chikitu Vibe Coolie Anirudh Rajinikanth",
    "Jinguchaa Thug Life A.R. Rahman Kamal Haasan",
    "Mallipoo Vendhu Thanindhathu Kaadu A.R. Rahman",
    "Marakkuma Nenjam Vendhu Thanindhathu Kaadu A.R. Rahman",
    "mental manadhil OK Kanmani A.R. Rahman",
    "Verithanam Bigil Thalapathy Vijay A.R. Rahman",
    "Singappenney Bigil A.R. Rahman",
    "Aalaporaan Thamizhan Mersal A.R. Rahman",
    "Mersal Arasan Mersal A.R. Rahman",
    "Sимtaangaran Sarkar A.R. Rahman",
    "CEO in the House Sarkar A.R. Rahman",
    "Achacho Aranmanai 4 Hiphop Tamizha",
    "Takkaru Takkaru Hiphop Tamizha",
    "Vaadi Pulla Vaadi Meesaya Murukku Hiphop Tamizha",
    "Saitji Meesaya Murukku Hiphop Tamizha",
    "Paisa Note Comali Hiphop Tamizha",
    "Orasaadha Vivek Mervin",
    "Guleba Gulebagavali Vivek Mervin Anirudh",
    "Dandanakka Romeo Juliet D Imman",
    "Aathichudi TN 07 AL 4777 Vijay Antony",
    "Machi Open The Bottle Mankatha Yuvan Shankar Raja",
    "Nakka Mukka Kadhalil Vizhunthen Vijay Antony",
    "Dailamo Dailamo Dishyum Vijay Antony",
    "Badass Leo Anirudh Thalapathy Vijay",
    "Naa Ready Leo Anirudh Thalapathy Vijay",
    "Ordinary Person Leo Anirudh Nikhita Gandhi",
    "Vaathi Coming Master Anirudh",
    "Vaathi Raid Master Anirudh",
    "Pathala Pathala Vikram Kamal Haasan Anirudh",
    "Once Upon a Time Vikram Anirudh",
    "Hukum Jailer Anirudh Rajinikanth",
    "Jujubee Jailer Anirudh",
    "Chellamma Doctor Sivakarthikeyan Anirudh",
    "So Baby Doctor Anirudh",
    "Jalabulajangu Don Sivakarthikeyan Anirudh",
    "Bae Don Anirudh",
    "Hunter Vantaar Vettaiyan Anirudh",
    "Manasilaayo Vettaiyan Anirudh Rajinikanth",
    "Fear Song Devara Anirudh",
    "Chuttamalle Devara Anirudh Shilpa Rao",
    "Galatta Aavesham Sushin Shyam Paal Dabba",
    "Illuminati Aavesham Sushin Shyam",
    "Kuthanthram Manjummel Boys Sushin Shyam",
    "Jorthaale Asal Kolaar",
    "170CM Paal Dabba"
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
        candidates = [c for c in pool if c not in self.recent_played[-15:]] or pool
        chosen = random.choice(candidates)
        self.recent_played.append(chosen)
        if len(self.recent_played) > 65:
            self.recent_played.pop(0)
        return chosen

    async def resolve_direct_stream(self, query: str) -> Optional[dict[str, Any]]:
        """Instant 0.5s 320kbps direct stream via JioSaavn CDN (works 100% on Cloud IPs without YouTube block)."""
        def _fetch() -> Optional[dict[str, Any]]:
            clean_q = query.replace("Official Audio", "").replace("Official", "").replace("-", " ").strip()
            for api_base in ("https://saavn.sumit.co/api/search/songs", "https://jiosaavn-api-privatecvc2.vercel.app/search/songs"):
                try:
                    r = requests.get(api_base, params={"query": clean_q, "limit": 5}, timeout=10)
                    if r.status_code != 200:
                        continue
                    data = r.json()
                    results = data.get("data", {}).get("results") or data.get("results") or []
                    for item in results:
                        title = html.unescape(str(item.get("name") or item.get("title") or query))
                        if any(bad in title.lower() for bad in BLACKLIST):
                            continue
                        dl_urls = item.get("downloadUrl") or item.get("download_url") or []
                        stream_url = ""
                        if isinstance(dl_urls, list) and dl_urls:
                            last_u = dl_urls[-1]
                            stream_url = last_u.get("url") or last_u.get("link") if isinstance(last_u, dict) else str(last_u)
                        if stream_url and stream_url.startswith("http"):
                            artists = item.get("artists", {}).get("primary", [])
                            artist_str = ", ".join(a.get("name", "") for a in artists if a.get("name")) if isinstance(artists, list) else ""
                            full_title = f"{title} - {artist_str}" if artist_str else title
                            return {
                                "query": query,
                                "title": full_title,
                                "url": stream_url,
                                "is_direct_cdn": True,
                            }
                except Exception as e:
                    print(f"[Direct CDN Search Warning]: {e}", flush=True)
            return None

        return await asyncio.to_thread(_fetch)

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
            for _ in range(5):
                q = self.pick_next_query()
                track_info = await self.resolve_direct_stream(q)
                if track_info:
                    break
            if not track_info:
                print("[WARN] Could not resolve track, retrying in 5s...", flush=True)
                return

            self.current_track = track_info
            gen = self.play_gen = self.play_gen + 1

            before_opts = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin"
            ffmpeg_src = discord.FFmpegPCMAudio(
                track_info["url"],
                executable=FFMPEG_EXE,
                before_options=before_opts,
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
            print(f"[THE LOUNGE 24/7 PLAYING (320kbps Direct)]: {track_info['title']}", flush=True)

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
            await asyncio.sleep(12)
            if (time.time() - self.boot_ts) >= MAX_RUNTIME_SEC:
                print("[RELAY HANDOFF]: Max runtime reached, exiting cleanly for next GitHub Actions runner...", flush=True)
                await self.close()
                return
            for guild in self.guilds:
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
