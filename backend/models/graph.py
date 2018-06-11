from collections.abc import Mapping
from functools import reduce


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

    def register(self, id, isa=None):
        if type(id) != str:
            raise TypeError()

        frame = Frame(id, isa=isa)
        self[id] = frame

        return frame

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
        if type(parent) == Frame:
            parent = parent.name()

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

    def compare(self, other, isa=True, intersection=True):
        # 1) Refactor "other" into a list of Fillers (either using the input Filler information, or defaulting to self)
        if type(other) == Fillers:
            other = other._storage
        if type(other) != list:
            other = [other]
        other = list(map(lambda o: o if type(o) == Filler else Filler(o), other))
        for o in other:
            if o._frame is None:
                o._frame = self._frame

        # 2) Compare each filler in self to the input fillers
        results = list(map(lambda f: f.compare(other, isa=isa, intersection=intersection), self._storage))

        if len(results) == 0 and len(self._storage) == 0 and len(other) == 0:
            return True

        if intersection:
            results = reduce(lambda x, y: x or y, results)
        else:
            results = reduce(lambda x, y: x and y, results)

        return results

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

    # The XOR operator is overridden here to provide a convenient single character comparator ("^") for the most
    # common comparison case: isa=True and intersection=True.  This is passed through to the Filler.compare method,
    # see that for details on the expected behavior.
    def __xor__(self, other):
        return self.compare(other, isa=True, intersection=True)

    def __eq__(self, other):
        return self.compare(other, isa=False, intersection=True)

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

    def compare(self, other, isa=True, intersection=True):
        # 1) Refactor "other" into a list of Fillers (either using the input Filler information, or defaulting to self)
        if type(other) != Filler:
            other = Filler(other)
            other._frame = self._frame
        value = other._value
        if type(value) != list:
            value = [value]
        others = list(map(lambda v: v if type(v) == Filler else Filler(v), value))
        for o in others:
            if o._frame is None:
                o._frame = other._frame

        # 2) For each value, do a comprehensive comparison, mapping the results
        def _compare(to):
            sr = self.resolve()
            tr = to.resolve()

            sv = sr
            tv = tr

            if type(sr) == Frame:
                sv = sr.name()

            if type(tr) == Frame:
                tv = tr.name()

            if sv == tv:
                return True

            if type(sr) == Frame and type(tr) == Frame and isa:
                if sr.isa(tr):
                    return True
                if tr.isa(sr):
                    return True

            return False

        # 3) Convert the results into a single comparator (if intersection is requested, then any single True is
        #    sufficient, otherwise all must be true).
        results = list(map(lambda value: _compare(value), others))
        if intersection:
            results = reduce(lambda x, y: x or y, results)
        else:
            results = reduce(lambda x, y: x and y, results)

        return results

    def __eq__(self, other):
        return self.compare(other, isa=False, intersection=True)

    # The XOR operator is overridden here to provide a convenient single character comparator ("^") for the most
    # common comparison case: isa=True and intersection=True.  This allows for all of the following statements
    # to return True (with generally accepted setup for frames in a graph, and graphs in a network):
    # OBJECT-1 ^ OBJECT-1
    # OBJECT-1 ^ OBJECT
    # OBJECT-1 ^ [OBJECT, EVENT]
    # OBJECT-1 ^ [OBJECT-1, OBJECT-2]
    # The XOR operator does not make traditional sense on a Filler, hence the selection of this operator to
    # override for different behavior.
    def __xor__(self, other):
        return self.compare(other, isa=True, intersection=True)

    def __str__(self):
        return str(self._value)

    def __repr__(self):
        return str(self)