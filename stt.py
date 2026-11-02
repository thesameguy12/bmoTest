"""Always-on hearing. Listens to the mic all the time, wakes on "hey BMO",
then captures the next thing you say as the prompt. Runs locally (faster-whisper)."""
import collections
import queue
import re
import threading
import time

import config

SR = 16000
BLOCK = 480                       # 30 ms of audio per block

# whisper often spells it differently: "hey Beemo", "hey B.M.O.", "hay bemo"...
WAKE = re.compile(
    r"\b(?:hey|hay|hei|hi|hello|okay|ok)\b[\s,.!\-]*"
    r"(?:b[\s.\-]*m[\s.\-]*o|bee?[\s\-]?mo|bemo|beamo|bimo|bemu|bemmo)\b", re.I)
JUNK = {"", "you", "thank you", "thanks", "thanks for watching", "bye"}   # whisper hallucinations


class Ears:
    def __init__(self, on_wake, on_thinking, on_prompt, on_cancel):
        self.on_wake, self.on_thinking = on_wake, on_thinking
        self.on_prompt, self.on_cancel = on_prompt, on_cancel
        self.mute = False             # main loop sets this while BMO thinks/talks
        self.wake_enabled = True      # False = don't listen for "hey BMO" (e.g. music playing)
        self._force = False           # set by force_wake(): act as if "hey BMO" was heard
        self.ready, self.status = False, "loading speech model..."
        self.model = None
        self._unmute_at = 0.0

    def force_wake(self):
        if self.ready:
            self._force = True

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            from faster_whisper import WhisperModel
            self.model = WhisperModel(config.STT_MODEL, device="cpu", compute_type="int8")
            self.ready, self.status = True, "ready"
            print('[ears] ready - say "hey BMO"')
            self._listen()
        except Exception as e:
            self.status = f"unavailable: {e}"
            print("[ears]", self.status)

    def _transcribe(self, audio, wake):
        segs, _ = self.model.transcribe(
            audio, language=config.STT_LANGUAGE, beam_size=1, vad_filter=True,
            initial_prompt="Hey BMO." if wake else None)
        text = " ".join(s.text.strip() for s in segs).strip()
        print("[heard]", text)
        return text

    def _listen(self):
        import numpy as np
        import sounddevice as sd

        q = queue.Queue()
        stream = sd.InputStream(samplerate=SR, channels=1, dtype="float32", blocksize=BLOCK,
                                callback=lambda indata, f, t, s: q.put(indata[:, 0].copy()))
        preroll = collections.deque(maxlen=10)          # ~0.3 s so first syllable isn't cut
        seg, speaking, silent = [], False, 0
        noise = 0.01
        prompt_mode, deadline = False, 0.0
        blk_s = BLOCK / SR

        with stream:
            while True:
                block = q.get()
                now = time.time()
                if self.mute or now < self._unmute_at:   # don't hear BMO's own voice
                    if self.mute:
                        self._unmute_at = now + 0.6
                    seg, speaking, silent = [], False, 0
                    preroll.clear()
                    continue
                if self._force:
                    self._force = False
                    prompt_mode, deadline = True, now + config.PROMPT_TIMEOUT
                    seg, speaking, silent = [], False, 0
                    preroll.clear()
                    self.on_wake()
                if prompt_mode and not speaking and now > deadline:
                    prompt_mode = False
                    self.on_cancel()

                rms = float(np.sqrt(np.mean(block ** 2)))
                if not speaking:
                    noise = 0.95 * noise + 0.05 * rms    # adaptive background-noise estimate
                if rms > max(config.MIN_VOICE_RMS, noise * 3):
                    if not speaking:
                        speaking, seg = True, list(preroll)
                    seg.append(block)
                    silent = 0
                elif speaking:
                    seg.append(block)
                    silent += 1
                else:
                    preroll.append(block)
                    continue

                too_long = len(seg) * blk_s > config.MAX_SEGMENT
                if not (silent * blk_s >= config.SILENCE_END or too_long):
                    continue

                audio = np.concatenate(seg)
                seg, speaking, silent = [], False, 0
                preroll.clear()
                if len(audio) < 0.3 * SR:
                    continue

                if prompt_mode:                           # this utterance is the prompt
                    prompt_mode = False
                    self.on_thinking()
                    text = self._transcribe(audio, wake=False)
                    if text.lower().strip(" .!?,") in JUNK:
                        self.on_cancel()
                    else:
                        self.on_prompt(text)
                    continue

                if not self.wake_enabled:
                    continue
                text = self._transcribe(audio, wake=True)  # looking for "hey BMO"
                m = WAKE.search(text)
                if not m:
                    continue
                rest = text[m.end():].strip(" ,.!?-")
                if len(rest.split()) >= 2:                 # "hey BMO what's the weather"
                    self.on_thinking()
                    self.on_prompt(rest)
                else:                                      # just "hey BMO" -> wait for prompt
                    prompt_mode, deadline = True, time.time() + config.PROMPT_TIMEOUT
                    self.on_wake()
