from collections.abc import Mapping
from functools import reduce
from typing import Any, List, Type, TypeVar, Union
from uuid import uuid4

import re

# Use the below block of code to avoid cyclic imports,
# while still allowing top-level imports for type hints.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.models.query import FrameQuery, SimpleFrameQuery


class Identifier(object):

    @classmethod
    def parse(cls, path: str) -> 'Identifier':
        graph = None
        name = None
        instance = None

        parts = re.split(r'\.([0-9]+)$', path, maxsplit=1)
        if len(parts) > 1:
            instance = int(parts[1])
            path = parts[0]

        parts = re.split(r'^(.+?)\.', path, maxsplit=1)
        if len(parts) > 2:
            graph = parts[1]
            path = parts[2]

        name = path

        return Identifier(graph, name, instance=instance)

    def __init__(self, graph: str, name: str, instance: int=None):
        self.graph = graph
        self.name = name
        self.instance = instance

    def resolve(self, graph: Union['Graph', str], network: Union['Network']=None) -> 'Frame':
        if graph is not None and isinstance(graph, Graph):
            if self in graph:
                return graph[self]

        if network is not None:
            return network.lookup(self, graph=graph)

        raise UnknownFrameError()

    def render(self, graph: bool=True, name: bool=True, instance: bool=True) -> str:
        values = []
        if graph: values.append(self.graph)
        if name: values.append(self.name)
        if instance: values.append(self.instance)

        return ".".join(map(lambda x: str(x), filter(lambda x: x is not None, values)))

    def __eq__(self, other):
        if isinstance(other, str):
            other = Identifier.parse(other)

        if isinstance(other, Identifier):
            if self.graph == other.graph or self.graph is None or other.graph is None:
                if self.name == other.name and self.instance == other.instance:
                    return True
        if isinstance(other, Frame):
            return self == other._identifier

        return False

    def __str__(self):
        return self.render()

    def __repr__(self):
        return "@" + str(self)

    def deep_copy(self):
        return Identifier(self.graph, self.name, instance=self.instance)


class Literal(object):

    def __init__(self, value):
        if isinstance(value, Literal):
            value = value.value
        self.value = value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if isinstance(other, Literal):
            other = other.value
        return self.value == other

    def deep_copy(self):
        return Literal(self.value)


class Network(object):

    G = TypeVar('G', bound='Graph')

    def __init__(self):
        self._storage = dict()

    def register(self, graph: Union[G, str]) -> G:
        if isinstance(graph, Graph):
            self[graph._namespace] = graph
        elif isinstance(graph, str):
            graph = Graph(graph)
            self[graph._namespace] = graph
        else:
            raise TypeError()

        return self[graph._namespace]

    def lookup(self, identifier: Union[Identifier, str], graph: Union['Graph', str]=None) -> 'Frame':
        if graph is not None and isinstance(graph, Graph):
            graph = graph._namespace

        try:
            return self[graph][identifier]
        except KeyError:
            pass

        if isinstance(identifier, str):
            identifier = Identifier.parse(identifier)

        if identifier.graph is None or identifier.graph not in self:
            raise Exception("Unknown graph for " + repr(identifier) + ".")

        return self[identifier.graph][identifier]

    def search(self, query: 'FrameQuery', exclude_knowledge=True) -> List['Frame']:
        graphs = self._storage.values()
        if exclude_knowledge:
            from backend.models.ontology import Ontology
            graphs = list(filter(lambda graph: not isinstance(graph, Ontology), graphs))

        results = list(map(lambda graph: graph.search(query), graphs))
        return list(reduce(lambda x, y: x + y, results))

    def __setitem__(self, key, value):
        if not isinstance(value, Graph):
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

        def __repr__(self):
            return str(self)


