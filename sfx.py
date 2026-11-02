"""Little chiptune bleeps generated in code (no sound files needed)."""
import array
import pygame
import audio
import config

PRESETS = {
    "move":   [(660, 35)],
    "select": [(520, 50), (780, 70)],
    "place":  [(600, 70)],
    "eat":    [(880, 50), (1320, 70)],
    "volume": [(700, 30)],
    "over":   [(400, 120), (300, 120), (200, 260)],
    "win":    [(523, 100), (659, 100), (784, 100), (1047, 220)],
    "tie":    [(500, 120), (500, 120)],
}
_cache = {}


def _build(notes):
    freq, fmt, ch = pygame.mixer.get_init()
    if fmt != -16:
        return None
    buf = array.array("h")
    for f, ms in notes:
        n = int(freq * ms / 1000)
        for i in range(n):
            v = 0
            if f:
                v = 7000 if int(i * f * 2 / freq) % 2 == 0 else -7000
                v = int(v * (1 - 0.7 * i / n))
            for _ in range(ch):
                buf.append(v)
    return pygame.mixer.Sound(buffer=buf.tobytes())


def play(name):
    if not config.SFX:
        return
    try:
        if name not in _cache:
            _cache[name] = _build(PRESETS[name])
        snd = _cache[name]
        if snd:
            snd.set_volume(audio.gain())
            snd.play()
    except Exception:
        pass
