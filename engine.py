import pyglet
import assets


class Engine:
    def __init__(self, width=1024, height=768, title="Incorrupta"):
        # Crear carpetas de assets si no existen
        assets.ensure_dirs()

        # Ventana principal (una sola ventana para todo el juego)
        self.window = pyglet.window.Window(
            width,
            height,
            caption=title,
            resizable=True
        )

        # Diccionario de escenas registradas
        self.scenes = {}
        # Escena actual
        self.current_scene = None
        # Manager de media (lo puedes usar desde fuera)
        self.media = None

        # Conectar eventos de la ventana a este objeto
        self.window.push_handlers(self)

    def register_scene(self, name, scene):
        """Registra una escena con un nombre."""
        self.scenes[name] = scene

    def go_to(self, name, **kwargs):
        """Cambia a otra escena."""
        if self.current_scene:
            try:
                self.current_scene.on_exit()
            except Exception:
                # si una escena no implementa on_exit, no pasa nada
                pass

        self.current_scene = self.scenes.get(name)
        if self.current_scene:
            self.current_scene.on_enter(**kwargs)

    # 🔴 AQUÍ EL CAMBIO IMPORTANTE: ya no tragamos excepciones 🔴
    def on_draw(self):
        """Evento de dibujo de pyglet."""
        self.window.clear()
        if self.current_scene:
            # Dejamos que la excepción salga para verla en consola
            self.current_scene.on_draw()

    def on_key_press(self, symbol, modifiers):
        """Evento de teclado de pyglet."""
        if self.current_scene:
            try:
                self.current_scene.on_key(symbol, modifiers)
            except Exception:
                pass

    # Bridge para algunos handlers de pyglet
    def on_key(self, symbol, modifiers):
        self.on_key_press(symbol, modifiers)

    def run(self):
        """Inicia el loop principal."""
        pyglet.clock.schedule_interval(self._update, 1 / 60.0)
        pyglet.app.run()

    def _update(self, dt):
        """Update por frame (llama on_update de la escena actual)."""
        if self.current_scene:
            try:
                self.current_scene.on_update(dt)
            except Exception:
                pass
