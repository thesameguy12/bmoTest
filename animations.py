import math
import pygame
import config

DARK = (20, 50, 45)


def _fit(img, size):
    w, h = img.get_size()
    scale = min(size[0] / w, size[1] / h)
    img = pygame.transform.smoothscale(img, (int(w * scale), int(h * scale)))
    surf = pygame.Surface(size)
    surf.fill(config.BG_COLOR)
    surf.blit(img, ((size[0] - img.get_width()) // 2, (size[1] - img.get_height()) // 2))
    return surf.convert()


def _placeholder(name, size):
    w, h = size
    frames = []
    for i in range(2):
        s = pygame.Surface(size)
        s.fill(config.BG_COLOR)
        bob = (int(h * 0.04) if i else 0) if name == "dancing" else 0
        ey = int(h * 0.38) - (int(h * 0.06) if name == "thinking" else 0) + bob
        ex, r = int(w * 0.17), int(h * (0.06 if name in ("listening", "surprised") else 0.045))
        for sign in (-1, 1):
            cx = w // 2 + sign * ex
            if (name == "idle" and i == 1) or name == "happy" or (name == "wink" and sign == 1):   # blink / closed eyes
                pygame.draw.line(s, DARK, (cx - r, ey), (cx + r, ey), 8)
            else:
                pygame.draw.circle(s, DARK, (cx, ey), r)
        my, mw = int(h * 0.58) + bob, int(w * 0.2)
        if name == "talking":
            mh = int(h * (0.12 if i == 0 else 0.04))
            pygame.draw.ellipse(s, DARK, (w // 2 - mw // 2, my, mw, mh))
        elif name in ("listening", "surprised"):
            pygame.draw.circle(s, DARK, (w // 2, my + int(h * 0.03)), int(h * 0.04))
        else:
            pygame.draw.arc(s, DARK, (w // 2 - mw // 2, my - int(h * 0.06), mw, int(h * 0.14)),
                            math.pi, 2 * math.pi, 8)
        if name == "thinking":
            for k in range(i + 2):
                pygame.draw.circle(s, DARK, (w // 2 + (k - 1) * 40, int(h * 0.78)), 10)
        if name == "dancing":                              # floating music notes
            for k, (nx, ny) in enumerate(((0.12, 0.3), (0.86, 0.22))):
                x, y = int(w * nx), int(h * (ny - 0.05 * ((i + k) % 2)))
                pygame.draw.circle(s, DARK, (x, y), 14)
                pygame.draw.line(s, DARK, (x + 13, y), (x + 13, y - 50), 5)
        frames.append(s.convert())
    return frames


class Animation:
    def __init__(self, name, cfg, size):
        self.fps = cfg.get("fps", 4)
        self.loop = cfg.get("loop", True)
        self.frames = []
        for fn in cfg.get("frames", []):
            path = config.ASSETS_DIR / fn
            if path.exists():
                self.frames.append(_fit(pygame.image.load(str(path)).convert_alpha(), size))
            else:
                print(f"[animations] missing {path.name} -> using placeholder")
                self.frames = []
                break
        if not self.frames:
            self.frames = _placeholder(name, size)


class Animator:
    def __init__(self, size):
        cfgs = dict(config.ANIMATIONS)
        for n in ("happy", "surprised", "wink"):      # tap faces; draw happy_1.png ... to replace the placeholders
            cfgs.setdefault(n, {"frames": [f"{n}_1.png", f"{n}_2.png"], "fps": 2, "loop": True})
        self.anims = {n: Animation(n, c, size) for n, c in cfgs.items()}
        self.current, self.t = "idle", 0.0

    def set(self, name):
        if name != self.current and name in self.anims:
            self.current, self.t = name, 0.0

    def update(self, dt):
        self.t += dt

    def frame(self):
        a = self.anims[self.current]
        i = int(self.t * a.fps)
        i = i % len(a.frames) if a.loop else min(i, len(a.frames) - 1)
        return a.frames[i]
