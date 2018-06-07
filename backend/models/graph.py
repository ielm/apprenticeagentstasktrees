from collections.abc import Mapping


class Network(object):

    def __init__(self):
        self._storage = dict()

    def register(self, namespace):
        if type(namespace) != str:
            raise TypeError()

        graph = Graph(namespace)
        self[namespace] = graph

        return graph

    def __setitem__(self, key, value):
        if type(value) != Graph:
            raise TypeError()

        if key != value._namespace:
            raise Network.NamespaceError(key, value._namespace)

        self._storage[key] = value

    def __getitem__(self, item):
        return self._storage[item]

    def __delitem__(self, key):
        del self._storage[key]

    def __iter__(self):
        return iter(self._storage)

    def __len__(self):
        return len(self._storage)

    class NamespaceError(Exception):

        def __init__(self, supplied, actual):
            self.supplied = supplied
            self.actual = actual

        def __str__(self):
            return "Supplied namespace '" + self.supplied + "' does not match actual namespace '" + self.actual + "'."


class Graph(Mapping):

    def __init__(self, namespace):
        self._namespace = namespace
        self._storage = dict()

    def __setitem__(self, key, value):
        if type(value) != Frame:
            raise TypeError("Graph elements must be Frame objects.")

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

        if not modified_key.startswith(self._namespace):
            modified_key = self._namespace + "." + modified_key

        return modified_key

    def search(self):
        raise Exception("NYI")

    def clear(self):
        self._storage = dict()


class Frame(object):

    def __init__(self):
        self._storage = dict()

    def __setitem__(self, key, value):
        if type(value) == Fillers:
            self._storage[key] = value
            return
        if type(value) != list:
            value = [value]

        self._storage[key] = Fillers(values=value)

    def __getitem__(self, item):
        if item in self._storage:
            return self._storage[item]
        return Fillers()

    def __delitem__(self, key):
        del self._storage[key]

    def __contains__(self, item):
        return item in self._storage

    def __len__(self):
        return len(self._storage)

    def __iter__(self):
        return iter(self._storage)

    def __str__(self):
        return str(self._storage)

    def __repr__(self):
        return str(self)


class Fillers(object):

    def __init__(self, values=None):
        self._storage = list()
        if values is not None and type(values) != list:
            values = [values]
        if values is not None:
            values = map(lambda value: value if type(value) == Filler else Filler(value), values)
            self._storage.extend(values)

    def __iadd__(self, other):
        if type(other) != Filler:
            other = Filler(other)

        self._storage.append(other)
        return self

    def __contains__(self, item):
        return item in self._storage

    def __len__(self):
        return len(self._storage)

    def __iter__(self):
        return iter(self._storage)

    def __eq__(self, other):
        if type(other) == Fillers:
            return self._storage == other._storage
        if type(other) == list:
            return self._storage == other

        return len(self._storage) == 1 and other in self._storage

    def __str__(self):
        return str(self._storage)

    def __repr__(self):
        return str(self)


class Filler(object):

    def __init__(self, value):
        self._value = value
        self._metadata = None

    def compare(self, other, isa=True):
        if type(other) != Filler:
            raise Exception("Filler.compare requires Filler as parameter[1].")

        # TODO: if either self.value or other.value are not a Frame (or Frame pointer): compare directly
        # TODO: else, resolve as Frames, compare directly, then recursive IS-A from each, looking for the other



    def __eq__(self, other):
        if type(other) == Filler:
            return self._value == other._value
        return self._value == other

    def __str__(self):
        return str(self._value)

    def __repr__(self):
        return str(self)