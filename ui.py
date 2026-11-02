"""Screen overlays: volume icon, idle clock, subtitles."""
import math
import random
import time
import pygame
import audio
import config


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _band(surf, color, c, r0, r1, a0, a1, steps=28):
    """Filled arc band (pygame's thick arcs have holes, so use a polygon)."""
    pts = []
    for i in range(steps + 1):
        a = a0 + (a1 - a0) * i / steps
        pts.append((c[0] + r1 * math.cos(a), c[1] - r1 * math.sin(a)))
    for i in range(steps, -1, -1):
        a = a0 + (a1 - a0) * i / steps
        pts.append((c[0] + r0 * math.cos(a), c[1] - r0 * math.sin(a)))
    pygame.draw.polygon(surf, color, pts)


def volume_overlay(screen, size):
    """BMO-style sound icon: a dot and three arcs that go gray -> dark with the volume."""
    w, h = size
    screen.fill(config.BG_COLOR)
    unit = h * 0.10
    r1max = unit * (1.3 + 2 * 1.15 + 0.6)
    cx, cy = int(w / 2 - (r1max - 0.55 * unit) / 2), h // 2
    pygame.draw.circle(screen, config.VOLUME_ON_COLOR, (cx, cy), int(unit * 0.55))
    for i in range(3):
        frac = max(0.0, min(1.0, audio.volume * 3 - i))      # each arc covers a third of the range
        color = _lerp(config.VOLUME_OFF_COLOR, config.VOLUME_ON_COLOR, frac)
        r0 = unit * (1.3 + i * 1.15)
        _band(screen, color, (cx, cy), r0, r0 + unit * 0.6, -math.pi / 4, math.pi / 4)
    if config.VOLUME_SHOW_PERCENT:
        font = pygame.font.Font(None, max(30, h // 10))
        img = font.render(f"{round(audio.volume * 100)}%", True, config.VOLUME_ON_COLOR)
        screen.blit(img, (w // 2 - img.get_width() // 2, int(h * 0.84)))


class IdleClock:
    """Black screen, dim 24h clock that jumps to a new spot every minute (no burn-in)."""

    def __init__(self, size):
        self.size = size
        self.font = pygame.font.Font(None, size[1] // 4)
        self.stamp, self.pos = None, (0, 0)

    def reset(self):
        self.stamp = None

    def draw(self, screen):
        t = time.strftime(config.IDLE_CLOCK_FORMAT)
        img = self.font.render(t, True, config.IDLE_CLOCK_COLOR)
        if t != self.stamp:
            self.stamp, m = t, 20
            self.pos = (random.randint(m, max(m, self.size[0] - img.get_width() - m)),
                        random.randint(m, max(m, self.size[1] - img.get_height() - m)))
        screen.fill(config.IDLE_CLOCK_BG)
        screen.blit(img, self.pos)


def wrap(text, font, max_w):
    lines, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if font.size(t)[0] <= max_w:
            cur = t
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


class Subtitles:
    def __init__(self, size):
        self.size = size
        self.font = pygame.font.Font(None, max(24, int(size[1] * config.SUBTITLE_SIZE)))
        self._text, self._surf = None, None

    def draw(self, screen, text, bottom):
        if text != self._text:
            lines = wrap(text, self.font, int(self.size[0] * 0.9))[-3:]
            lh = self.font.get_linesize()
            surf = pygame.Surface((self.size[0], len(lines) * lh + 24), pygame.SRCALPHA)
            surf.fill((0, 0, 0, 170))
            for i, line in enumerate(lines):
                img = self.font.render(line, True, (255, 255, 255))
                surf.blit(img, ((self.size[0] - img.get_width()) // 2, 12 + i * lh))
            self._text, self._surf = text, surf
        screen.blit(self._surf, (0, bottom - self._surf.get_height()))
