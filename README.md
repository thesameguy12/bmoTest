# BMO - setup

1. Python 3.10+  ->  `pip install -r requirements.txt`
2. Ollama: https://ollama.com  ->  `ollama pull qwen2.5:1.5b`
3. espeak-ng (voice): Windows = installer from github.com/espeak-ng/espeak-ng/releases,
   Debian = `sudo apt install espeak-ng libportaudio2`
4. `python main.py`  (first run downloads the speech model, so it needs internet)

## Talking
Say "hey BMO" (then pause and ask, or say it all in one go). BMO is deaf while he
thinks/talks. Voice commands that never touch the LLM: "volume up/down", "volume 40",
"mute", "play <song>", "stop the music", "pause", "play snake", "play tic tac toe", "games".

## Buttons (the Arduino just types these keys - change them in config.BUTTONS)
| button   | key   | on the face screen           | in a game              |
|----------|-------|------------------------------|------------------------|
| d-pad    | arrows| up/down = volume             | move                   |
| green    | Z     | open games menu              | confirm / play again   |
| red      | X     | stop music                   | back to menu           |
| triangle | C     | same as saying "hey BMO"     | pause (Snake)          |
ENTER = type instead, ESC = quit.

## Music
Drop mp3/ogg/wav files into `music/` ("play <part of the filename>").
For online free (Creative Commons) music: free key at developer.jamendo.com ->
JAMENDO_CLIENT_ID in config.py.

## Volume
The volume buttons/commands change the real computer volume (config.SYSTEM_VOLUME).
Windows: `pip install pycaw` (already in requirements). Debian: needs `pactl`, `wpctl` or `amixer`
(`sudo apt install alsa-utils` if none is installed).

## Idle clock / subtitles
IDLE_CLOCK, IDLE_CLOCK_AFTER, SUBTITLES in config.py.
