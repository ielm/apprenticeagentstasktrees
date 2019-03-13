# from backend.agent import Agent
from backend.models.grammar import Grammar
# from backend.models.graph import Filler, Frame, Identifier, Literal, Network, Slot
from enum import Enum
from functools import reduce
from ontograph import graph
from ontograph.Frame import Frame, Slot
from ontograph.Index import Identifier
from typing import Any, List, Union


class Filler(object): pass
class Literal(object): pass
class Network(object): pass


class Query(object):

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

    def search(self) -> List[Frame]:
        results = []
        for space in graph:
            for frame in space:
                if self.compare(frame):
                    results.append(frame)
        return results

class AndQuery(Query):

    def __init__(self, queries: List[Query]):
        self.queries = queries

    def compare(self, other) -> bool:
        if len(self.queries) == 0:
            return False

        return reduce(lambda x, y: x and y, map(lambda query: query.compare(other), self.queries))

    def __str__(self):
        return "(" + " and ".join(list(map(lambda q: str(q), self.queries))) + ")"

    def __eq__(self, other):
        if not isinstance(other, AndQuery):
            return super().__eq__(other)
        return self.queries == other.queries


class OrQuery(Query):

    def __init__(self, queries: List[Query]):
        self.queries = queries

    def compare(self, other) -> bool:
        if len(self.queries) == 0:
            return False

        return reduce(lambda x, y: x or y, map(lambda query: query.compare(other), self.queries))

    def __str__(self):
        return "(" + " or ".join(list(map(lambda q: str(q), self.queries))) + ")"

    def __eq__(self, other):
        if not isinstance(other, OrQuery):
            return super().__eq__(other)
        return self.queries == other.queries


class ExactQuery(Query):

    def __init__(self, queries: List[Query]):
        self.queries = queries

    def compare(self, other: List[Any]) -> bool:
        if isinstance(other, str):
            return False

        try:
            iter(other)
        except TypeError:
            return False

        if isinstance(other, Frame):
            other = list(other)

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
        return self.queries == other.queries


class NotQuery(Query):

    def __init__(self, query: Query):
        self.query = query

    def compare(self, other) -> bool:
        return not self.query.compare(other)

    def __str__(self):
        return "not " + str(self.query)

    def __eq__(self, other):
        if not isinstance(other, NotQuery):
            return super().__eq__(other)
        return self.query == other.query


class FrameQuery(Query):

    def __init__(self, subquery: Union[AndQuery, OrQuery, NotQuery, ExactQuery, 'IdentifierQuery', 'SlotQuery']):
        self.subquery = subquery

    def compare(self, other: Frame) -> bool:
        return self.subquery.compare(other)

    def __str__(self):
        return str(self.subquery)

    def __eq__(self, other):
        if not isinstance(other, FrameQuery):
            return super().__eq__(other)
        return self.subquery == other.subquery


class SimpleFrameQuery(FrameQuery):

    def __init__(self, network: Network, comparator="and"):
        logic = AndQuery(network, [])
        if comparator == "or":
            logic = OrQuery(network, [])
        elif comparator == "not":
            logic = NotQuery(network, None)
        elif comparator == "exactly":
            logic = ExactQuery(network, [])
        super().__init__(network, logic)

    def _append(self, query: Query):
        if isinstance(self.subquery, NotQuery):
            self.subquery.query = query
        else:
            self.subquery.queries.append(query)

    def id(self, identifier: Union[Frame, Filler, Identifier, str]) -> 'SimpleFrameQuery':
        if isinstance(identifier, Frame):
            identifier = identifier._identifier
        elif isinstance(identifier, Filler):
            identifier = identifier._value
        elif isinstance(identifier, str):
            identifier = Identifier.parse(identifier)

        self._append(IdentifierQuery(self.network, identifier, IdentifierQuery.Comparator.EQUALS))
        return self

    def isa(self, identifier: Union[Frame, Filler, Identifier, str], set: bool=True, from_concept: bool=False) -> 'SimpleFrameQuery':
        if isinstance(identifier, Frame):
            identifier = identifier._identifier
        elif isinstance(identifier, Filler):
            identifier = identifier._value
        elif isinstance(identifier, str):
            identifier = Identifier.parse(identifier)

        self._append(IdentifierQuery(self.network, identifier, IdentifierQuery.Comparator.ISA, set=set, from_concept=from_concept))
        return self

    def sub(self, identifier: Union[Frame, Filler, Identifier, str], set: bool=True, from_concept: bool=False) -> 'SimpleFrameQuery':
        if isinstance(identifier, Frame):
            identifier = identifier._identifier
        elif isinstance(identifier, Filler):
            identifier = identifier._value
        elif isinstance(identifier, str):
            identifier = Identifier.parse(identifier)

        self._append(IdentifierQuery(self.network, identifier, IdentifierQuery.Comparator.SUBCLASSES, set=set, from_concept=from_concept))
        return self

    def has(self, slot: Union[Slot, str]) -> 'SimpleFrameQuery':
        if isinstance(slot, Slot):
            slot = slot._name

        self._append(SlotQuery(self.network, NameQuery(self.network, slot)))
        return self

    def f(self, slot: Union[Slot, str], filler: Union[Filler, Identifier, Literal, Any]) -> 'SimpleFrameQuery':
        if isinstance(slot, Slot):
            slot = slot._name

        if isinstance(filler, Filler):
            filler = filler._value
        elif not isinstance(filler, Identifier) and not isinstance(filler, Literal):
            filler = Filler(filler)._value

        vq = IdentifierQuery(self.network, filler, IdentifierQuery.Comparator.EQUALS) if isinstance(filler, Identifier) else LiteralQuery(self.network, filler)
        vq = FillerQuery(self.network, vq)

        self._append(SlotQuery(self.network, AndQuery(self.network, [NameQuery(self.network, slot), vq])))
        return self

    def fisa(self, slot: Union[Slot, str], filler: Union[Filler, Identifier]) -> 'SimpleFrameQuery':
        if isinstance(slot, Slot):
            slot = slot._name

        if isinstance(filler, Filler):
            filler = filler._value

        vq = FillerQuery(self.network, IdentifierQuery(self.network, filler, IdentifierQuery.Comparator.ISA))

        self._append(SlotQuery(self.network, AndQuery(self.network, [NameQuery(self.network, slot), vq])))
        return self


