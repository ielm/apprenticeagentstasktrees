from backend.models.graph import Identifier, Literal, Network
from lark import Lark, Transformer
from pkgutil import get_data

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.agent import Agent


class Grammar(object):

    @classmethod
    def parse(cls, network: Network, input: str, resource: str="backend.resources", peg: str="grammar.lark", start: str="start", agent: 'Agent'=None):
        grammar = get_data(resource, peg).decode('ascii')
        lark = Lark(grammar, start=start)
        tree = lark.parse(input)
        return GrammarTransformer(network, agent=agent).transform(tree)


class GrammarTransformer(Transformer):

    def __init__(self, network: Network, agent: 'Agent'=None):
        super().__init__()
        self.network = network
        self.agent = agent

    def start(self, matches):
        return matches[0]

    # Bootstrap

    def bootstrap(self, matches):
        from backend.models.bootstrap import Bootstrap
        return list(filter(lambda match: isinstance(match, Bootstrap), matches))

    def declare_knowledge(self, matches):
        from backend.models.bootstrap import BootstrapDeclareKnowledge, BootstrapTriple

        graph = matches[0]
        name = matches[1]
        index = False if str(matches[2]) == "=" else matches[2]
        isa = list(filter(lambda m: isinstance(m, Identifier), matches))
        properties = list(filter(lambda m: isinstance(m, BootstrapTriple), matches))

        return BootstrapDeclareKnowledge(self.network, graph, name, index=index, isa=isa, properties=properties)

    def declare_knowledge_instance(self, matches):
        if isinstance(matches[0], int):
            return matches[0]
        return True

    def declare_knowledge_element(self, matches):
        return matches[0]

    def declare_isa_knowledge(self, matches):
        return matches[1]

    def declare_property_knowledge(self, matches):
        from backend.models.bootstrap import BootstrapTriple
        slot = matches[0]
        facet = matches[1] if len(matches) == 3 else None
        filler = matches[-1]

        return BootstrapTriple(slot, filler, facet=facet)

    def append_knowledge(self, matches):
        from backend.models.bootstrap import BootstrapAppendKnowledge, BootstrapTriple

        identifier = matches[0]
        properties = list(filter(lambda m: isinstance(m, BootstrapTriple), matches))

        return BootstrapAppendKnowledge(self.network, identifier, properties)

    def append_knowledge_element(self, matches):
        return matches[0]

    def append_property_knowledge(self, matches):
        from backend.models.bootstrap import BootstrapTriple
        slot = matches[0]
        facet = matches[1] if len(matches) == 3 else None
        filler = matches[-1]

        return BootstrapTriple(slot, filler, facet=facet)

    def slot(self, matches):
        return str(matches[0])

    def facet(self, matches):
        return str(matches[0])

    def filler(self, matches):
        return matches[0]

    # Statements and executables

    def define(self, matches):
        return matches[1]

    def goal(self, matches):
        from backend.models.agenda import Action, Condition, Goal
        from backend.models.bootstrap import BoostrapGoal

        name = str(matches[0])
        variables = matches[1]
        graph = matches[5]

        priority = matches[6]
        resources = matches[7]
        plan = list(filter(lambda match: isinstance(match, Action), matches))
        conditions = list(filter(lambda match: isinstance(match, Condition), matches))

        condition_order = 1
        for c in conditions:
            c.frame["ORDER"] = condition_order
            condition_order += 1

        return BoostrapGoal(Goal.define(self.agent[graph], name, priority, resources, plan, conditions, variables))

    def priority(self, matches):
        from backend.models.statement import Statement

        if len(matches) == 2:
            if isinstance(matches[1], Statement):
                return matches[1].frame
            return matches[1]

        return 0.5

    def resources(self, matches):
        from backend.models.statement import Statement

        if len(matches) == 2:
            if isinstance(matches[1], Statement):
                return matches[1].frame
            return matches[1]

        return 0.5

    def goal_status(self, matches):
        from backend.models.agenda import Goal
        if str(matches[0]).upper() == "PENDING":
            return Goal.Status.PENDING
        if str(matches[0]).upper() == "ACTIVE":
            return Goal.Status.ACTIVE
        if str(matches[0]).upper() == "ABANDONED":
            return Goal.Status.ABANDONED
        if str(matches[0]).upper() == "SATISFIED":
            return Goal.Status.SATISFIED

    def action(self, matches):
        from backend.models.agenda import Action
        name = matches[1]
        select = matches[2]
        perform = matches[3:]

        return Action.build(self.agent.exe, name, select, perform)

    def action_selection(self, matches):
        from backend.models.agenda import Action
        select = matches[1]
        if str(select) == "DEFAULT":
            select = Action.DEFAULT
        elif str(select) == "IF":
            select = matches[2]

        return select

    def action_do(self, matches):
        from backend.models.agenda import Action
        perform = matches[1]

        if str(perform) == "IDLE":
            perform = Action.IDLE

        return perform

    def condition(self, matches):
        from backend.models.agenda import Condition, Goal

        statements = matches[1][1]
        status = matches[3]
        logic = matches[1][0]

        return Condition.build(self.agent.exe, statements, status, logic=logic)

    def condition_and(self, matches):
        from backend.models.agenda import Condition
        from backend.models.agenda import Statement

        return Condition.Logic.AND, list(filter(lambda match: isinstance(match, Statement), matches))

    def condition_or(self, matches):
        from backend.models.agenda import Condition
        from backend.models.agenda import Statement

        return Condition.Logic.OR, list(filter(lambda match: isinstance(match, Statement), matches))

    def condition_nand(self, matches):
        from backend.models.agenda import Condition
        from backend.models.agenda import Statement

        return Condition.Logic.NAND, list(filter(lambda match: isinstance(match, Statement), matches))

    def condition_nor(self, matches):
        from backend.models.agenda import Condition
        from backend.models.agenda import Statement

        return Condition.Logic.NOR, list(filter(lambda match: isinstance(match, Statement), matches))

    def condition_not(self, matches):
        from backend.models.agenda import Condition
        from backend.models.agenda import Statement

        return Condition.Logic.NOT, list(filter(lambda match: isinstance(match, Statement), matches))

    def statement(self, matches):
        return matches[0]

    def boolean_statement(self, matches):
        return matches[0]

    def add_filler_statement(self, matches):
        from backend.models.statement import AddFillerStatement
        domain = matches[0]
        slot = str(matches[1])
        filler = matches[2]

        return AddFillerStatement.instance(self.agent.exe, domain, slot, filler)

    def assign_filler_statement(self, matches):
        from backend.models.statement import AssignFillerStatement
        domain = matches[0]
        slot = str(matches[1])
        filler = matches[3]

        return AssignFillerStatement.instance(self.agent.exe, domain, slot, filler)

    def capability_statement(self, matches):
        from backend.models.statement import CapabilityStatement, Statement
        capability = matches[1]
        callback = list(filter(lambda match: isinstance(match, Statement), matches))
        params = matches[2]

        return CapabilityStatement.instance(self.agent.exe, capability, callback, params)

    def exists_statement(self, matches):
        from backend.models.statement import ExistsStatement

        return ExistsStatement.instance(self.agent.exe, matches[1])

    def foreach_statement(self, matches):
        from backend.models.statement import ForEachStatement

        return ForEachStatement.instance(self.agent.exe, matches[4], str(matches[2]), matches[5:])

    def is_statement(self, matches):
        from backend.models.statement import IsStatement
        domain = matches[0]
        slot = str(matches[1])
        filler = matches[4]

        return IsStatement.instance(self.agent.exe, domain, slot, filler)

    def mp_statement(self, matches):
        from backend.models.statement import MeaningProcedureStatement

        return MeaningProcedureStatement.instance(self.agent.exe, matches[1], matches[2])

    def statement_instance(self, matches):
        if isinstance(matches[0], Identifier):
            if matches[0].render() == "SELF":
                return self.agent.identity
            return matches[0].resolve(None, network=self.network)
        if str(matches[0]) == "SELF":
            return self.agent.identity

        return matches[0]

    def make_instance_statement(self, matches):
        from backend.models.statement import MakeInstanceStatement
        in_graph = matches[0]
        of = matches[1]
        params = matches[2]

        return MakeInstanceStatement.instance(self.agent.exe, in_graph, of, params)

    def arguments(self, matches):
        return matches

    def argument(self, matches):
        return str(matches[0])

    def special_agent_graph(self, matches):
        name = str(matches[0]).upper()

        return {
            "INTERNAL": self.agent.internal._namespace,
            "EXE": self.agent.exe._namespace,
            "ONTOLOGY": self.agent.ontology._namespace,
            "WM": self.agent.wo_memory._namespace,
            "LT": self.agent.lt_memory._namespace
        }[name]

    # Views and querying

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
        from_concept = False
        if matches[0] == "~":
            from_concept = True
            matches = matches[1:]
        comparator = None
        if matches[0] == "=":
            comparator = IdentifierQuery.Comparator.EQUALS
        elif matches[0] == "^":
            comparator = IdentifierQuery.Comparator.ISA
        elif matches[0] == "^.":
            comparator = IdentifierQuery.Comparator.ISPARENT
        elif matches[0] == ">":
            comparator = IdentifierQuery.Comparator.SUBCLASSES
        set = True
        if matches[1] == "!":
            set = False
        return IdentifierQuery(self.network, matches[-1], comparator, set=set, from_concept=from_concept)

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

    def boolean(self, matches):
        return matches[0].lower() == "true"
