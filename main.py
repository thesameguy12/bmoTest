import queue
import random
import re
import threading
import time
import pygame

import audio
import commands
import config
import controls
import games
import sfx
import ui
from animations import Animator
from brain import Brain
from music import Music
from stt import Ears
from voice import Voice


def main():
    pygame.init()
    pygame.mixer.init()
    config.MUSIC_DIR.mkdir(exist_ok=True)
    if config.FULLSCREEN:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.mouse.set_visible(False)
    else:
        screen = pygame.display.set_mode(config.WINDOW_SIZE)
    pygame.display.set_caption("BMO")
    size = screen.get_size()
    anim = Animator(size)
    font = pygame.font.Font(None, max(28, size[1] // 18))
    brain, voice, music = Brain(), Voice(), Music()
    clock_ui, subs = ui.IdleClock(size), ui.Subtitles(size)

    state = {"mode": "idle", "subtitle": "", "sub_until": 0.0,
             "active_at": time.time(), "pending_game": None}
    inbox = queue.Queue()
    game = None

    def touch():
        state["active_at"] = time.time()

    def submit(text):
        touch()
        state["mode"] = "thinking"
        inbox.put(text)

    def on_wake():
        touch()
        if state["mode"] == "idle":
            state["mode"] = "listening"

    def on_cancel():
        touch()
        if state["mode"] in ("listening", "thinking") and inbox.empty():
            state["mode"] = "idle"

    ears = Ears(on_wake=on_wake, on_thinking=lambda: state.update(mode="thinking"),
                on_prompt=submit, on_cancel=on_cancel)
    ears.start()

    def say_line(text):
        state["subtitle"] = re.sub(r"[*_#`~]", "", text).strip()
        state["sub_until"] = 0.0                          # 0 = keep showing
        state["mode"] = "talking"
        voice.speak(text)
        state["mode"] = "thinking"

    def run_command(cmd):
        """Local commands. Returns what BMO should say (or None for silence)."""
        kind, arg = cmd
        if kind == "vol_set":
            audio.set_volume(arg)
            sfx.play("volume")
        elif kind == "vol_delta":
            audio.change(arg * config.VOLUME_STEP)
            sfx.play("volume")
        elif kind == "mute":
            audio.mute()
        elif kind == "unmute":
            audio.unmute()
            sfx.play("volume")
        elif kind == "game":
            state["pending_game"] = arg
            return random.choice(["Yay! BMO loves games!", "Let's play!"])
        elif kind == "game_exit":
            state["pending_game"] = "exit"
            return "Okay! That was fun!"
        elif kind == "music_play":
            return music.play_query(arg)
        elif kind == "music_stop":
            music.stop()
            return "Okay, BMO stopped the music."
        elif kind == "music_pause":
            music.pause()
            return "Paused!"
        elif kind == "music_resume":
            music.resume()
            return "Music time again!"
        elif kind == "now_playing":
            return f"This is {music.title}." if music.active else "BMO is not playing anything."
        return None

    def worker():
        while True:
            item = inbox.get()
            try:
                if isinstance(item, tuple):               # ("say", text) from a game
                    say_line(item[1])
                else:
                    state["mode"] = "thinking"
                    cmd = commands.parse(item)
                    if cmd:
                        reply = run_command(cmd)
                        if reply:
                            say_line(reply)
                    else:
                        for sentence in brain.reply_stream(item):
                            say_line(sentence)
            except Exception as e:
                print("[error]", e)
            state["sub_until"] = time.time() + 1.5        # linger, then fade out
            state["mode"] = "idle"
            touch()

    threading.Thread(target=worker, daemon=True).start()

    typing, buf, clock_on = False, "", False
    clock = pygame.time.Clock()
    running = True
    while running:
        dt = clock.tick(config.FPS) / 1000
        now = time.time()
        ears.mute = state["mode"] in ("thinking", "talking")       # deaf while BMO is busy
        ears.wake_enabled = config.MUSIC_WAKEWORD or not music.playing

        # music: pause while BMO listens/talks, resume afterwards
        if state["mode"] in ("listening", "talking"):
            music.hold()
        elif state["mode"] == "idle":
            music.release()
        music.poll()
        music.apply_volume()

        # games asked for by voice / finished / talking
        pg = state["pending_game"]
        if pg:
            state["pending_game"] = None
            game = None if pg == "exit" else games.create(pg, size)
            touch()
        if game and game.done:
            game = games.create(game.exit_to, size) if game.exit_to else None
            touch()
        if game and config.GAME_VOICE:
            line = game.pop_say()
            if line:
                inbox.put(("say", line))

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if clock_on:                              # first key press only wakes the screen
                    touch()
                    continue
                touch()
                btn = controls.to_button(ev.key)
                if typing:
                    if ev.key == pygame.K_RETURN:
                        if buf.strip() and state["mode"] == "idle":
                            submit(buf.strip())
                        buf, typing = "", False
                    elif ev.key == pygame.K_ESCAPE:
                        buf, typing = "", False
                    elif ev.key == pygame.K_BACKSPACE:
                        buf = buf[:-1]
                    elif ev.unicode and ev.unicode.isprintable():
                        buf += ev.unicode
                elif ev.key == pygame.K_ESCAPE:
                    running = False
                elif game:
                    if btn:
                        game.button(btn)
                elif ev.key == pygame.K_RETURN:
                    typing = True
                elif btn == "up":
                    audio.change(config.VOLUME_STEP)
                    sfx.play("volume")
                elif btn == "down":
                    audio.change(-config.VOLUME_STEP)
                    sfx.play("volume")
                elif btn == "green":
                    game = games.create("menu", size)
                elif btn == "red":
                    music.stop()
                elif btn == "triangle":
                    ears.force_wake()                     # same as saying "hey BMO"

        if game:
            game.update(dt)

        overlay = now - audio.changed_at < config.VOLUME_OVERLAY_SECONDS
        clock_on = (config.IDLE_CLOCK and game is None and state["mode"] == "idle" and not typing
                    and (config.IDLE_CLOCK_WITH_MUSIC or not music.playing)
                    and now - state["active_at"] > config.IDLE_CLOCK_AFTER)
        if not clock_on:
            clock_ui.reset()

        if overlay:
            ui.volume_overlay(screen, size)
        elif game:
            game.draw(screen)
        elif clock_on:
            clock_ui.draw(screen)
        else:
            mode = state["mode"]
            if mode == "idle" and music.playing:
                mode = "dancing"
            anim.set(mode)
            anim.update(dt)
            screen.blit(anim.frame(), (0, 0))

        bottom = size[1]
        if typing:
            bar = pygame.Rect(0, size[1] - font.get_height() - 24, size[0], font.get_height() + 24)
            pygame.draw.rect(screen, (20, 50, 45), bar)
            screen.blit(font.render("> " + buf + "_", True, (230, 255, 245)), (16, bar.y + 12))
            bottom = bar.y
        sub = state["subtitle"]
        if (config.SUBTITLES and sub and not clock_on and not overlay
                and (state["sub_until"] == 0.0 or now < state["sub_until"])):
            subs.draw(screen, sub, bottom)
        pygame.display.flip()
    music.stop()
    pygame.quit()


if __name__ == "__main__":
    main()
