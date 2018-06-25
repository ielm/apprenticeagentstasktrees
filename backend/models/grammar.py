from backend.models.graph import Identifier, Literal, Network
from lark import Lark, Transformer
from pkgutil import get_data


class Grammar(object):

    @classmethod
    def parse(cls, network: Network, input: str, resource: str="backend.resources", peg: str="grammar.lark", start: str="start"):
        grammar = get_data(resource, peg).decode('ascii')
        lark = Lark(grammar, start=start)
        tree = lark.parse(input)
        return GrammarTransformer(network).transform(tree)


class GrammarTransformer(Transformer):

    def __init__(self, network: Network):
        super().__init__()
        self.network = network

    def start(self, matches):
        return matches[0]

    def frame_query(self, matches):
        from backend.models.query import FrameQuery
        return FrameQuery(self.network, matches[0])

    def frame_id_query(self, matches):
        return matches[0]

    def logical_slot_query(self, matches):
        return matches[0]

    def logical_and_slot_query(self, matches):
        from backend.models.query import AndQuery
        return AndQuery(self.network, matches)

    def logical_or_slot_query(self, matches):
        from backend.models.query import OrQuery
        return OrQuery(self.network, matches)

    def logical_not_slot_query(self, matches):
        from backend.models.query import NotQuery
        return NotQuery(self.network, matches[0])

    def logical_exact_slot_query(self, matches):
        from backend.models.query import ExactQuery
        return ExactQuery(self.network, matches[0].queries)

    def slot_query(self, matches):
        from backend.models.query import SlotQuery
        return SlotQuery(self.network, matches[0])

    def slot_name_only_query(self, matches):
        from backend.models.query import NameQuery
        return NameQuery(self.network, matches[0])

    def slot_name_fillers_query(self, matches):
        from backend.models.query import AndQuery, NameQuery
        if matches[0] == "*":
            return matches[1]
        else:
            return AndQuery(self.network, [NameQuery(self.network, matches[0]), matches[1]])

    def logical_filler_query(self, matches):
        return matches[0]

    def logical_and_filler_query(self, matches):
        from backend.models.query import AndQuery
        return AndQuery(self.network, matches)

    def logical_or_filler_query(self, matches):
        from backend.models.query import OrQuery
        return OrQuery(self.network, matches)

    def logical_not_filler_query(self, matches):
        from backend.models.query import NotQuery
        return NotQuery(self.network, matches[0])

    def logical_exact_filler_query(self, matches):
        from backend.models.query import ExactQuery
        return ExactQuery(self.network, matches[0].queries)

    def filler_query(self, matches):
        from backend.models.query import FillerQuery
        return FillerQuery(self.network, matches[0])

    def identifier_query(self, matches):
        from backend.models.query import IdentifierQuery
        comparator = None
        if matches[0] == "=":
            comparator = IdentifierQuery.Comparator.EQUALS
        elif matches[0] == "^=":
            comparator = IdentifierQuery.Comparator.ISA
        elif matches[0] == "^.":
            comparator = IdentifierQuery.Comparator.ISPARENT
        return IdentifierQuery(self.network, matches[1], comparator)

    def literal_query(self, matches):
        from backend.models.query import LiteralQuery
        return LiteralQuery(self.network, matches[1])

    def identifier(self, matches):
        return Identifier.parse(".".join(map(lambda match: str(match), matches)))

    def literal(self, matches):
        return Literal(matches[0])

    def graph(self, matches):
        return str(matches[0])

    def name(self, matches):
        return str(matches[0])

    def instance(self, matches):
        return int(matches[0])

    def double(self, matches):
        return float(".".join(map(lambda match: str(match), matches)))

    def integer(self, matches):
        return int(matches[0])

    def string(self, matches):
        return "".join(matches)
