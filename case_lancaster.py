from scene import Scene
from pyglet.text import Label
import os
from media_manager import MediaManager
from effects import async_warning_flash, glitch_text_once
import pyglet


class CaseLancasterScene(Scene):
    def __init__(self, engine, save_manager, inventory):
        super().__init__(engine)
        self.save_manager = save_manager
        self.inventory = inventory
        self.media = MediaManager()
        self.overlay_opacity = 0.0
        self.corruption_level = 0.0
        self.font_name = 'Courier New'
        self.from_palette = 'green'

    def on_enter(self, from_terminal_palette=None, **kwargs):
        # De qué paleta venimos (verde, ámbar, etc.)
        self.from_palette = from_terminal_palette or 'green'

        # Música ambiental del caso (si existe)
        audio_path = os.path.join(os.path.dirname(__file__), 'assets', 'audio', 'case_ambient.ogg')
        if os.path.exists(audio_path):
            self.media.play_music(audio_path, loop=True, volume=0.28)

        # Nivel de corrupción inicial (podemos usarlo luego)
        self.corruption_level = 0.1

    def on_update(self, dt):
        # Aquí luego puedes subir la corrupción, manejar timers, etc.
        pass

    def on_draw(self):
        from pyglet import gl

        # Dimensiones de la ventana
        w = self.engine.window.width
        h = self.engine.window.height

        # Color de fondo según paleta de origen (para que se sienta como "reboot")
        if self.from_palette == 'green':
            gl.glClearColor(0.01, 0.02, 0.02, 1)
        elif self.from_palette == 'amber':
            gl.glClearColor(0.04, 0.02, 0.01, 1)
        elif self.from_palette == 'white':
            gl.glClearColor(0.02, 0.02, 0.02, 1)
        elif self.from_palette == 'purple':
            gl.glClearColor(0.02, 0.01, 0.03, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        # Texto descriptivo de la escena (luego aquí metemos tu narrativa real)
        label = Label(
            'Lancaster Hill - Exterior del internado\n'
            'El auto está estacionado al pie de la colina.\n'
            '(Pulsa S para un glitch rojo de presencia, I para ver inventario, '
            'ESC para volver al archivo Vaticano)',
            x=30,
            y=h - 80,
            width=w - 60,      # importante para multiline en pyglet 2.x
            multiline=True,
            font_name=self.font_name,
            font_size=16,
            color=(220, 220, 220, 255)
        )
        label.draw()

        # Overlay rojo (glitch de presencia) si está activo
        if self.overlay_opacity > 0:
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
            gl.glColor4f(1.0, 0.0, 0.0, self.overlay_opacity)
            pyglet.graphics.draw(
                4, pyglet.gl.GL_QUADS,
                ('v2f', [
                    0, 0,
                    w, 0,
                    w, h,
                    0, h
                ])
            )
            gl.glDisable(gl.GL_BLEND)

    def on_key(self, symbol, modifiers):
        from pyglet.window import key

        if symbol == key.S:
            # Glitch rojo de presencia demoníaca
            def draw_cb(opacity, overlay_color):
                self.overlay_opacity = opacity

            async_warning_flash(draw_cb, flashes=8, base_delay=0.04)
            print(glitch_text_once('Sientes una presencia... la incorrupta está cerca.', intensity=0.35))

        elif symbol == key.I:
            # Ver inventario en consola (por ahora)
            print('Inventory:', self.inventory.items)

        elif symbol == key.ESCAPE:
            # Volver a la terminal del Vaticano
            self.engine.go_to('vatican_terminal')
