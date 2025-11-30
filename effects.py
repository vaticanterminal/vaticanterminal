import random
import time
from threading import Thread

def glitch_text_once(s, intensity=0.12):
    chars = list(s)
    for i, c in enumerate(chars):
        if c != ' ' and random.random() < intensity:
            chars[i] = random.choice('█▓▒░#@$%&?*')
    return ''.join(chars)

def async_warning_flash(callback_draw, flashes=6, base_delay=0.06):
    """
    callback_draw(opacity, overlay_color) se llamará en un hilo aparte.
    Tú usas opacity en la escena para dibujar un overlay rojo.
    """
    def _run():
        for i in range(flashes):
            op = 0.6 * (1 - i / (flashes + 1))
            callback_draw(opacity=op, overlay_color=(1.0, 0.0, 0.0))
            time.sleep(base_delay)
        callback_draw(opacity=0.0, overlay_color=(0, 0, 0))
    t = Thread(target=_run, daemon=True)
    t.start()
