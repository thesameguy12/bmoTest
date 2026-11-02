"""Tiny persistent settings (volume, high scores) in user_settings.json."""
import json
import config

_PATH = config.BASE_DIR / "user_settings.json"
try:
    _data = json.loads(_PATH.read_text())
except Exception:
    _data = {}


def get(key, default=None):
    return _data.get(key, default)


def put(key, value):
    _data[key] = value
    try:
        _PATH.write_text(json.dumps(_data, indent=2))
    except OSError:
        pass
