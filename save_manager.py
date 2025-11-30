import json
import os
from tempfile import NamedTemporaryFile

class SaveManager:
    def __init__(self, save_dir=None):
        if save_dir is None:
            save_dir = os.path.join(os.path.expanduser('~'), '.incorrupta_saves')
        os.makedirs(save_dir, exist_ok=True)
        self.save_dir = save_dir
        self.current_version = "1.0"

    def _path(self, slot_name):
        return os.path.join(self.save_dir, f"{slot_name}.json")

    def save(self, slot_name, data):
        data_to_write = {"version": self.current_version, "data": data}
        tmp = NamedTemporaryFile("w", delete=False, dir=self.save_dir, encoding="utf-8")
        try:
            json.dump(data_to_write, tmp, ensure_ascii=False, indent=2)
            tmp.flush()
            tmp.close()
            final = self._path(slot_name)
            os.replace(tmp.name, final)
        finally:
            if os.path.exists(tmp.name):
                try:
                    os.unlink(tmp.name)
                except:
                    pass

    def load(self, slot_name):
        path = self._path(slot_name)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            saved = json.load(f)
        return saved.get("data")

    def list_saves(self):
        return [f[:-5] for f in os.listdir(self.save_dir) if f.endswith('.json')]
