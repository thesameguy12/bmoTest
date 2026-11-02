from .menu import Menu
from .snake import Snake
from .tictactoe import TicTacToe

REGISTRY = {"snake": ("Snake", Snake), "tictactoe": ("Tic-Tac-Toe", TicTacToe)}


def create(name, size):
    if name == "menu":
        return Menu(size, [(k, v[0]) for k, v in REGISTRY.items()])
    return REGISTRY[name][1](size)
