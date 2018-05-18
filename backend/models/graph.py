from collections.abc import Mapping


class Graph(Mapping):

    def __init__(self):
        self._storage = dict()

    def __setitem__(self, key, value):
        key = self._modify_key(key)
        self._storage[key] = value

    def __getitem__(self, key):
        key = self._modify_key(key)
        return self._storage[key]

    def __delitem__(self, key):
        key = self._modify_key(key)
        del self._storage[key]

    def __iter__(self):
        return iter(self._storage)

    def __len__(self):
        return len(self._storage)

    def _modify_key(self, key):
        modified_key = key if not key.startswith("ASSEMBLE") else key.replace("ASSEMBLE", "BUILD") + "X"
        return modified_key

    def search(self):
        raise Exception("NYI")