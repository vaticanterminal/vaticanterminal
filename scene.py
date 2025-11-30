class Scene:
    """Base para escenas (menú, intro, casos, etc.)."""
    def __init__(self, engine):
        self.engine = engine

    def on_enter(self, **kwargs):
        pass

    def on_exit(self):
        pass

    def on_update(self, dt):
        pass

    def on_draw(self):
        pass

    def on_key(self, symbol, modifiers):
        pass