class SlotQuery(Query):

    def __init__(self, subquery: Union[AndQuery, OrQuery, ExactQuery, NotQuery, 'NameQuery', 'FillerQuery']):
        self.subquery = subquery

    def compare(self, other: Union[Frame, Slot]) -> bool:
        if isinstance(other, Frame):
            for slot in other:
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

    def __str__(self):
        if isinstance(self.subquery, AndQuery) and len(self.subquery.queries) == 2 and isinstance(self.subquery.queries[0], NameQuery) and isinstance(self.subquery.queries[1], FillerQuery):
            slot = str(self.subquery.queries[0]).replace("*slot is ", "")
            filler = str(self.subquery.queries[1]).replace("*value ", "")
            return slot + " " + filler

        return str(self.subquery)

    def __eq__(self, other):
        if not isinstance(other, SlotQuery):
            return super().__eq__(other)
        return self.subquery == other.subquery


class NameQuery(Query):

    def __init__(self, name: str):
        self.name = name

    def compare(self, other: Slot) -> bool:
        return other.property == self.name

    def __str__(self):
        return "*slot is " + self.name

    def __eq__(self, other):
        if not isinstance(other, NameQuery):
            return super().__eq__(other)
        return self.name == other.name


class FillerQuery(Query):

    def __init__(self, query: Union['LiteralQuery', 'IdentifierQuery']):
        self.query = query

    def compare(self, other: Union[Slot, Any]) -> bool:
        if isinstance(other, Slot):
            for filler in other:
                if self.query.compare(filler):
                    return True
            return False

        return self.query.compare(other)

    def __str__(self):
        return str(self.query)

    def __eq__(self, other):
        if not isinstance(other, FillerQuery):
            return super().__eq__(other)
        return self.query == other.query


class LiteralQuery(Query):

    def __init__(self, value):
        self.value = value

    def compare(self, other) -> bool:
        return self.value == other

    def __str__(self):
        return "*value = " + str(self.value)

    def __eq__(self, other):
        if not isinstance(other, LiteralQuery):
            return super().__eq__(other)
        return self.value == other.value


class IdentifierQuery(Query):

    class Comparator(Enum):
        EQUALS = 1      # Is self.identifier exactly the same as the input
        ISA = 2         # Is self.identifier an ancestor of the input
        ISPARENT = 3    # Is self.identifier the immediate parent of the input
        SUBCLASSES = 4  # Is self.identifier a child of the input

    def __init__(self, identifier: Union[Identifier, Frame, str], comparator: Comparator, set: bool=True, from_concept: bool=False):
        if isinstance(identifier, Frame):
            identifier = identifier.id
        if isinstance(identifier, Identifier):
            identifier = identifier.id

        self.identifier = identifier
        self.comparator = comparator
        self.set = set
        self.from_concept = from_concept

    def compare(self, other: Union[Frame, Identifier, str]) -> bool:
        if isinstance(other, Identifier):
            other = other.id

        if isinstance(other, Frame):
            other = other.id

        if not isinstance(other, str):
            return False

        if self.from_concept:
            other = Frame(other).parents()[0].id if len(Frame(other).parents()) > 0 else "@ONT.ALL"

        if self.set:
            frame = Frame(other)
            for filler in frame["ELEMENTS"]:
                if self.compare(filler):
                    return True

        if self.comparator == self.Comparator.EQUALS:
            return self.identifier == other

        if self.comparator == self.Comparator.ISA:
            return Frame(other) ^ Frame(self.identifier)

        if self.comparator == self.Comparator.ISPARENT:
            other = Frame(other)
            return self.identifier in other.parents()

        if self.comparator == self.Comparator.SUBCLASSES:
            return Frame(self.identifier) ^ Frame(other)

        return False

    def __str__(self):
        operator = ""
        if self.comparator == IdentifierQuery.Comparator.EQUALS:
            operator = "="
        if self.comparator == IdentifierQuery.Comparator.ISA:
            operator = "^"
        if self.comparator == IdentifierQuery.Comparator.ISPARENT:
            operator = "^."
        if self.comparator == IdentifierQuery.Comparator.SUBCLASSES:
            operator = ">"

        if not self.set:
            operator = operator + "!"

        if self.from_concept:
            operator = "~" + operator

        return "*value " + operator + " " + str(self.identifier)

    def __eq__(self, other):
        if not isinstance(other, IdentifierQuery):
            return super().__eq__(other)

        return self.identifier == other.identifier and self.comparator == other.comparator and self.set == other.set and self.from_concept == other.from_concept