class Graph(Mapping):

    def __init__(self, namespace: str):
        self._namespace = namespace
        self._storage = dict()
        self._network = None
        self._indexes = dict()

    def __setitem__(self, key: Union[Identifier, str], value: 'Frame'):
        if not isinstance(value, Frame):
            raise TypeError("Graph elements must be Frame objects.")
        if key != value._identifier:
            raise Network.NamespaceError(key, value._identifier)

        if isinstance(key, Identifier):
            key = key.render()

        key = self._modify_key(key)
        self._storage[key] = value
        value._network = self._network
        value._graph = self
        value._identifier.graph = self._namespace

    def __getitem__(self, key: Union[Identifier, str]):
        if isinstance(key, Identifier):
            key = key.render()

        key = self._modify_key(key)
        return self._storage[key]

    def __delitem__(self, key):
        key = self._modify_key(key)
        del self._storage[key]

    def __iter__(self):
        return iter(self._storage)

    def __len__(self):
        return len(self._storage)

    def _modify_key(self, key: Union[Identifier, str]) -> str:
        modified_key = key

        if not modified_key.startswith(self._namespace):
            modified_key = self._namespace + "." + modified_key

        return modified_key

    def _frame_type(self) -> Type['Frame']:
        return Frame

    def _next_index(self, concept):
        if concept in self._indexes:
            index = self._indexes[concept] + 1
            self._indexes[concept] = index
            return index

        self._indexes[concept] = 1
        return 1

    def register(self, id: str, isa: Union['Slot', 'Filler', List['Filler'], Identifier, List['Identifier'], str, List[str]]=None, generate_index: bool=False) -> 'Frame':
        if type(id) != str:
            raise TypeError()

        if generate_index:
            id = id + "." + str(self._next_index(id))

        frame = self._frame_type()(id, isa=isa)
        self[id] = frame

        return frame

    def search(self, query: 'FrameQuery') -> List['Frame']:
        return list(filter(lambda frame: query.compare(frame), self._storage.values()))

    def clear(self):
        self._storage = dict()


class Frame(object):

    def __init__(self, identifier: Union[Identifier, str], isa: Union['Slot', 'Filler', List['Filler'], Identifier, List['Identifier'], str, List[str]]=None):
        if isinstance(identifier, Identifier):
            self._identifier = identifier
        else:
            self._identifier = Identifier.parse(identifier)

        self._storage = dict()

        self._network = None
        self._graph = None

        self._uuid = uuid4()

        if isa is not None:
            self[self._ISA_type()] = isa

    def _ISA_type(self):
        return "IS-A"

    def name(self) -> str:
        return str(self._identifier)

    def isa(self, parent: Union['Frame', Identifier, str]) -> bool:
        if isinstance(parent, Frame):
            parent = parent.name()
        if isinstance(parent, Identifier):
            parent = parent.render()

        try:
            if parent in self.ancestors():
                return True
        except UnknownFrameError: pass

        if parent == self.name():
            return True

        if self._graph is not None:

            try:
                if self._graph._namespace + "." + parent in self.ancestors():
                    return True
            except UnknownFrameError: pass

            if self._graph._namespace + "." + parent == self.name():
                return True

        return False

    # TODO: return list of Identifiers
    def ancestors(self) -> [str]:
        result = []
        for parent in self[self._ISA_type()]:
            parent = parent.resolve()

            if parent is None:
                continue

            if isinstance(parent, Frame):
                result.append(parent.name())
                result.extend(parent.ancestors())
            elif isinstance(parent, str):
                result.append(parent)
        return result

    def parents(self) -> List[Identifier]:
        return list(map(lambda isa: isa._value, self[self._ISA_type()]))

    def concept(self, full_path: bool=True) -> str:
        identifiers = list(map(lambda filler: filler._value, filter(lambda filler: isinstance(filler._value, Identifier), self[self._ISA_type()])))
        identifiers = list(map(lambda identifier: identifier if identifier.graph is not None else Identifier(self._graph._namespace, identifier.name, instance=identifier.instance), identifiers))

        concepts = list(map(lambda identifier: identifier.render(graph=full_path, instance=False), identifiers))

        return "&".join(concepts)

    def __setitem__(self, key, value):
        if type(value) == Slot:
            self._storage[key] = value
            value._frame = self
            return
        if type(value) != list:
            value = [value]

        self._storage[key] = Slot(key, values=value, frame=self)

    def __getitem__(self, item):
        if item in self._storage:
            return self._storage[item]
        return Slot(item, frame=self)

    def __delitem__(self, key):
        del self._storage[key]

    def __contains__(self, item):
        return item in self._storage

    def __len__(self):
        return len(self._storage)

    def __iter__(self):
        return iter(self._storage)

    # The XOR operator is overridden here to provide a convenient single character comparator ("^") for the most
    # common comparison case: "isa".  Effectively, "HUMAN" ^ "OBJECT" == True.
    def __xor__(self, other):
        return self.isa(other)

    def __str__(self):
        return str(self._identifier) + " = " +str(self._storage)

    def __repr__(self):
        return str(self)

    def deep_copy(self, graph: Graph):
        copy = self.__class__(self._identifier.deep_copy())
        copy._network = self._network
        copy._graph = graph
        copy._uuid = uuid4()

        copy._storage = dict()
        for slot in self._storage.values():
            copy._storage[slot._name] = slot.deep_copy(copy)

        return copy

    @classmethod
    def q(cls, n: Network, comparator: str="and") -> 'SimpleFrameQuery':
        from backend.models.query import SimpleFrameQuery
        return SimpleFrameQuery(n, comparator=comparator)


