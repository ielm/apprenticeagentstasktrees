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

    def view(self, matches):
        from backend.models.path import Path
        from backend.models.view import View

        query = matches[2]

        paths = list(filter(lambda match: isinstance(match, Path), matches))
        if len(paths) == 0:
            paths = None

        return View(self.network, matches[1], query=query, follow=paths)

    def view_all(self, matches):
        return None

    def view_query(self, matches):
        return matches[0]

    def path(self, matches):
        from backend.models.path import Path, PathStep
        path = Path()
        for match in filter(lambda match: isinstance(match, PathStep), matches):
            path.to_step(match)
        return path

    def step(self, matches):
        from backend.models.path import PathStep
        from backend.models.query import FrameQuery
        from lark.lexer import Token
        relation = matches[0]
        recursive = "RECURSIVE" in map(lambda token: token.type, filter(lambda match: isinstance(match, Token), matches))
        query = None

        for match in matches:
            if isinstance(match, FrameQuery):
                query = match

        return PathStep(relation, recursive, query)

    def to(self, matches):
        from backend.models.query import FrameQuery, Query
        return FrameQuery(self.network, list(filter(lambda match: isinstance(match, Query), matches))[0])

    def relation(self, matches):
        return str(matches[0])

    def frame_query(self, matches):
        from backend.models.query import FrameQuery, Query
        return FrameQuery(self.network, list(filter(lambda match: isinstance(match, Query), matches))[0])

    def frame_id_query(self, matches):
        return matches[0]

    def logical_slot_query(self, matches):
        return matches[0]

    def logical_and_slot_query(self, matches):
        from backend.models.query import AndQuery, Query
        return AndQuery(self.network, list(filter(lambda match: isinstance(match, Query), matches)))

    def logical_or_slot_query(self, matches):
        from backend.models.query import OrQuery, Query
        return OrQuery(self.network, list(filter(lambda match: isinstance(match, Query), matches)))

    def logical_not_slot_query(self, matches):
        from backend.models.query import NotQuery
        return NotQuery(self.network, matches[1])

    def logical_exact_slot_query(self, matches):
        from backend.models.query import ExactQuery
        return ExactQuery(self.network, matches[1].queries)

    def slot_query(self, matches):
        from backend.models.query import SlotQuery
        return SlotQuery(self.network, matches[0])

    def slot_name_only_query(self, matches):
        from backend.models.query import NameQuery
        return NameQuery(self.network, matches[1])

    def slot_name_fillers_query(self, matches):
        from backend.models.query import AndQuery, NameQuery
        if matches[0] == "*":
            return matches[1]
        else:
            return AndQuery(self.network, [NameQuery(self.network, matches[0]), matches[1]])

    def logical_filler_query(self, matches):
        return matches[0]

    def logical_and_filler_query(self, matches):
        from backend.models.query import AndQuery, Query
        return AndQuery(self.network, list(filter(lambda match: isinstance(match, Query), matches)))

    def logical_or_filler_query(self, matches):
        from backend.models.query import OrQuery, Query
        return OrQuery(self.network, list(filter(lambda match: isinstance(match, Query), matches)))

    def logical_not_filler_query(self, matches):
        from backend.models.query import NotQuery
        return NotQuery(self.network, matches[1])

    def logical_exact_filler_query(self, matches):
        from backend.models.query import ExactQuery
        return ExactQuery(self.network, matches[1].queries)

    def filler_query(self, matches):
        from backend.models.query import FillerQuery
        return FillerQuery(self.network, matches[0])

    def identifier_query(self, matches):
        from backend.models.query import IdentifierQuery
        comparator = None
        if matches[0] == "=":
            comparator = IdentifierQuery.Comparator.EQUALS
        elif matches[0] == "^":
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

    def tmr(self, matches):
        return "TMR#" + str(matches[0])

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
