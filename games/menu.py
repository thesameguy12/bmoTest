import sfx
from . import style as st
from .base import Game


class Menu(Game):
    title = "Games"

    def __init__(self, size, items):
        super().__init__(size)
        self.items = items                   # [(key, label), ...]
        self.sel = 0

    def button(self, b):
        n = len(self.items)
        if b == "up":
            self.sel = (self.sel - 1) % n
            sfx.play("move")
        elif b == "down":
            self.sel = (self.sel + 1) % n
            sfx.play("move")
        elif b == "green":
            sfx.play("select")
            self.done, self.exit_to = True, self.items[self.sel][0]
        elif b == "red":
            self.done, self.exit_to = True, None

    def draw(self, screen):
        import pygame
        w, h = self.size
        screen.fill(st.BG)
        st.text(screen, "GAMES", max(60, h // 7), st.INK, center=(w // 2, int(h * 0.16)))
        row_h = max(50, h // 9)
        top = int(h * 0.32)
        for i, (_, label) in enumerate(self.items):
            y = top + i * (row_h + 14)
            if i == self.sel:
                pygame.draw.rect(screen, st.PANEL, (w // 2 - w // 5, y, 2 * w // 5, row_h))
                pygame.draw.rect(screen, st.INK, (w // 2 - w // 5, y, 2 * w // 5, row_h), 5)
            st.text(screen, label, max(36, h // 12), st.INK, center=(w // 2, y + row_h // 2))
        st.hint_row(screen, [("green", "play"), ("red", "back")], w // 2, int(h * 0.88), max(24, h // 22))
