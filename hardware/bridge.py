"""Reads button presses from the Arduino over USB serial and types the matching
keys (the ones in ../config.py -> BUTTONS). Run it next to BMO:

    python bridge.py            # auto-detects the Arduino
    python bridge.py COM5       # or /dev/ttyUSB0 on Linux

Needs: pip install pyserial pynput   (Linux: X11/Xfce session, user in the 'dialout' group)
"""
import sys
import time
from pathlib import Path

import serial
import serial.tools.list_ports
from pynput.keyboard import Controller, Key

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402

SPECIAL = {"up": Key.up, "down": Key.down, "left": Key.left, "right": Key.right,
           "return": Key.enter, "space": Key.space, "escape": Key.esc}
kb = Controller()
held = set()


def key_for(button):
    name = config.BUTTONS.get(button)
    return SPECIAL.get(name, name) if name else None


def find_port():
    ports = list(serial.tools.list_ports.comports())
    hints = ("arduino", "ch340", "ch341", "cp210", "ftdi", "wch", "usb serial", "usb-serial")
    for p in ports:
        text = f"{p.description} {p.manufacturer}".lower()
        if any(h in text for h in hints):
            return p.device
    return ports[0].device if ports else None


def release_all():
    for k in list(held):
        kb.release(k)
        held.discard(k)


def run(port):
    with serial.Serial(port, 115200, timeout=1) as ser:
        print(f"[bridge] connected on {port}")
        ser.reset_input_buffer()
        while True:
            line = ser.readline().decode(errors="ignore").strip()
            if not line:
                continue
            try:
                button, state = line.split()
            except ValueError:
                continue
            key = key_for(button)
            if key is None:
                continue
            if state == "1":
                kb.press(key)
                held.add(key)
            else:
                kb.release(key)
                held.discard(key)


def main():
    wanted = sys.argv[1] if len(sys.argv) > 1 else None
    while True:                                     # reconnect if the cable is unplugged
        port = wanted or find_port()
        if not port:
            print("[bridge] no serial device found, retrying...")
            time.sleep(2)
            continue
        try:
            run(port)
        except (serial.SerialException, OSError) as e:
            print("[bridge] lost connection:", e)
            release_all()
            time.sleep(2)
        except KeyboardInterrupt:
            release_all()
            return


if __name__ == "__main__":
    main()
