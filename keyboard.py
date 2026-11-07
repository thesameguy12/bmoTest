"""On-screen keyboard for the touch screen (Linux can't pop one up by itself, so BMO draws his own)."""
import pygame

INK = (20, 50, 45)
PANEL = (176, 232, 208)
GREEN = (58, 170, 96)

ROWS = [
    list("1234567890"),
    list("qwertyuiop"),
    list("asdfghjkl"),
    ["<shift>"] + list("zxcvbnm") + ["<back>"],
    ["<close>", ",", " ", ".", "?", "<send>"],
]
WEIGHT = {"<shift>": 1.6, "<back>": 1.6, "<close>": 1.6, "<send>": 1.8, " ": 4.5}
LABEL = {"<shift>": "SHIFT", "<back>": "DEL", "<close>": "X", "<send>": "SEND", " ": "space"}


class OnScreenKeyboard:
    def __init__(self, size):
        w, h = size
        self.height = int(h * 0.48)
        self.top = h - self.height
        self.shift = False
        self.font = pygame.font.Font(None, max(26, self.height // 7))
        self.keys = []                                   # (rect, value)
        pad = max(4, w // 160)
        row_h = (self.height - pad * (len(ROWS) + 1)) // len(ROWS)
        for r, row in enumerate(ROWS):
            unit = (w - pad * (len(row) + 1)) / sum(WEIGHT.get(k, 1.0) for k in row)
            x, y = pad, self.top + pad + r * (row_h + pad)
            for k in row:
                kw = int(unit * WEIGHT.get(k, 1.0))
                self.keys.append((pygame.Rect(x, y, kw, row_h), k))
                x += kw + pad

    def hit(self, pos):
        """Returns a character, "<back>", "<send>", "<close>", or None (shift just toggles)."""
        for rect, k in self.keys:
            if rect.collidepoint(pos):
                if k == "<shift>":
                    self.shift = not self.shift
                    return None
                if len(k) == 1 and k.isalpha() and self.shift:
                    self.shift = False
                    return k.upper()
                return k
        return None

    def draw(self, screen):
        pygame.draw.rect(screen, INK, (0, self.top, screen.get_width(), self.height))
        for rect, k in self.keys:
            on = k == "<shift>" and self.shift
            pygame.draw.rect(screen, GREEN if on else PANEL, rect, border_radius=8)
            label = LABEL.get(k, k.upper() if self.shift else k)
            img = self.font.render(label, True, INK)
            screen.blit(img, img.get_rect(center=rect.center))
