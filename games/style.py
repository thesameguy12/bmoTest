"""Shared BMO look for the games: mint screen, dark green ink, red/green button colours."""
import pygame
import config

BG = config.BG_COLOR
PANEL = (176, 232, 208)
INK = (20, 50, 45)
RED = (214, 69, 96)
GREEN = (58, 170, 96)

_fonts = {}


def font(size):
    if size not in _fonts:
        _fonts[size] = pygame.font.Font(None, size)
    return _fonts[size]


def text(screen, s, size, color, center=None, topleft=None, topright=None):
    img = font(size).render(s, True, color)
    rect = img.get_rect()
    if center:
        rect.center = center
    elif topleft:
        rect.topleft = topleft
    elif topright:
        rect.topright = topright
    screen.blit(img, rect)
    return rect


def _hint_widths(items, fsize):
    f = font(fsize)
    r = f.get_height() // 2
    return [2 * r + 8 + f.size(label)[0] for _, label in items], r * 2


def hint_row(screen, items, cx, top, fsize):
    """Row of button hints, e.g. [("green", "again"), ("red", "menu")]."""
    f = font(fsize)
    widths, gap = _hint_widths(items, fsize)
    r = f.get_height() // 2
    x = cx - (sum(widths) + gap * (len(items) - 1)) // 2
    for (kind, label), wd in zip(items, widths):
        cy = top + r
        if kind == "triangle":
            pygame.draw.polygon(screen, INK, [(x + r, cy - r), (x, cy + r * 0.8), (x + 2 * r, cy + r * 0.8)])
        else:
            pygame.draw.circle(screen, GREEN if kind == "green" else RED, (x + r, cy), r)
        screen.blit(f.render(label, True, INK), (x + 2 * r + 8, cy - f.get_height() // 2))
        x += wd + gap
    return f.get_height()


def banner(screen, size, title, sub=None, hint_items=None):
    w, h = size
    parts = [font(max(46, h // 8)).render(title, True, INK)]
    if sub:
        parts.append(font(max(30, h // 14)).render(sub, True, INK))
    hf = max(24, h // 22)
    hint_w = 0
    if hint_items:
        ws, gap = _hint_widths(hint_items, hf)
        hint_w = sum(ws) + gap * (len(ws) - 1)
    box_w = max([p.get_width() for p in parts] + [hint_w]) + 80
    box_h = sum(p.get_height() + 10 for p in parts) + (font(hf).get_height() + 20 if hint_items else 0) + 36
    box = pygame.Rect(0, 0, box_w, box_h)
    box.center = (w // 2, h // 2)
    pygame.draw.rect(screen, PANEL, box)
    pygame.draw.rect(screen, INK, box, 5)
    y = box.y + 22
    for p in parts:
        screen.blit(p, (w // 2 - p.get_width() // 2, y))
        y += p.get_height() + 10
    if hint_items:
        hint_row(screen, hint_items, w // 2, y + 6, hf)
