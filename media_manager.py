import pyglet
import os

class MediaManager:
    def __init__(self):
        self.player = pyglet.media.Player()
        self.current_source = None

    def play_sound(self, path, volume=1.0):
        if not os.path.exists(path):
            return
        src = pyglet.media.load(path, streaming=False)
        player = pyglet.media.Player()
        player.volume = volume
        player.queue(src)
        player.play()
        return player

    def play_music(self, path, loop=True, volume=0.6):
        if not os.path.exists(path):
            return None
        self.player.next_source()
        src = pyglet.media.load(path)
        self.player.queue(src)
        self.player.loop = loop
        self.player.volume = volume
        self.player.play()
        return self.player

    def stop_music(self):
        try:
            self.player.pause()
            self.player.delete()
        except Exception:
            pass

    def play_video(self, path):
        if not os.path.exists(path):
            return None
        src = pyglet.media.load(path)
        player = pyglet.media.Player()
        player.queue(src)
        player.play()
        return player
