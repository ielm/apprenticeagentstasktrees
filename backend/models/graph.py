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

    def lookup(self, name, graph=None):
        try:
            return self[graph][name]
        except KeyError:
            pass

        parts = name.split(".", maxsplit=1)
        if len(parts) < 2:
            raise Exception("Unknown graph for '" + name + "'.")
        graph = parts[0]

        return self[graph][name]

    def __setitem__(self, key, value):
        if type(value) != Graph:
            raise TypeError()

        if key != value._namespace:
            raise Network.NamespaceError(key, value._namespace)

        self._storage[key] = value
        value._network = self

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
        self._network = None

    def __setitem__(self, key, value):
        if type(value) != Frame:
            raise TypeError("Graph elements must be Frame objects.")
        if key != value._name:
            raise Network.NamespaceError(key, value._name)

        key = self._modify_key(key)
        self._storage[key] = value
        value._network = self._network
        value._graph = self

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

    def __init__(self, name, isa=None):
        self._name = name
        self._storage = dict()

        self._network = None
        self._graph = None

        if isa is not None:
            self["IS-A"] = isa

    def name(self):
        name = self._name
        if self._graph is not None:
            name = self._graph._namespace + "." + name
        return name

    def isa(self, parent):
        if parent in self.ancestors():
            return True
        if parent == self.name():
            return True
        if self._graph is not None:
            if self._graph._namespace + "." + parent in self.ancestors():
                return True
            if self._graph._namespace + "." + parent == self.name():
                return True

        return False

    def ancestors(self):
        result = []
        for parent in self["IS-A"]:
            parent = parent.resolve()

            if parent is None:
                continue

            result.append(parent.name())
            result.extend(parent.ancestors())
        return result

    def __setitem__(self, key, value):
        if type(value) == Fillers:
            self._storage[key] = value
            value._frame = self
            return
        if type(value) != list:
            value = [value]

        self._storage[key] = Fillers(values=value, frame=self)

    def __getitem__(self, item):
        if item in self._storage:
            return self._storage[item]
        return Fillers(frame=self)

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

    def __init__(self, values=None, frame=None):
        self._storage = list()
        self._frame = frame

        if values is not None and type(values) != list:
            values = [values]
        if values is not None:
            values = list(map(lambda value: value if type(value) == Filler else Filler(value), values))
            for value in values: value._frame = self._frame

            self._storage.extend(values)

    def __iadd__(self, other):
        if type(other) != Filler:
            other = Filler(other)
        other._frame = self._frame

        self._storage.append(other)
        return self

    def __contains__(self, item):
        return item in self._storage

    def __len__(self):
        return len(self._storage)

    def __iter__(self):
        return iter(self._storage)

    def __getitem__(self, item):
        return self._storage[item]

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
        self._frame = None

    def resolve(self):
        if type(self._value) == Frame:
            return self._value
        if type(self._value) == str:
            if self._frame is not None:
                if self._frame._graph is not None:
                    try:
                        return self._frame._graph[self._value]
                    except KeyError: pass
                    if self._frame._graph._network is not None:
                        try:
                            return self._frame._graph._network.lookup(self._value, graph=self._frame._graph._namespace)
                        except KeyError: pass
        return self._value

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