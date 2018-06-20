from backend.models.graph import Filler, Identifier, Network, Slot
from functools import reduce
from typing import List, Union


class Query(object):

    def __init__(self, network: Network):
        self.network = network

    def compare(self, other) -> bool:
        return False


class AndQuery(Query):

    def __init__(self, network: Network, queries: List[Query]):
        super().__init__(network)
        self.queries = queries

    def compare(self, other) -> bool:
        if len(self.queries) == 0:
            return False

        return reduce(lambda x, y: x and y, map(lambda query: query.compare(other), self.queries))


class OrQuery(Query):

    def __init__(self, network: Network, queries: List[Query]):
        super().__init__(network)
        self.queries = queries

    def compare(self, other) -> bool:
        if len(self.queries) == 0:
            return False

        return reduce(lambda x, y: x or y, map(lambda query: query.compare(other), self.queries))


class NotQuery(Query):

    def __init__(self, network: Network, query: Query):
        super().__init__(network)
        self.query = query

    def compare(self, other) -> bool:
        return not self.query.compare(other)


class SlotQuery(Query):

    def __init__(self, network: Network, name: str=None, queries: List[Union['FillerQuery', 'LiteralQuery', 'IdentifierQuery']]=None, intersects=True, contains=False, equals=False):
        super().__init__(network)
        self.name = name
        self.queries = queries
        self.intersects = intersects
        self.contains = contains
        self.equals = equals

    def compare(self, other: Slot) -> bool:
        if self.name is None and self.queries is None:
            return False

        if self.name is not None:
            if other._name != self.name:
                return False

        if self.queries is not None and len(self.queries) > 0:
            q = list(map(lambda query: query if isinstance(query, FillerQuery) else FillerQuery(self.network, query), self.queries))

            if not self.intersects and not self.contains and not self.equals:
                return False
            if self.equals:
                if not self._equals(other, q):
                    return False
            if self.contains:
                if not self._contains(other, q):
                    return False
            if self.intersects:
                if not self._intersects(other, q):
                    return False

        return True

    def _intersects(self, slot: Slot, q: List['FillerQuery']):
        for filler in slot:
            for query in q:
                if query.compare(filler):
                    return True
        return False

    def _contains(self, slot: Slot, q: List['FillerQuery']):
        for query in q:
            found = False
            for filler in slot:
                if query.compare(filler):
                    found = True
                    break
            if not found:
                return False
        return True

    def _equals(self, slot: Slot, q: List['FillerQuery']):
        if len(slot) != len(q):
            return False
        return self._contains(slot, q)

class FillerQuery(Query):

    def __init__(self, network: Network, query: Union['LiteralQuery', 'IdentifierQuery']):
        super().__init__(network)
        self.query = query

    def compare(self, other: Filler) -> bool:
        return self.query.compare(other._value)


class LiteralQuery(Query):

    def __init__(self, network: Network, value):
        super().__init__(network)
        self.value = value

    def compare(self, other) -> bool:
        return self.value == other


class IdentifierQuery(Query):

    def __init__(self, network: Network, identifier: Union[Identifier, str]=None, isa: Union[Identifier, str]=None, parent: Union[Identifier, str]=None):
        super().__init__(network)

        if isinstance(identifier, str):
            identifier = Identifier.parse(identifier)
        if isinstance(isa, str):
            isa = Identifier.parse(isa)
        if isinstance(parent, str):
            parent = Identifier.parse(parent)

        self.identifier = identifier
        self.isa = isa
        self.parent = parent

    def compare(self, other: Union[Identifier, str]) -> bool:
        if isinstance(other, str):
            other = Identifier.parse(other)

        if self.identifier is not None:
            if self.identifier == other:
                return True

        if self.isa is not None:
            if other.resolve(None, self.network) ^ self.isa.resolve(None, self.network):
                return True

        if self.parent is not None:
            if other.resolve(None, self.network)["IS-A"] == self.parent:
                return True

        return False
