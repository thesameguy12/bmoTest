import random
import pygame
import sfx
import store
from . import style as st
from .base import Game

DIRS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}


class Snake(Game):
    title = "Snake"

    def __init__(self, size):
        super().__init__(size)
        self.header = int(size[1] * 0.12)
        self.rows = 16
        self.cell = max(8, (size[1] - self.header - 10) // self.rows)
        self.cols = max(10, min(40, (size[0] - 20) // self.cell))
        self.x0 = (size[0] - self.cols * self.cell) // 2
        self.y0 = self.header + (size[1] - self.header - self.rows * self.cell) // 2
        self.best = int(store.get("snake_best", 0))
        self.reset()

    def reset(self):
        cx, cy = self.cols // 2, self.rows // 2
        self.body = [(cx - i, cy) for i in range(3)]       # head first
        self.dir, self.queue = (1, 0), []
        self.score, self.alive, self.paused, self.acc = 0, True, False, 0.0
        self.won = False
        self.food = self._spawn()

    def _spawn(self):
        taken = set(self.body)
        free = [(x, y) for x in range(self.cols) for y in range(self.rows) if (x, y) not in taken]
        return random.choice(free) if free else None

    def button(self, b):
        if b == "red":
            self.done, self.exit_to = True, "menu"
            return
        if not self.alive:
            if b == "green":
                self.reset()
            return
        if b == "triangle" or (b == "green" and self.paused):
            self.paused = not self.paused
            return
        if b in DIRS and not self.paused:
            last = self.queue[-1] if self.queue else self.dir
            d = DIRS[b]
            if len(self.queue) < 2 and d != last and d != (-last[0], -last[1]):
                self.queue.append(d)

    def update(self, dt):
        if self.paused or not self.alive:
            return
        self.acc += dt
        interval = max(0.07, 0.16 - 0.004 * self.score)    # speeds up as you eat
        while self.acc >= interval and self.alive:
            self.acc -= interval
            self._step()

    def _step(self):
        if self.queue:
            self.dir = self.queue.pop(0)
        nx, ny = self.body[0][0] + self.dir[0], self.body[0][1] + self.dir[1]
        eat = (nx, ny) == self.food
        solid = self.body if eat else self.body[:-1]
        if not (0 <= nx < self.cols and 0 <= ny < self.rows) or (nx, ny) in solid:
            self._die()
            return
        self.body.insert(0, (nx, ny))
        if not eat:
            self.body.pop()
            return
        self.score += 1
        sfx.play("eat")
        self.food = self._spawn()
        if self.food is None:
            self.won = True
            self._die()

    def _die(self):
        self.alive = False
        sfx.play("win" if self.won else "over")
        if self.score > self.best:
            self.best = self.score
            store.put("snake_best", self.best)
            if self.score > 2:
                self.say("New high score! BMO is so proud!")
        elif self.score == 0:
            self.say("Oh no! BMO crashed right away!")
        else:
            self.say(random.choice(["Oh no! Try again!", "Bonk! BMO hit something.", "Good game!"]))

    def draw(self, screen):
        w, h = self.size
        screen.fill(st.BG)
        hs = max(28, int(self.header * 0.55))
        st.text(screen, f"SCORE {self.score}", hs, st.INK, topleft=(24, 14))
        st.text(screen, f"BEST {self.best}", hs, st.INK, topright=(w - 24, 14))
        board = pygame.Rect(self.x0, self.y0, self.cols * self.cell, self.rows * self.cell)
        pygame.draw.rect(screen, st.PANEL, board)
        pygame.draw.rect(screen, st.INK, board.inflate(10, 10), 5)
        c = self.cell
        if self.food:
            fx, fy = self.food
            pygame.draw.rect(screen, st.RED, pygame.Rect(self.x0 + fx * c, self.y0 + fy * c, c, c).inflate(-c // 3, -c // 3))
        for i, (x, y) in enumerate(self.body):
            rect = pygame.Rect(self.x0 + x * c + 1, self.y0 + y * c + 1, c - 2, c - 2)
            pygame.draw.rect(screen, st.INK, rect)
            if i == 0:                                     # little BMO eyes on the head
                e = max(2, c // 6)
                for ex in (c // 3, 2 * c // 3):
                    pygame.draw.rect(screen, st.PANEL, (rect.x + ex - e // 2, rect.y + c // 3, e, e))
        if not self.alive:
            st.banner(screen, self.size, "YOU WIN!" if self.won else "GAME OVER", f"score {self.score}",
                      [("green", "again"), ("red", "menu")])
        elif self.paused:
            st.banner(screen, self.size, "PAUSED", None, [("triangle", "resume"), ("red", "menu")])
