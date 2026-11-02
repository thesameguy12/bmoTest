class Game:
    """Every game gets button presses ("up","down","left","right","green","red","triangle"),
    updates, and draws. Set done=True (and exit_to="menu" or None) to leave."""
    title = ""

    def __init__(self, size):
        self.size = size
        self.done = False
        self.exit_to = None
        self._lines = []

    def say(self, text):
        self._lines.append(text)

    def pop_say(self):
        return self._lines.pop(0) if self._lines else None

    def button(self, name):
        pass

    def update(self, dt):
        pass

    def draw(self, screen):
        pass
