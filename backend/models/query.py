from backend.models.graph import Filler, Frame, Identifier, Network, Slot
from functools import reduce
from typing import Any, List, Union


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


class ExactQuery(Query):

    def __init__(self, network: Network, queries: List[Query]):
        super().__init__(network)
        self.queries = queries

    def compare(self, other: List[Any]) -> bool:
        if isinstance(other, str):
            return False

        try:
            iter(other)
        except TypeError:
            return False

        if isinstance(other, Frame):
            other = other._storage.values()

        return self._equals(other, self.queries)

    def _contains(self, other: List[Any], q: List[Query]):
        for query in q:
            found = False
            for value in other:
                if query.compare(value):
                    found = True
                    break
            if not found:
                return False
        return True

    def _equals(self, other: List[Any], q: List[Query]):
        if len(other) != len(q):
            return False
        return self._contains(other, q)


class NotQuery(Query):

    def __init__(self, network: Network, query: Query):
        super().__init__(network)
        self.query = query

    def compare(self, other) -> bool:
        return not self.query.compare(other)


class FrameQuery(Query):

    def __init__(self, network: Network, subquery: Union[AndQuery, OrQuery, NotQuery, ExactQuery, 'IdentifierQuery', 'SlotQuery']):
        super().__init__(network)
        self.subquery = subquery

    def compare(self, other: Frame) -> bool:
        return self.subquery.compare(other)


class SlotQuery(Query):

    def __init__(self, network: Network, subquery: Union[AndQuery, OrQuery, ExactQuery, NotQuery, 'NameQuery', 'FillerQuery']):
        super().__init__(network)
        self.subquery = subquery

    def compare(self, other: Union[Frame, Slot]) -> bool:
        if isinstance(other, Frame):
            for slot in other._storage.values():
                if self.subquery.compare(slot):
                    return True
            return False

        return self.subquery.compare(other)

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


class NameQuery(Query):

    def __init__(self, network: Network, name: str):
        super().__init__(network)
        self.name = name

    def compare(self, other: Slot) -> bool:
        return other._name == self.name


class FillerQuery(Query):

    def __init__(self, network: Network, query: Union['LiteralQuery', 'IdentifierQuery']):
        super().__init__(network)
        self.query = query

    def compare(self, other: Union[Slot, Filler]) -> bool:
        if isinstance(other, Slot):
            for filler in other:
                if self.query.compare(filler):
                    return True
            return False

        return self.query.compare(other._value)


class LiteralQuery(Query):

    def __init__(self, network: Network, value):
        super().__init__(network)
        self.value = value

    def compare(self, other) -> bool:
        return self.value == other


class IdentifierQuery(Query):

    def __init__(self, network: Network, identifier: Union[Identifier, Frame, str]=None, isa: Union[Identifier, Frame, str]=None, parent: Union[Identifier, Frame, str]=None):
        super().__init__(network)

        if isinstance(identifier, Frame):
            identifier = identifier._identifier
        if isinstance(identifier, str):
            identifier = Identifier.parse(identifier)

        if isinstance(isa, Frame):
            isa = isa._identifier
        if isinstance(isa, str):
            isa = Identifier.parse(isa)

        if isinstance(parent, Frame):
            parent = parent._identifier
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