class Slot(object):

    def __init__(self, name: str, values=None, frame: Frame=None):
        self._name = name
        self._storage = list()
        self._frame = frame

        if values is not None and type(values) != list:
            values = [values]
        if values is not None:
            values = list(map(lambda value: value if isinstance(value, Filler) else Filler(value), values))
            for value in values: value._frame = self._frame

            self._storage.extend(values)

    def compare(self, other, isa: bool=True, intersection: bool=True) -> bool:
        if isinstance(other, Slot):
            other = other._storage

        if not isinstance(other, list):
            other = [other]

        # Compare each filler in self to the input fillers
        results = list(map(lambda f: f.compare(other, isa=isa, intersection=intersection), self._storage))

        if len(results) == 0 and len(self._storage) == 0 and len(other) == 0:
            return True
        if len(results) == 0 and len(self._storage) == 0:
            return False

        if intersection:
            results = reduce(lambda x, y: x or y, results)
        else:
            results = reduce(lambda x, y: x and y, results)

        return results

    def __add__(self, other):
        if not isinstance(other, Slot):
            return self + other

        result = Slot(self._name, values=self._storage, frame=self._frame)
        result._storage.extend(other._storage)
        return result

    def __iadd__(self, other):
        if not isinstance(other, Filler):
            other = Filler(other)
        if other in self._storage:
            return self

        other._frame = self._frame

        self._storage.append(other)
        return self

    def __isub__(self, other):
        if not isinstance(other, Filler):
            other = Filler(other)

        self._storage = list(filter(lambda filler: filler != other, self._storage))

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
        return self._name + "=" + str(self._storage)

    def __repr__(self):
        return str(self)

    def deep_copy(self, frame: Frame):
        copy = Slot(self._name, frame=frame)
        copy._storage = list()
        for filler in self:
            copy._storage.append(filler.deep_copy(frame))

        return copy


class Filler(object):

    def __init__(self, value: Union[Identifier, Literal, Any], metadata: dict=None):
        if isinstance(value, Identifier) or isinstance(value, Literal):
            self._value = value
        elif isinstance(value, str):
            self._value = Identifier.parse(value)
        elif isinstance(value, Frame):
            self._value = value._identifier
        else:
            self._value = Literal(value)

        self._metadata = None
        self._frame = None

        self._uuid = uuid4()

        if metadata is not None:
            self._metadata = metadata

    def resolve(self) -> Union[Frame, Any]:
        if isinstance(self._value, Frame):
            return self._value
        if isinstance(self._value, Identifier):
            graph = None
            network = None

            if self._frame is not None:
                graph = self._frame._graph
                if graph is not None:
                    network = graph._network

            return self._value.resolve(graph, network=network)
        # TODO: Can this even be the case now?
        if isinstance(self._value, str):
            if self._frame is not None:
                if self._frame._graph is not None:
                    try:
                        return self._frame._graph[self._value]
                    except KeyError: pass
                    if self._frame._graph._network is not None:
                        try:
                            return self._frame._graph._network.lookup(self._value, graph=self._frame._graph._namespace)
                        except KeyError: pass
                        except Exception: pass
        return self._value

    def compare(self, other, isa: bool=True, intersection: bool=True) -> bool:
        if not isinstance(other, list):
            other = [other]

        other = list(map(lambda f: f._value if isinstance(f, Filler) else f, other))

        def _compare(to):

            local = self._value

            if local == to:
                return True

            if isinstance(to, str):
                if local == Identifier.parse(to):
                    return True

            if isinstance(local, Identifier) and isa:
                try:
                    if self.resolve().isa(to):
                        return True
                except UnknownFrameError: pass

            if isinstance(to, Identifier) and isa:
                try:
                    if to.resolve(self._graph(), self._network()).isa(local):
                        return True
                except UnknownFrameError: pass

            if isinstance(to, Frame) and isa:
                try:
                    if to.isa(local):
                        return True
                except UnknownFrameError: pass

            return False

        # Convert the results into a single comparator (if intersection is requested, then any single True is
        # sufficient, otherwise all must be true).
        results = list(map(lambda value: _compare(value), other))
        if intersection:
            results = reduce(lambda x, y: x or y, results)
        else:
            results = reduce(lambda x, y: x and y, results)

        return results

    def _graph(self) -> Graph:
        if self._frame is not None:
            return self._frame._graph

    def _network(self) -> Network:
        graph = self._graph()
        if graph is not None:
            return graph._network

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

    def deep_copy(self, frame: Frame):
        copy = Filler(self._value.deep_copy(), metadata=self._metadata)
        copy._frame = frame
        copy._uuid = uuid4()

        return copy


class UnknownFrameError(Exception): pass


class FrameParseError(Exception): pass
