"""Master volume. With SYSTEM_VOLUME on, it IS the computer's real volume
(Windows slider / Debian mixer); otherwise it only scales BMO's own sounds."""
import time
import config
import store
import sysvolume

volume = max(0.0, min(1.0, float(store.get("volume", config.DEFAULT_VOLUME))))
changed_at = 0.0                  # when it last changed (the overlay shows for a moment after)
_before_mute = 0.5
_last_set = 0.0
_system = config.SYSTEM_VOLUME and sysvolume.init()

if _system:                       # the real system volume is the truth
    _cur = sysvolume.get()
    if _cur is not None:
        volume = round(_cur, 2)


def gain():
    """Volume applied inside the app. With real system volume, the app plays at full
    level and the system does the attenuating (otherwise it would be applied twice)."""
    return 1.0 if _system else volume ** 2


def set_volume(v):
    global volume, changed_at, _last_set
    volume = round(max(0.0, min(1.0, v)), 2)
    changed_at = _last_set = time.time()
    store.put("volume", volume)
    if _system:
        sysvolume.set(volume)


def change(delta):
    global volume
    if _system and time.time() - _last_set > 5:            # someone may have used the system slider
        cur = sysvolume.get()
        if cur is not None:
            volume = round(cur, 2)
    set_volume(volume + delta)


def mute():
    global _before_mute
    if volume > 0:
        _before_mute = volume
    set_volume(0.0)


def unmute():
    set_volume(_before_mute if volume == 0 else volume)
