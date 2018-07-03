from backend.models.grammar import Grammar
from backend.models.graph import Filler, Frame, Identifier, Network, Slot
from enum import Enum
from functools import reduce
from typing import Any, List, Union


class Query(object):

    def __init__(self, network: Network):
        self.network = network

    def compare(self, other) -> bool:
        return False

    @classmethod
    def parse(cls, network: Network, input: str) -> 'Query':
        result = Grammar.parse(network, input, start="frame_query")

        if not isinstance(result, Query):
            raise Exception("Parsed value for \"" + input + "\" is not a Query.")

        return result

    @classmethod
    def parsef(cls, network: Network, input: str, **kwargs):
        return Query.parse(network, input.format(**kwargs))


class AndQuery(Query):

    def __init__(self, network: Network, queries: List[Query]):
        super().__init__(network)
        self.queries = queries

    def compare(self, other) -> bool:
        if len(self.queries) == 0:
            return False

        return reduce(lambda x, y: x and y, map(lambda query: query.compare(other), self.queries))

    def __eq__(self, other):
        if not isinstance(other, AndQuery):
            return super().__eq__(other)
        return self.network == other.network and self.queries == other.queries


class OrQuery(Query):

    def __init__(self, network: Network, queries: List[Query]):
        super().__init__(network)
        self.queries = queries

    def compare(self, other) -> bool:
        if len(self.queries) == 0:
            return False

        return reduce(lambda x, y: x or y, map(lambda query: query.compare(other), self.queries))

    def __eq__(self, other):
        if not isinstance(other, OrQuery):
            return super().__eq__(other)
        return self.network == other.network and self.queries == other.queries


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

    def __eq__(self, other):
        if not isinstance(other, ExactQuery):
            return super().__eq__(other)
        return self.network == other.network and self.queries == other.queries


class NotQuery(Query):

    def __init__(self, network: Network, query: Query):
        super().__init__(network)
        self.query = query

    def compare(self, other) -> bool:
        return not self.query.compare(other)

    def __eq__(self, other):
        if not isinstance(other, NotQuery):
            return super().__eq__(other)
        return self.network == other.network and self.query == other.query


class FrameQuery(Query):

    def __init__(self, network: Network, subquery: Union[AndQuery, OrQuery, NotQuery, ExactQuery, 'IdentifierQuery', 'SlotQuery']):
        super().__init__(network)
        self.subquery = subquery

    def compare(self, other: Frame) -> bool:
        return self.subquery.compare(other)

    def __eq__(self, other):
        if not isinstance(other, FrameQuery):
            return super().__eq__(other)
        return self.network == other.network and self.subquery == other.subquery


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

    def __eq__(self, other):
        if not isinstance(other, SlotQuery):
            return super().__eq__(other)
        return self.network == other.network and self.subquery == other.subquery


class NameQuery(Query):

    def __init__(self, network: Network, name: str):
        super().__init__(network)
        self.name = name

    def compare(self, other: Slot) -> bool:
        return other._name == self.name

    def __eq__(self, other):
        if not isinstance(other, NameQuery):
            return super().__eq__(other)
        return self.network == other.network and self.name == other.name


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

    def __eq__(self, other):
        if not isinstance(other, FillerQuery):
            return super().__eq__(other)
        return self.network == other.network and self.query == other.query


class LiteralQuery(Query):

    def __init__(self, network: Network, value):
        super().__init__(network)
        self.value = value

    def compare(self, other) -> bool:
        return self.value == other

    def __eq__(self, other):
        if not isinstance(other, LiteralQuery):
            return super().__eq__(other)
        return self.network == other.network and self.value == other.value


class IdentifierQuery(Query):

    class Comparator(Enum):
        EQUALS = 1      # Is self.identifier exactly the same as the input
        ISA = 2         # Is self.identifier an ancestor of the input
        ISPARENT = 3    # Is self.identifier the immediate parent of the input

    def __init__(self, network: Network, identifier: Union[Identifier, Frame, str], comparator: Comparator):
        super().__init__(network)

        if isinstance(identifier, Frame):
            identifier = identifier._identifier
        if isinstance(identifier, str):
            identifier = Identifier.parse(identifier)

        self.identifier = identifier
        self.comparator = comparator

    def compare(self, other: Union[Frame, Identifier, Filler, str]) -> bool:
        if isinstance(other, Filler):
            other = other._value

        if isinstance(other, str):
            other = Identifier.parse(other)

        if isinstance(other, Frame):
            other = other._identifier

        if self.comparator == self.Comparator.EQUALS:
            return self.identifier == other

        if self.comparator == self.Comparator.ISA:
            return other.resolve(None, self.network) ^ self.identifier.resolve(None, self.network)

        if self.comparator == self.Comparator.ISPARENT:
            return other.resolve(None, self.network)["IS-A"] == self.identifier

        return False

    def __eq__(self, other):
        if not isinstance(other, IdentifierQuery):
            return super().__eq__(other)

        return self.network == other.network and self.identifier == other.identifier and self.comparator == other.comparator
