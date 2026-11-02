"""All settings in one place. Edit this file, not the code."""
from pathlib import Path

BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"      # put your PNGs here

# ---------- Display ----------
FULLSCREEN = True                     # False = windowed (handy while developing)
WINDOW_SIZE = (960, 600)
BG_COLOR = (111, 207, 172)            # BMO screen colour
FPS = 30

# ---------- Animations ----------
# name -> list of image files inside assets/ (+ speed). Add your own names here.
# Missing files? A drawn placeholder face is used so the app always runs.
ANIMATIONS = {
    "idle":      {"frames": ["idle_1.png", "idle_2.png"],           "fps": 2, "loop": True},
    "listening": {"frames": ["listening_1.png", "listening_2.png"], "fps": 2, "loop": True},
    "thinking":  {"frames": ["thinking_1.png", "thinking_2.png"],   "fps": 3, "loop": True},
    "talking":   {"frames": ["talking_1.png", "talking_2.png"],     "fps": 8, "loop": True},
    "dancing":   {"frames": ["dancing_1.png", "dancing_2.png"],     "fps": 4, "loop": True},  # while music plays
}

# ---------- Brain (Ollama) ----------
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:1.5b"     # alternatives: "llama3.2:1b", "gemma3:1b" (avoid reasoning models: slow + break the web router)
NUM_CTX = 4096             # keep the SAME for every call, changing it makes Ollama reload the model
MAX_TOKENS = 300           # max length of one reply, in tokens (~4 tokens per word-ish; 1 sentence ~ 20-30)
HISTORY_TURNS = 4          # how many past exchanges BMO remembers

# ---------- Internet ----------
CITY = "Maribor"           # default city for weather
NEWS_FEED = "https://feeds.bbci.co.uk/news/world/rss.xml"
WEB_RESULTS = 4            # search results given to the model
FETCH_PAGES = True         # also read the text of the top result
PAGE_CHARS = 1200          # more = better answers but MUCH slower on a Celeron

# ---------- Hearing (always listening, wake phrase: "hey BMO") ----------
STT_MODEL = "tiny.en"      # "base.en" is more accurate but ~2x slower
STT_LANGUAGE = "en"
MIN_VOICE_RMS = 0.015      # mic loudness that counts as speech; raise if it reacts to noise,
                           # lower if it doesn't hear you (quiet mics)
SILENCE_END = 0.8          # seconds of silence that end a sentence
MAX_SEGMENT = 12           # longest single utterance in seconds
PROMPT_TIMEOUT = 8         # after "hey BMO", seconds to wait for you to start talking

# ---------- Subtitles ----------
SUBTITLES = True           # show what BMO says at the bottom of the screen
SUBTITLE_SIZE = 0.06       # text height as a fraction of screen height

# ---------- Voice (espeak-ng) ----------
ESPEAK_VOICE = "en-us+f5"  # f1-f5 female, m1-m7 male variants
ESPEAK_PITCH = 90          # 0-99, higher = more child-like
ESPEAK_SPEED = 170         # words per minute
ESPEAK_GAP = 2             # pause between words (10ms units)

# ---------- Master volume ----------
SYSTEM_VOLUME = True       # True = change the REAL computer volume (Windows / Debian). False = app-only volume
DEFAULT_VOLUME = 0.7       # only used when SYSTEM_VOLUME is False or unavailable
VOLUME_STEP = 0.1          # per "volume up/down" or d-pad press
VOLUME_OVERLAY_SECONDS = 1.5
VOLUME_ON_COLOR = (20, 50, 45)      # lit arcs  (put his eye colour here if you like)
VOLUME_OFF_COLOR = (150, 185, 172)  # unlit arcs (the gray)
VOLUME_SHOW_PERCENT = True

# ---------- Music ----------
MUSIC_DIR = BASE_DIR / "music"      # drop mp3/ogg/wav files here (subfolders ok)
MUSIC_CONTINUE = True               # after a local track ends, shuffle to another
MUSIC_WAKEWORD = False              # listen for "hey BMO" while music plays? (unreliable, use the triangle button)
JAMENDO_CLIENT_ID = ""              # free key from developer.jamendo.com -> enables online search of free music

# ---------- Idle clock ----------
IDLE_CLOCK = True                   # show a 24h clock instead of the face when idle
IDLE_CLOCK_AFTER = 120              # seconds of inactivity before the clock appears
IDLE_CLOCK_FORMAT = "%H:%M"         # 24-hour time
IDLE_CLOCK_COLOR = (70, 150, 125)
IDLE_CLOCK_BG = (0, 0, 0)
IDLE_CLOCK_WITH_MUSIC = False       # False = BMO keeps dancing instead while music plays

# ---------- Games & buttons ----------
SFX = True                          # chiptune bleeps
GAME_VOICE = True                   # BMO comments on game results
TTT_MISTAKE_CHANCE = 0.25           # 0 = unbeatable tic-tac-toe, higher = easier
# Logical button -> keyboard key name. The Arduino just has to type these keys.
BUTTONS = {
    "up": "up", "down": "down", "left": "left", "right": "right",
    "green": "z", "red": "x", "triangle": "c",
}
