import os
from engine import Engine
from save_manager import SaveManager
from inventory import Inventory
from vatican_terminal import VaticanTerminal
from vatican_firmware import VaticanFirmware
from vatican_warning import VaticanWarning
from arde import Arde         
from vatican_shell import VaticanShell
from case_lancaster import CaseLancasterScene
import assets


def integrate_existing(file_path):
    if os.path.exists(file_path):
        print('Found original file at', file_path)
    else:
        print('Original file missing:', file_path)


def main():
    engine = Engine(1024, 720, title='Incorrupta - Refactor base')
    save_manager = SaveManager()
    inventory = Inventory()

    # Registrar escenas
    engine.register_scene('vatican_firmware', VaticanFirmware(engine))
    engine.register_scene('vatican_shell', VaticanShell(engine))
    engine.register_scene('vatican_terminal', VaticanTerminal(engine))
    engine.register_scene('vatican_warning', VaticanWarning(engine))
    engine.register_scene('case_lancaster', CaseLancasterScene(engine, save_manager, inventory))
    engine.register_scene('arde', Arde(engine))  

    # si quieres enlazar con tu script viejo, ajusta esta ruta
    integrate_existing('Incorrupta2025.py')

    # Flujo de arranque: Firmware -> Shell -> Daemonum Index / menú -> casos
    engine.go_to('vatican_firmware')
    engine.run()


if __name__ == '__main__':
    main()
