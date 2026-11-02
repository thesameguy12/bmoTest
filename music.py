"""Music player: your own files in music/ first, then free Creative Commons music
from Jamendo (needs a free JAMENDO_CLIENT_ID in config.py)."""
import os
import random
import re
import tempfile
import threading
import time
from pathlib import Path

import pygame
import requests

import audio
import config

EXTS = {".mp3", ".ogg", ".wav", ".flac"}
FILLER = {"the", "a", "an", "some", "song", "songs", "music", "by", "please", "track",
          "for", "me", "something", "play", "called", "named", "from", "of"}


def _pretty(stem):
    return re.sub(r"[_\-]+", " ", stem).strip()


class Music:
    def __init__(self):
        self.title, self.source = "", None
        self.active = False       # a track is loaded (playing, paused or held)
        self.paused = False       # paused by the user
        self.held = False         # paused automatically while BMO listens/talks
        self._lock = threading.RLock()
        self._tmpdir = None
        self._cur_tmp = None

    @property
    def playing(self):
        return self.active and not self.paused

    # ---------- helpers ----------
    def _tracks(self):
        found = []
        if config.MUSIC_DIR.exists():
            for root, _, files in os.walk(config.MUSIC_DIR):
                for f in files:
                    if Path(f).suffix.lower() in EXTS:
                        found.append(Path(root) / f)
        return found

    def _play_file(self, path, title, source, temp=False):
        with self._lock:
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(audio.gain())
            pygame.mixer.music.play()
            self.title, self.source = title, source
            self.active, self.paused, self.held = True, False, False
            old, self._cur_tmp = self._cur_tmp, (str(path) if temp else None)
            if old and old != self._cur_tmp:
                try:
                    os.remove(old)
                except OSError:
                    pass

    def _jamendo(self, words):
        params = {"client_id": config.JAMENDO_CLIENT_ID, "format": "json", "limit": 8,
                  "audioformat": "mp32"}
        if words:
            params["search"] = " ".join(words)
        else:
            params["order"] = "popularity_week"
        data = requests.get("https://api.jamendo.com/v3.0/tracks/", params=params, timeout=10).json()
        results = [x for x in data.get("results", []) if x.get("audio")]
        if not results:
            return None
        return results[0] if words else random.choice(results)

    def _download(self, url):
        if self._tmpdir is None:
            self._tmpdir = tempfile.mkdtemp(prefix="bmo_music_")
        path = os.path.join(self._tmpdir, f"track_{int(time.time())}.mp3")
        with requests.get(url, stream=True, timeout=20) as r:
            r.raise_for_status()
            with open(path, "wb") as f:
                for chunk in r.iter_content(65536):
                    f.write(chunk)
        return path

    # ---------- commands ----------
    def play_query(self, query):
        """Returns the line BMO should say."""
        words = [w for w in re.findall(r"\w+", query.lower()) if w not in FILLER]
        tracks = self._tracks()
        if tracks:
            if not words:
                p = random.choice(tracks)
                self._play_file(p, _pretty(p.stem), "local")
                return f"BMO is playing {_pretty(p.stem)}!"
            best, cands = 0, []
            for p in tracks:
                name = (p.stem + " " + p.parent.name).lower()
                score = sum(1 for w in words if w in name)
                if score > best:
                    best, cands = score, [p]
                elif score == best and score > 0:
                    cands.append(p)
            if cands and best >= (len(words) + 1) // 2:
                p = random.choice(cands)
                self._play_file(p, _pretty(p.stem), "local")
                return f"BMO is playing {_pretty(p.stem)}!"

        if not config.JAMENDO_CLIENT_ID:
            print("[music] no local match and no JAMENDO_CLIENT_ID set in config.py")
            return "BMO could not find that song on his hard drive."
        try:
            t = self._jamendo(words)
            if not t:
                return "BMO could not find that song."
            path = self._download(t["audio"])
            self._play_file(path, f"{t['name']} by {t['artist_name']}", "web", temp=True)
            return f"BMO is playing {t['name']}!"
        except Exception as e:
            print("[music] web error:", e)
            return "BMO could not reach the music place."

    def stop(self):
        with self._lock:
            try:
                pygame.mixer.music.stop()
                if hasattr(pygame.mixer.music, "unload"):
                    pygame.mixer.music.unload()
            except pygame.error:
                pass
            self.active = self.paused = self.held = False
            if self._cur_tmp:
                try:
                    os.remove(self._cur_tmp)
                except OSError:
                    pass
                self._cur_tmp = None

    def pause(self):
        with self._lock:
            if self.active and not self.paused:
                pygame.mixer.music.pause()
                self.paused = True

    def resume(self):
        with self._lock:
            if self.active and self.paused:
                pygame.mixer.music.unpause()
                self.paused, self.held = False, False

    def hold(self):
        """Pause automatically while BMO listens or talks."""
        with self._lock:
            if self.active and not self.paused and not self.held:
                pygame.mixer.music.pause()
                self.held = True

    def release(self):
        with self._lock:
            if self.held:
                self.held = False
                if not self.paused:
                    pygame.mixer.music.unpause()

    def apply_volume(self):
        if self.active:
            pygame.mixer.music.set_volume(audio.gain())

    def poll(self):
        """Call every frame: detects the end of a track."""
        try:
            with self._lock:
                if not self.active or self.paused or self.held or pygame.mixer.music.get_busy():
                    return
                src = self.source
            if src == "local" and config.MUSIC_CONTINUE:
                tracks = self._tracks()
                if tracks:
                    p = random.choice(tracks)
                    self._play_file(p, _pretty(p.stem), "local")
                    return
            self.stop()
        except Exception as e:
            print("[music]", e)
            self.stop()
