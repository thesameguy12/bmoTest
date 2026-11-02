"""Controls the REAL system volume.
Windows: pycaw.  Linux/Debian: pactl (PulseAudio/PipeWire), wpctl (PipeWire) or amixer (ALSA)."""
import re
import shutil
import subprocess
import sys
import threading

_backend = None
_started = False
_target = None
_lock = threading.Lock()
_event = threading.Event()
_tls = threading.local()


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=3).stdout


# ---------- Windows ----------
def _win(op, v=None):
    import comtypes
    from comtypes import CLSCTX_ALL
    from ctypes import POINTER, cast
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    if not getattr(_tls, "com", False):                 # COM must be initialised per thread
        try:
            comtypes.CoInitialize()
        except OSError:
            pass
        _tls.com = True
    dev = AudioUtilities.GetSpeakers()
    if hasattr(dev, "EndpointVolume"):                  # newer pycaw
        ep = dev.EndpointVolume
    else:                                               # older pycaw
        ep = cast(dev.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None), POINTER(IAudioEndpointVolume))
    if op == "get":
        return float(ep.GetMasterVolumeLevelScalar())
    ep.SetMasterVolumeLevelScalar(v, None)
    if v > 0:
        ep.SetMute(0, None)                             # un-mute if the system was muted


# ---------- read / write ----------
def get():
    """Current system volume 0.0-1.0, or None if unknown."""
    try:
        if _backend == "win":
            return _win("get")
        if _backend == "pactl":
            m = re.search(r"(\d+)%", _run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"]))
            return int(m.group(1)) / 100 if m else None
        if _backend == "wpctl":
            m = re.search(r"Volume:\s*([\d.]+)", _run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"]))
            return float(m.group(1)) if m else None
        if _backend == "amixer":
            m = re.search(r"\[(\d+)%\]", _run(["amixer", "sget", "Master"]))
            return int(m.group(1)) / 100 if m else None
    except Exception as e:
        print("[volume] read failed:", e)
    return None


def _apply(v):
    pct = f"{int(round(v * 100))}%"
    if _backend == "win":
        _win("set", v)
    elif _backend == "pactl":
        _run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", pct])
        if v > 0:
            _run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"])
    elif _backend == "wpctl":
        _run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", pct])
        if v > 0:
            _run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "0"])
    elif _backend == "amixer":
        _run(["amixer", "-q", "sset", "Master", pct] + (["unmute"] if v > 0 else []))


def _loop():
    """Applies changes in the background so button presses never stall the screen."""
    global _target
    while True:
        _event.wait()
        _event.clear()
        with _lock:
            v, _target = _target, None
        if v is None:
            continue
        try:
            _apply(v)
        except Exception as e:
            print("[volume] could not set system volume:", e)


def set(v):
    global _target
    if _backend is None:
        return
    with _lock:
        _target = max(0.0, min(1.0, v))
    _event.set()


def init():
    """True if the real system volume can be controlled."""
    global _backend, _started
    if _started:
        return _backend is not None
    _started = True
    for b in (["win"] if sys.platform == "win32" else ["pactl", "wpctl", "amixer"]):
        if b != "win" and not shutil.which(b):
            continue
        _backend = b
        if get() is not None:
            threading.Thread(target=_loop, daemon=True).start()
            print(f"[volume] controlling the system volume via {b}")
            return True
    _backend = None
    print("[volume] no system volume control found - falling back to an app-only volume")
    return False
