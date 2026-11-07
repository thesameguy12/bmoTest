"""Instant local voice commands (volume, music, games). Anything not matched here
goes to the LLM. Returns (command, argument) or None."""
import re


def _norm(text):
    t = text.lower().replace("'", " ")
    t = re.sub(r"[^\w\s%]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"^((please|bmo|hey|okay|ok|can you|could you|will you|would you) )+", "", t)
    t = re.sub(r"( please| for me)$", "", t)
    return t


UP = (r"\bvolume up\b", r"\blouder\b", r"\bturn (?:it )?up\b", r"\bturn up the volume\b",
      r"\bturn the volume up\b", r"\b(?:increase|raise) (?:the )?volume\b", r"\bspeak up\b", r"\btoo quiet\b")
DOWN = (r"\bvolume down\b", r"\bquieter\b", r"\bsofter\b", r"\bturn (?:it )?down\b",
        r"\bturn down the volume\b", r"\bturn the volume down\b", r"\b(?:decrease|lower|reduce) (?:the )?volume\b",
        r"\btoo loud\b")
EMPTY_PLAY = {"music", "some music", "something", "a song", "some songs", "songs",
              "a random song", "something nice", "me something"}


LEAD = {"the", "web", "internet", "online", "net", "for", "up", "about", "this", "that", "it",
        "something", "me", "on", "google"}


def _search_query(rest):
    """'search this up on the web' -> '' (ask what to search); 'search for cats' -> 'cats'."""
    rest = re.sub(r"\b(on|in|using|via|with) (the )?(web|internet|google|net)\b", " ", rest)
    words = rest.split()
    while words and words[0] in LEAD:
        words.pop(0)
    while words and words[-1] in ("up", "please"):
        words.pop()
    return " ".join(words)


def parse(text):
    t = _norm(text)
    if not t:
        return None

    m = re.search(r"\bvolume (?:to |at )?(\d{1,3})\b|\b(\d{1,3}) percent volume\b", t)
    if m:
        return ("vol_set", min(int(m.group(1) or m.group(2)), 100) / 100)
    if re.search(r"\bvolume (?:to |at )?(max|maximum|full)\b", t):
        return ("vol_set", 1.0)
    if re.search(r"\bvolume (?:to |at )?half\b", t):
        return ("vol_set", 0.5)
    if re.fullmatch(r"un ?mute( yourself| the sound| the volume)?", t):
        return ("unmute", None)
    if re.fullmatch(r"mute( yourself| the sound| the volume)?", t):
        return ("mute", None)
    if any(re.search(p, t) for p in UP):
        return ("vol_delta", +1)
    if any(re.search(p, t) for p in DOWN):
        return ("vol_delta", -1)

    m = re.match(r"(?:search|google|look up|lookup|look it up|browse)\b(.*)$", t)
    if m:
        return ("web_search", _search_query(m.group(1)))

    if re.search(r"\b(exit|quit|close|leave|stop) (?:the |this )?game\b", t):
        return ("game_exit", None)
    if re.search(r"\b(play|start|launch|open|show|lets play|let s play)\b", t):
        if re.search(r"\bsnake\b", t):
            return ("game", "snake")
        if re.search(r"tic ?tac ?toe|n[ao]ughts and crosses", t):
            return ("game", "tictactoe")
        if re.search(r"\bgames?\b", t):
            return ("game", "menu")
    if re.fullmatch(r"(the )?games?( menu)?", t):
        return ("game", "menu")

    if t == "stop" or re.search(r"\b(stop|turn off|end)\b.*\b(music|song|playing|playback)\b", t):
        return ("music_stop", None)
    if re.fullmatch(r"pause( the)?( music| song| playback)?", t):
        return ("music_pause", None)
    if re.fullmatch(r"(resume|continue|unpause)( the)?( music| song| playback| playing)?", t):
        return ("music_resume", None)
    if re.search(r"\bwhat s (this|that|playing)\b|\bwhat song\b|\bwhich song\b|\bwhat is playing\b", t):
        return ("now_playing", None)

    m = re.match(r"play (.+)", t)
    if m:
        q = re.sub(r"\b(on|from|using) (youtube|you tube|spotify)\b", "", m.group(1)).strip()
        return ("music_play", "" if q in EMPTY_PLAY else q)
    if t in ("music", "some music"):
        return ("music_play", "")
    return None
