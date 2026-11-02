import random
import pygame
import config
import sfx
from . import style as st
from .base import Game

LINES = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]


def winner(b):
    for a, c, d in LINES:
        if b[a] and b[a] == b[c] == b[d]:
            return b[a], (a, c, d)
    return None, None


def minimax(b, player):
    """Score from BMO's (O) point of view: +1 BMO wins, -1 you win, 0 tie."""
    w, _ = winner(b)
    if w == "O":
        return 1
    if w == "X":
        return -1
    if all(b):
        return 0
    scores = []
    for i in range(9):
        if not b[i]:
            b[i] = player
            scores.append(minimax(b, "X" if player == "O" else "O"))
            b[i] = ""
    return max(scores) if player == "O" else min(scores)


def ai_move(b, mistake_chance):
    empty = [i for i in range(9) if not b[i]]
    if random.random() < mistake_chance:
        return random.choice(empty)
    scored = []
    for i in empty:
        b[i] = "O"
        scored.append((minimax(b, "X"), i))
        b[i] = ""
    best = max(s for s, _ in scored)
    return random.choice([i for s, i in scored if s == best])


class TicTacToe(Game):
    title = "Tic-Tac-Toe"

    def __init__(self, size):
        super().__init__(size)
        self.header = int(size[1] * 0.12)
        self.score = {"X": 0, "O": 0, "tie": 0}
        self.first = "X"
        self.reset()

    def reset(self):
        self.board = [""] * 9
        self.cursor = 4
        self.turn = self.first
        self.first = "O" if self.first == "X" else "X"     # alternate who starts
        self.over, self.win_line, self.result = False, None, ""
        self.ai_t = 0.0

    def button(self, b):
        if b == "red":
            self.done, self.exit_to = True, "menu"
            return
        if self.over:
            if b == "green":
                self.reset()
            return
        if self.turn != "X":
            return
        r, c = divmod(self.cursor, 3)
        if b == "left":
            c = max(0, c - 1)
        elif b == "right":
            c = min(2, c + 1)
        elif b == "up":
            r = max(0, r - 1)
        elif b == "down":
            r = min(2, r + 1)
        elif b == "green" and not self.board[self.cursor]:
            self._place(self.cursor, "X")
            return
        if r * 3 + c != self.cursor:
            sfx.play("move")
        self.cursor = r * 3 + c

    def _place(self, i, who):
        self.board[i] = who
        sfx.play("place")
        w, line = winner(self.board)
        if w:
            self.over, self.win_line, self.result = True, line, w
            self.score[w] += 1
            sfx.play("win" if w == "X" else "over")
            self.say("You beat BMO! Rematch!" if w == "X" else random.choice(["BMO wins! Yay!", "BMO did it!"]))
        elif all(self.board):
            self.over, self.result = True, "tie"
            self.score["tie"] += 1
            sfx.play("tie")
            self.say("A tie! Everybody wins!")
        else:
            self.turn = "O" if who == "X" else "X"
            self.ai_t = 0.0

    def update(self, dt):
        if self.over or self.turn != "O":
            return
        self.ai_t += dt
        if self.ai_t > 0.8:                                 # BMO "thinks" for a moment
            self._place(ai_move(self.board, config.TTT_MISTAKE_CHANCE), "O")

    def draw(self, screen):
        w, h = self.size
        screen.fill(st.BG)
        hs = max(28, int(self.header * 0.5))
        st.text(screen, f"YOU {self.score['X']}    BMO {self.score['O']}    TIE {self.score['tie']}",
                hs, st.INK, center=(w // 2, self.header // 2 + 6))
        side = int(min(w, h - self.header) * 0.82)
        x0, y0 = (w - side) // 2, self.header + (h - self.header - side) // 2
        cell = side // 3
        for i in (1, 2):
            pygame.draw.line(screen, st.INK, (x0 + i * cell, y0), (x0 + i * cell, y0 + side), 6)
            pygame.draw.line(screen, st.INK, (x0, y0 + i * cell), (x0 + side, y0 + i * cell), 6)

        def center(i):
            return x0 + (i % 3) * cell + cell // 2, y0 + (i // 3) * cell + cell // 2

        for i, mark in enumerate(self.board):
            cx, cy = center(i)
            p = int(cell * 0.26)
            if mark == "X":                                 # green like the green button
                pygame.draw.line(screen, st.GREEN, (cx - p, cy - p), (cx + p, cy + p), 12)
                pygame.draw.line(screen, st.GREEN, (cx - p, cy + p), (cx + p, cy - p), 12)
            elif mark == "O":                               # red like the red button
                pygame.draw.circle(screen, st.RED, (cx, cy), int(cell * 0.3), 12)
        if not self.over and self.turn == "X":
            r, c = divmod(self.cursor, 3)
            pygame.draw.rect(screen, st.INK, (x0 + c * cell + 8, y0 + r * cell + 8, cell - 16, cell - 16), 5)
        if self.win_line:
            pygame.draw.line(screen, st.INK, center(self.win_line[0]), center(self.win_line[2]), 14)
        if self.over:
            title = {"X": "YOU WIN!", "O": "BMO WINS!", "tie": "IT'S A TIE!"}[self.result]
            st.banner(screen, self.size, title, None, [("green", "again"), ("red", "menu")])
