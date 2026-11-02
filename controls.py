"""Turns keyboard keys into logical BMO buttons (dpad, green, red, triangle).
The future Arduino only has to type the keys listed in config.BUTTONS."""
import pygame
import config

_map = {}


def to_button(key):
    if not _map:
        for logical, name in config.BUTTONS.items():
            try:
                _map[pygame.key.key_code(name)] = logical
            except ValueError:
                print(f"[controls] unknown key name '{name}' for button '{logical}'")
    return _map.get(key)
