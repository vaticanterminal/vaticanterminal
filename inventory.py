class Inventory:
    def __init__(self, items=None):
        self.items = list(items) if items else []

    def add(self, item):
        if item not in self.items:
            self.items.append(item)

    def remove(self, item):
        if item in self.items:
            self.items.remove(item)

    def has(self, item):
        return item in self.items

    def to_dict(self):
        return {'items': list(self.items)}

    @classmethod
    def from_dict(cls, d):
        return cls(items=d.get('items', []))
