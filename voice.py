"""Child-like robot voice via espeak-ng. Swap speak() later for a different TTS."""
import os
import re
import shutil
import subprocess
import tempfile
import time
import pygame
import audio
import config

_CANDIDATES = [
    "espeak-ng",
    r"C:\Program Files\eSpeak NG\espeak-ng.exe",
    r"C:\Program Files (x86)\eSpeak NG\espeak-ng.exe",
]


def _find():
    for c in _CANDIDATES:
        p = shutil.which(c) or (c if os.path.exists(c) else None)
        if p:
            return p
    return None


class Voice:
    def __init__(self):
        self.exe = _find()
        if not self.exe:
            print("[voice] espeak-ng not found - BMO will be silent (text only)")

    def speak(self, text):
        text = re.sub(r"[*_#`~]", "", text).strip()
        if not text:
            return
        if not self.exe:
            print("[BMO]", text)
            time.sleep(min(6, len(text) * 0.05))
            return
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        try:
            subprocess.run(
                [self.exe, "-v", config.ESPEAK_VOICE, "-p", str(config.ESPEAK_PITCH),
                 "-s", str(config.ESPEAK_SPEED), "-g", str(config.ESPEAK_GAP), "-w", path, text],
                check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            snd = pygame.mixer.Sound(path)
            snd.set_volume(audio.gain())
            ch = snd.play()
            while ch is not None and ch.get_busy():
                time.sleep(0.02)
        finally:
            try:
                os.remove(path)
            except OSError:
                pass
