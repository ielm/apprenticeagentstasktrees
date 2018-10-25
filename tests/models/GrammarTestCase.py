from backend.agent import Agent
from backend.models.agenda import Action, Condition, Goal
from backend.models.grammar import Grammar
from backend.models.graph import Identifier, Literal, Network
from backend.models.mps import AgentMethod
from backend.models.path import Path
from backend.models.query import AndQuery, ExactQuery, FillerQuery, FrameQuery, IdentifierQuery, LiteralQuery, NameQuery, NotQuery, OrQuery, SlotQuery
from backend.models.statement import AddFillerStatement, AssignFillerStatement, CapabilityStatement, ExistsStatement, ForEachStatement, IsStatement, MakeInstanceStatement, MeaningProcedureStatement
from backend.models.view import View

import unittest


class GrammarTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()

    def test_parse_instance(self):
        self.assertEqual(1, Grammar.parse(self.n, "1", start="instance"))
        self.assertEqual(123, Grammar.parse(self.n, "123", start="instance"))

    def test_parse_name(self):
        self.assertEqual("EVENT", Grammar.parse(self.n, "EVENT", start="name"))
        self.assertEqual("EvEnT", Grammar.parse(self.n, "EvEnT", start="name"))
        self.assertEqual("Ev-EnT", Grammar.parse(self.n, "Ev-EnT", start="name"))
        self.assertEqual("EvEn_T", Grammar.parse(self.n, "EvEn_T", start="name"))
        self.assertEqual("*EvEn.T", Grammar.parse(self.n, "*EvEn.T", start="name"))

    def test_parse_graph(self):
        self.assertEqual("WM", Grammar.parse(self.n, "WM", start="graph"))
        self.assertEqual("TmR", Grammar.parse(self.n, "TmR", start="graph"))
        self.assertEqual("TMR#123456", Grammar.parse(self.n, "TMR#123456", start="graph"))

    def test_parse_identifier(self):
        self.assertEqual(Identifier("WM", "EVENT", instance=1), Grammar.parse(self.n, "WM.EVENT.1", start="identifier"))
        self.assertEqual(Identifier(None, "EVENT", instance=1), Grammar.parse(self.n, "EVENT.1", start="identifier"))
        self.assertEqual(Identifier("WM", "EVENT"), Grammar.parse(self.n, "WM.EVENT", start="identifier"))
        self.assertEqual(Identifier(None, "EVENT"), Grammar.parse(self.n, "EVENT", start="identifier"))
        with self.assertRaises(Exception):
            Grammar.parse(self.n, "True", start="identifier")
        with self.assertRaises(Exception):
            Grammar.parse(self.n, "False", start="identifier")

    def test_parse_integer(self):
        self.assertEqual(1, Grammar.parse(self.n, "1", start="integer"))
        self.assertEqual(123, Grammar.parse(self.n, "123", start="integer"))

    def test_parse_double(self):
        self.assertEqual(1.0, Grammar.parse(self.n, "1.0", start="double"))
        self.assertEqual(1.01, Grammar.parse(self.n, "1.01", start="double"))

    def test_parse_string(self):
        self.assertEqual("test", Grammar.parse(self.n, "\"test\"", start="string"))
        self.assertEqual("123", Grammar.parse(self.n, "\"123\"", start="string"))
        self.assertEqual("12ac3b3", Grammar.parse(self.n, "\"12ac3b3\"", start="string"))

    def test_parse_literal(self):
        self.assertEqual(Literal(1), Grammar.parse(self.n, "1", start="literal"))
        self.assertEqual(Literal(1.0), Grammar.parse(self.n, "1.0", start="literal"))
        self.assertEqual(Literal("test"), Grammar.parse(self.n, "\"test\"", start="literal"))
        self.assertEqual(Literal("123"), Grammar.parse(self.n, "\"123\"", start="literal"))
        self.assertEqual("12ac3b3", Grammar.parse(self.n, "\"12ac3b3\"", start="literal"))
        self.assertEqual(True, Grammar.parse(self.n, "True", start="literal"))
        self.assertEqual(True, Grammar.parse(self.n, "TRUE", start="literal"))
        self.assertEqual(False, Grammar.parse(self.n, "False", start="literal"))
        self.assertEqual(False, Grammar.parse(self.n, "FaLsE", start="literal"))

    def test_parse_literal_query(self):
        self.assertEqual(LiteralQuery(self.n, 123), Grammar.parse(self.n, "=123", start="literal_query"))
        self.assertEqual(LiteralQuery(self.n, 123), Grammar.parse(self.n, "= 123", start="literal_query"))

    def test_parse_identifier_query(self):
        self.assertEqual(IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.EQUALS), Grammar.parse(self.n, "=WM.HUMAN.1", start="identifier_query"))
        self.assertEqual(IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.EQUALS), Grammar.parse(self.n, "= WM.HUMAN.1", start="identifier_query"))
        self.assertEqual(IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.EQUALS, set=False), Grammar.parse(self.n, "=! WM.HUMAN.1", start="identifier_query"))
        self.assertEqual(IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.ISA), Grammar.parse(self.n, "^WM.HUMAN.1", start="identifier_query"))
        self.assertEqual(IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.ISA), Grammar.parse(self.n, "^ WM.HUMAN.1", start="identifier_query"))
        self.assertEqual(IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.ISA, set=False), Grammar.parse(self.n, "^! WM.HUMAN.1", start="identifier_query"))
        self.assertEqual(IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.ISPARENT), Grammar.parse(self.n, "^.WM.HUMAN.1", start="identifier_query"))
        self.assertEqual(IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.ISPARENT), Grammar.parse(self.n, "^. WM.HUMAN.1", start="identifier_query"))
        self.assertEqual(IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.ISPARENT, set=False), Grammar.parse(self.n, "^.! WM.HUMAN.1", start="identifier_query"))
        self.assertEqual(IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.SUBCLASSES), Grammar.parse(self.n, ">WM.HUMAN.1", start="identifier_query"))
        self.assertEqual(IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.SUBCLASSES), Grammar.parse(self.n, "> WM.HUMAN.1", start="identifier_query"))
        self.assertEqual(IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.SUBCLASSES, set=False), Grammar.parse(self.n, ">! WM.HUMAN.1", start="identifier_query"))
        self.assertEqual(IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.SUBCLASSES, from_concept=True), Grammar.parse(self.n, "~> WM.HUMAN.1", start="identifier_query"))

    def test_parse_filler_query(self):
        self.assertEqual(FillerQuery(self.n, LiteralQuery(self.n, 123)), Grammar.parse(self.n, "=123", start="filler_query"))
        self.assertEqual(FillerQuery(self.n, IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.EQUALS)), Grammar.parse(self.n, "=WM.HUMAN.1", start="filler_query"))

    def test_parse_slot_query(self):
        nq = NameQuery(self.n, "THEME")
        fq1 = FillerQuery(self.n, LiteralQuery(self.n, 123))
        fq2 = FillerQuery(self.n, LiteralQuery(self.n, 456))

        self.assertEqual(SlotQuery(self.n, nq), Grammar.parse(self.n, "HAS THEME", start="slot_query"))
        self.assertEqual(SlotQuery(self.n, nq), Grammar.parse(self.n, "has THEME", start="slot_query"))
        self.assertEqual(SlotQuery(self.n, fq1), Grammar.parse(self.n, "* = 123", start="slot_query"))
        self.assertEqual(SlotQuery(self.n, fq1), Grammar.parse(self.n, "* (= 123)", start="slot_query"))
        self.assertEqual(SlotQuery(self.n, AndQuery(self.n, [NameQuery(self.n, "*CTX.SLOT"), fq1])), Grammar.parse(self.n, "*CTX.SLOT = 123", start="slot_query"))
        self.assertEqual(SlotQuery(self.n, AndQuery(self.n, [fq1, fq2])), Grammar.parse(self.n, "* (= 123 AND = 456)", start="slot_query"))
        self.assertEqual(SlotQuery(self.n, AndQuery(self.n, [fq1, fq2])), Grammar.parse(self.n, "* (= 123 and = 456)", start="slot_query"))
        self.assertEqual(SlotQuery(self.n, OrQuery(self.n, [fq1, fq2])), Grammar.parse(self.n, "* (= 123 OR = 456)", start="slot_query"))
        self.assertEqual(SlotQuery(self.n, OrQuery(self.n, [fq1, fq2])), Grammar.parse(self.n, "* (= 123 or = 456)", start="slot_query"))
        self.assertEqual(SlotQuery(self.n, NotQuery(self.n, fq1)), Grammar.parse(self.n, "* NOT = 123", start="slot_query"))
        self.assertEqual(SlotQuery(self.n, NotQuery(self.n, fq1)), Grammar.parse(self.n, "* not = 123", start="slot_query"))
        self.assertEqual(SlotQuery(self.n, NotQuery(self.n, fq1)), Grammar.parse(self.n, "* NOT (= 123)", start="slot_query"))
        self.assertEqual(SlotQuery(self.n, ExactQuery(self.n, [fq1, fq2])), Grammar.parse(self.n, "* EXACTLY (= 123 AND = 456)", start="slot_query"))
        self.assertEqual(SlotQuery(self.n, ExactQuery(self.n, [fq1, fq2])), Grammar.parse(self.n, "* exactly (= 123 AND = 456)", start="slot_query"))
        self.assertEqual(SlotQuery(self.n, AndQuery(self.n, [nq, ExactQuery(self.n, [fq1, fq2])])), Grammar.parse(self.n, "THEME EXACTLY (= 123 AND = 456)", start="slot_query"))

    def test_parse_frame_query(self):
        iq = IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.EQUALS)
        sq1 = SlotQuery(self.n, AndQuery(self.n, [NameQuery(self.n, "THEME"), FillerQuery(self.n, LiteralQuery(self.n, 123))]))
        sq2 = SlotQuery(self.n, AndQuery(self.n, [NameQuery(self.n, "THEME"), FillerQuery(self.n, LiteralQuery(self.n, 456))]))

        self.assertEqual(FrameQuery(self.n, sq1), Grammar.parse(self.n, "WHERE THEME = 123", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, sq1), Grammar.parse(self.n, "where THEME = 123", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, sq1), Grammar.parse(self.n, "SHOW FRAMES WHERE THEME = 123", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, sq1), Grammar.parse(self.n, "show frames where THEME = 123", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, sq1), Grammar.parse(self.n, "WHERE (THEME = 123)", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, AndQuery(self.n, [sq1, sq2])), Grammar.parse(self.n, "WHERE (THEME = 123 AND THEME = 456)", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, AndQuery(self.n, [sq1, sq2])), Grammar.parse(self.n, "WHERE (THEME = 123 and THEME = 456)", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, OrQuery(self.n, [sq1, sq2])), Grammar.parse(self.n, "WHERE (THEME = 123 OR THEME = 456)", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, OrQuery(self.n, [sq1, sq2])), Grammar.parse(self.n, "WHERE (THEME = 123 or THEME = 456)", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, NotQuery(self.n, sq1)), Grammar.parse(self.n, "WHERE NOT THEME = 123", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, NotQuery(self.n, sq1)), Grammar.parse(self.n, "WHERE not THEME = 123", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, NotQuery(self.n, sq1)), Grammar.parse(self.n, "WHERE NOT (THEME = 123)", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, ExactQuery(self.n, [sq1, sq2])), Grammar.parse(self.n, "WHERE EXACTLY (THEME = 123 AND THEME = 456)", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, ExactQuery(self.n, [sq1, sq2])), Grammar.parse(self.n, "WHERE exactly (THEME = 123 AND THEME = 456)", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, iq), Grammar.parse(self.n, "WHERE @ =WM.HUMAN.1", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, AndQuery(self.n, [iq, sq1])), Grammar.parse(self.n, "WHERE (@ =WM.HUMAN.1 AND THEME = 123)", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, OrQuery(self.n, [iq, sq1])), Grammar.parse(self.n, "WHERE (@ =WM.HUMAN.1 OR THEME = 123)", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, NotQuery(self.n, iq)), Grammar.parse(self.n, "WHERE NOT (@ =WM.HUMAN.1)", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, NotQuery(self.n, iq)), Grammar.parse(self.n, "WHERE NOT @ =WM.HUMAN.1", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, IdentifierQuery(self.n, "ONT.EVENT", IdentifierQuery.Comparator.ISA)), Grammar.parse(self.n, "WHERE @^ONT.EVENT", start="frame_query"))

    def test_parse_view_graph(self):
        g1 = self.n.register("TEST")
        g2 = self.n.register("TMR#123")
        self.assertEqual(View(self.n, g1), Grammar.parse(self.n, "VIEW TEST SHOW ALL"))
        self.assertEqual(View(self.n, g1), Grammar.parse(self.n, "view TEST show all"))
        self.assertEqual(View(self.n, g2), Grammar.parse(self.n, "view TMR#123 show all"))

    def test_parse_view_graph_with_query(self):
        g = self.n.register("TEST")
        query = FrameQuery(self.n, IdentifierQuery(self.n, "TEST.FRAME.1", IdentifierQuery.Comparator.EQUALS))
        self.assertEqual(View(self.n, g, query=query), Grammar.parse(self.n, "VIEW TEST SHOW FRAMES WHERE @=TEST.FRAME.1"))
        self.assertEqual(View(self.n, g, query=query), Grammar.parse(self.n, "view TEST show frames where @=TEST.FRAME.1"))

    def test_parse_follow(self):
        self.assertEqual(Path().to("REL"), Grammar.parse(self.n, "[REL]->", start="path"))
        self.assertEqual(Path().to("*"), Grammar.parse(self.n, "[*]->", start="path"))
        self.assertEqual(Path().to("REL1").to("REL2"), Grammar.parse(self.n, "[REL1]->[REL2]->", start="path"))
        self.assertEqual(Path().to("REL1").to("REL2"), Grammar.parse(self.n, "[REL1]-> [REL2]->", start="path"))
        self.assertEqual(Path().to("REL1").to("REL2"), Grammar.parse(self.n, "[REL1]-> THEN [REL2]->", start="path"))
        self.assertEqual(Path().to("REL", recursive=True), Grammar.parse(self.n, "[REL*]->", start="path"))
        self.assertEqual(Path().to("REL", recursive=True), Grammar.parse(self.n, "[REL *]->", start="path"))
        self.assertEqual(Path().to("REL", query=FrameQuery(self.n, IdentifierQuery(self.n, "TEST.FRAME.1", IdentifierQuery.Comparator.EQUALS))), Grammar.parse(self.n, "[REL]->TO @ = TEST.FRAME.1", start="path"))
        self.assertEqual(Path().to("REL", query=FrameQuery(self.n, IdentifierQuery(self.n, "TEST.FRAME.1", IdentifierQuery.Comparator.EQUALS))), Grammar.parse(self.n, "[REL]-> TO @ = TEST.FRAME.1", start="path"))
        self.assertEqual(Path().to("REL", query=FrameQuery(self.n, IdentifierQuery(self.n, "TEST.FRAME.1", IdentifierQuery.Comparator.EQUALS))).to("OTHER"), Grammar.parse(self.n, "[REL]-> TO @ = TEST.FRAME.1 [OTHER]->", start="path"))
        self.assertEqual(Path().to("REL", query=FrameQuery(self.n, IdentifierQuery(self.n, "TEST.FRAME.1", IdentifierQuery.Comparator.EQUALS))).to("OTHER"), Grammar.parse(self.n, "[REL]-> TO @ = TEST.FRAME.1 THEN [OTHER]->", start="path"))

    def test_parse_view_graph_with_path(self):
        g = self.n.register("TEST")
        self.assertEqual(View(self.n, g, follow=Path().to("REL")), Grammar.parse(self.n, "VIEW TEST SHOW ALL FOLLOW [REL]->"))
        self.assertEqual(View(self.n, g, follow=Path().to("REL").to("OTHER")), Grammar.parse(self.n, "view TEST SHOW ALL FOLLOW [REL]->[OTHER]->"))
        self.assertEqual(View(self.n, g, follow=[Path().to("REL1"), Path().to("REL2")]), Grammar.parse(self.n, "view TEST SHOW ALL FOLLOW [REL1]-> AND FOLLOW [REL2]->"))


class AgendaGrammarTestCase(unittest.TestCase):

    class TestAgent(Agent):
        def __init__(self, g, agent):
            from backend.models.statement import StatementHierarchy
            Network.__init__(self)
            self.register(g)
            self.register(StatementHierarchy().build())

            self.exe = g
            self.internal = g
            self.ontology = g
            self.wo_memory = g
            self.lt_memory = g
            self.identity = agent

    def setUp(self):
        from backend.models.graph import Graph
        self.g = Graph("SELF")
        self.agentFrame = self.g.register("AGENT")

        self.agent = AgendaGrammarTestCase.TestAgent(self.g, self.agentFrame)

    def test_statement_instance(self):
        concept = self.g.register("MYCONCEPT")
        instance = self.g.register("FRAME", generate_index=True)

        # SELF refers to the agent's identity
        self.assertEqual(self.agentFrame, Grammar.parse(self.agent, "SELF", start="statement_instance", agent=self.agent))

        # An instance can be created on a specified graph (by name); here "SELF" is the graph name, and TEST.MYCONCEPT is an identifier to make an instance of
        self.assertEqual(MakeInstanceStatement.instance(self.g, self.g._namespace, concept, []), Grammar.parse(self.agent, "@SELF:SELF.MYCONCEPT()", start="statement_instance", agent=self.agent))

        # Graph names don't need to be known; a few have unique identifiers, but must be followed by the "!" to be
        # registered as such;  AGENT.INTERNAL, AGENT.EXE, AGENT.ONTOLOGY, AGENT.WM, and AGENT.LT are valid
        self.assertEqual(MakeInstanceStatement.instance(self.g, self.g._namespace, concept, []), Grammar.parse(self.agent, "@AGENT.INTERNAL!:SELF.MYCONCEPT()", start="statement_instance", agent=self.agent))

        # If a fully qualified identifier is not provided, the agent's EXE graph will be assumed
        self.assertEqual(MakeInstanceStatement.instance(self.g, self.g._namespace, concept, []), Grammar.parse(self.agent, "@SELF:MYCONCEPT()", start="statement_instance", agent=self.agent))

        # New instances can include arguments
        self.assertEqual(MakeInstanceStatement.instance(self.g, self.g._namespace, concept, ["$arg1", "$arg2"]), Grammar.parse(self.agent, "@SELF:SELF.MYCONCEPT($arg1, $arg2)", start="statement_instance", agent=self.agent))

        # A simple identifier is also a valid statement instance
        self.assertEqual(instance, Grammar.parse(self.agent, "#SELF.FRAME.1", start="statement_instance", agent=self.agent))

        # Any variable can also be used
        self.assertEqual("$var1", Grammar.parse(self.agent, "$var1", start="statement_instance", agent=self.agent))

    def test_is_statement(self):
        f = self.g.register("FRAME")

        self.assertEqual(IsStatement.instance(self.g, f, "SLOT", 123), Grammar.parse(self.agent, "#SELF.FRAME[SLOT] == 123", start="is_statement", agent=self.agent))

    def test_make_instance_statement(self):
        concept = self.g.register("MYCONCEPT")
        self.assertEqual(MakeInstanceStatement.instance(self.g, self.g._namespace, concept, []), Grammar.parse(self.agent, "@SELF:SELF.MYCONCEPT()", start="make_instance_statement", agent=self.agent))
        self.assertEqual(MakeInstanceStatement.instance(self.g, self.g._namespace, concept, []), Grammar.parse(self.agent, "@AGENT.INTERNAL!:SELF.MYCONCEPT()", start="make_instance_statement", agent=self.agent))
        self.assertEqual(MakeInstanceStatement.instance(self.g, self.g._namespace, concept, []), Grammar.parse(self.agent, "@SELF:MYCONCEPT()", start="make_instance_statement", agent=self.agent))
        self.assertEqual(MakeInstanceStatement.instance(self.g, self.g._namespace, concept, ["$arg1", "$arg2"]), Grammar.parse(self.agent, "@SELF:SELF.MYCONCEPT($arg1, $arg2)", start="make_instance_statement", agent=self.agent))

    def test_add_filler_statement(self):
        f = self.g.register("FRAME")

        statement = AddFillerStatement.instance(self.g, self.agentFrame, "SLOT", 123)
        parsed = Grammar.parse(self.agent, "SELF[SLOT] += 123", start="add_filler_statement", agent=self.agent)
        self.assertEqual(statement, parsed)

        statement = AddFillerStatement.instance(self.g, self.agentFrame, "SLOT", f)
        parsed = Grammar.parse(self.agent, "SELF[SLOT] += #SELF.FRAME", start="add_filler_statement", agent=self.agent)
        self.assertEqual(statement, parsed)

        statement = AddFillerStatement.instance(self.g, f, "SLOT", 123)
        parsed = Grammar.parse(self.agent, "#SELF.FRAME[SLOT] += 123", start="add_filler_statement", agent=self.agent)
        self.assertEqual(statement, parsed)

    def test_assign_filler_statement(self):
        f = self.g.register("FRAME")

        statement = AssignFillerStatement.instance(self.g, self.agentFrame, "SLOT", 123)
        parsed = Grammar.parse(self.agent, "SELF[SLOT] = 123", start="assign_filler_statement", agent=self.agent)
        self.assertEqual(statement, parsed)

        statement = AssignFillerStatement.instance(self.g, self.agentFrame, "SLOT", f)
        parsed = Grammar.parse(self.agent, "SELF[SLOT] = #SELF.FRAME", start="assign_filler_statement", agent=self.agent)
        self.assertEqual(statement, parsed)

        statement = AssignFillerStatement.instance(self.g, f, "SLOT", 123)
        parsed = Grammar.parse(self.agent, "#SELF.FRAME[SLOT] = 123", start="assign_filler_statement", agent=self.agent)
        self.assertEqual(statement, parsed)

    def test_exists_statement(self):
        statement = ExistsStatement.instance(self.g, SlotQuery(self.agent, AndQuery(self.agent, [NameQuery(self.agent, "THEME"), FillerQuery(self.agent, LiteralQuery(self.agent, 123))])))
        parsed = Grammar.parse(self.agent, "EXISTS THEME = 123", start="exists_statement", agent=self.agent)
        self.assertEqual(statement, parsed)

    def test_foreach_statement(self):
        query = SlotQuery(self.agent, AndQuery(self.agent, [NameQuery(self.agent, "THEME"), FillerQuery(self.agent, LiteralQuery(self.agent, 123))]))
        statement = ForEachStatement.instance(self.g, query, "$var", AddFillerStatement.instance(self.g, "$var", "SLOT", 456))
        parsed = Grammar.parse(self.agent, "FOR EACH $var IN THEME = 123 | $var[SLOT] += 456", start="foreach_statement", agent=self.agent)
        self.assertEqual(statement, parsed)

        query = SlotQuery(self.agent, AndQuery(self.agent, [NameQuery(self.agent, "THEME"), FillerQuery(self.agent, LiteralQuery(self.agent, 123))]))
        statement = ForEachStatement.instance(self.g, query, "$var", [AddFillerStatement.instance(self.g, "$var", "SLOT", 456), AddFillerStatement.instance(self.g, "$var", "SLOT", 456)])
        parsed = Grammar.parse(self.agent, "FOR EACH $var IN THEME = 123 | $var[SLOT] += 456 | $var[SLOT] += 456", start="foreach_statement", agent=self.agent)
        self.assertEqual(statement, parsed)

    def test_mp_statement(self):
        statement = MeaningProcedureStatement.instance(self.g, "mp1", [])
        parsed = Grammar.parse(self.agent, "SELF.mp1()", start="mp_statement", agent=self.agent)
        self.assertEqual(statement, parsed)

        statement = MeaningProcedureStatement.instance(self.g, "mp1", ["$var1", "$var2"])
        parsed = Grammar.parse(self.agent, "SELF.mp1($var1, $var2)", start="mp_statement", agent=self.agent)
        self.assertEqual(statement, parsed)

    def test_capability_statement(self):
        self.agent.exe.register("TEST-CAPABILITY")

        statement = CapabilityStatement.instance(self.agent.exe, "SELF.TEST-CAPABILITY", [], [])
        parsed = Grammar.parse(self.agent, "CAPABILITY #SELF.TEST-CAPABILITY()", start="capability_statement", agent=self.agent)
        self.assertEqual(statement, parsed)

        statement = CapabilityStatement.instance(self.agent.exe, "SELF.TEST-CAPABILITY", [], ["$var1", "$var2"])
        parsed = Grammar.parse(self.agent, "CAPABILITY #SELF.TEST-CAPABILITY($var1, $var2)", start="capability_statement", agent=self.agent)
        self.assertEqual(statement, parsed)

        callback1 = AssignFillerStatement.instance(self.g, self.agentFrame, "SLOTA", 123)
        callback2 = AssignFillerStatement.instance(self.g, self.agentFrame, "SLOTB", 456)
        statement = CapabilityStatement.instance(self.agent.exe, "SELF.TEST-CAPABILITY", [callback1, callback2], [])
        parsed = Grammar.parse(self.agent, "CAPABILITY #SELF.TEST-CAPABILITY() | THEN DO SELF[SLOTA] = 123 | THEN DO SELF[SLOTB] = 456", start="capability_statement", agent=self.agent)
        self.assertEqual(statement, parsed)

    def test_action(self):

        action = Action.build(self.g, "testaction", Action.DEFAULT, Action.IDLE)
        parsed = Grammar.parse(self.agent, "ACTION (testaction) SELECT DEFAULT DO IDLE", start="action", agent=self.agent)
        self.assertEqual(action, parsed)

        query = SlotQuery(self.agent, AndQuery(self.agent, [NameQuery(self.agent, "THEME"), FillerQuery(self.agent, LiteralQuery(self.agent, 123))]))
        action = Action.build(self.g, "testaction", ExistsStatement.instance(self.g, query), Action.IDLE)
        parsed = Grammar.parse(self.agent, "ACTION (testaction) SELECT IF EXISTS THEME = 123 DO IDLE", start="action", agent=self.agent)
        self.assertEqual(action, parsed)

        statement = MeaningProcedureStatement.instance(self.g, "mp1", [])
        action = Action.build(self.g, "testaction", Action.DEFAULT, [statement, statement])
        parsed = Grammar.parse(self.agent, "ACTION (testaction) SELECT DEFAULT DO SELF.mp1() DO SELF.mp1()", start="action", agent=self.agent)
        self.assertEqual(action, parsed)

    def test_condition(self):
        query = SlotQuery(self.agent, AndQuery(self.agent, [NameQuery(self.agent, "THEME"), FillerQuery(self.agent, LiteralQuery(self.agent, 123))]))

        condition = Condition.build(self.g, [ExistsStatement.instance(self.g, query)], Goal.Status.SATISFIED, logic=Condition.Logic.AND, order=1)
        parsed = Grammar.parse(self.agent, "WHEN EXISTS THEME = 123 THEN satisfied", start="condition", agent=self.agent)
        self.assertEqual(condition, parsed)

        condition = Condition.build(self.g, [ExistsStatement.instance(self.g, query), ExistsStatement.instance(self.g, query)], Goal.Status.SATISFIED, logic=Condition.Logic.AND, order=1)
        parsed = Grammar.parse(self.agent, "WHEN EXISTS THEME = 123 AND EXISTS THEME = 123 THEN satisfied", start="condition", agent=self.agent)
        self.assertEqual(condition, parsed)

        condition = Condition.build(self.g, [ExistsStatement.instance(self.g, query), ExistsStatement.instance(self.g, query)], Goal.Status.SATISFIED, logic=Condition.Logic.OR, order=1)
        parsed = Grammar.parse(self.agent, "WHEN EXISTS THEME = 123 OR EXISTS THEME = 123 THEN satisfied", start="condition", agent=self.agent)
        self.assertEqual(condition, parsed)

    def test_define_goal(self):
        # A goal has a name and a destination graph, and a default priority
        goal: Goal = Grammar.parse(self.agent, "DEFINE XYZ() AS GOAL IN SELF", start="define", agent=self.agent).goal
        self.assertTrue(goal.frame.name() in self.g)
        self.assertEqual(goal.name(), "XYZ")
        self.assertEqual(goal.priority(self.agent), 0.5)

        # A goal can be overwritten
        goal: Goal = Grammar.parse(self.agent, "DEFINE XYZ() AS GOAL IN SELF", start="define", agent=self.agent).goal
        self.assertTrue(goal.frame.name() in self.g)
        self.assertEqual(goal.name(), "XYZ")
        self.assertEqual(2, len(self.g)) # One is the agent, the other is the overwritten goal

        # A goal can have parameters
        goal: Goal = Goal.define(self.g, "XYZ", 0.5, 0.5, [], [], ["$var1", "$var2"])
        parsed: Goal = Grammar.parse(self.agent, "DEFINE XYZ($var1, $var2) AS GOAL IN SELF", start="define", agent=self.agent).goal
        self.assertEqual(goal, parsed)

        # A goal can have a numeric priority
        goal: Goal = Goal.define(self.g, "XYZ", 0.9, 0.5, [], [], [])
        parsed: Goal = Grammar.parse(self.agent, "DEFINE XYZ() AS GOAL IN SELF PRIORITY 0.9", start="define", agent=self.agent).goal
        self.assertEqual(goal, parsed)

        # A goal can have a statement priority
        goal: Goal = Goal.define(self.g, "XYZ", MeaningProcedureStatement.instance(self.g, "mp1", []).frame, 0.5, [], [], [])
        parsed: Goal = Grammar.parse(self.agent, "DEFINE XYZ() AS GOAL IN SELF PRIORITY SELF.mp1()", start="define", agent=self.agent).goal
        self.assertEqual(goal.frame["PRIORITY"].singleton()["CALLS"].singleton(), parsed.frame["PRIORITY"].singleton()["CALLS"].singleton())

        # A goal can have a numeric resources
        goal: Goal = Goal.define(self.g, "XYZ", 0.5, 0.9, [], [], [])
        parsed: Goal = Grammar.parse(self.agent, "DEFINE XYZ() AS GOAL IN SELF RESOURCES 0.9", start="define", agent=self.agent).goal
        self.assertEqual(goal, parsed)

        # A goal can have a statement resources
        goal: Goal = Goal.define(self.g, "XYZ", 0.5, MeaningProcedureStatement.instance(self.g, "mp1", []).frame, [], [], [])
        parsed: Goal = Grammar.parse(self.agent, "DEFINE XYZ() AS GOAL IN SELF RESOURCES SELF.mp1()", start="define", agent=self.agent).goal
        self.assertEqual(goal.frame["RESOURCES"].singleton()["CALLS"].singleton(), parsed.frame["RESOURCES"].singleton()["CALLS"].singleton())

        # A goal can have plans (actions)
        a1: Action = Action.build(self.g, "action_a", Action.DEFAULT, Action.IDLE)
        a2: Action = Action.build(self.g, "action_b", Action.DEFAULT, Action.IDLE)
        goal: Goal = Goal.define(self.g, "XYZ", 0.5, 0.5, [a1, a2], [], [])
        parsed: Goal = Grammar.parse(self.agent, "DEFINE XYZ() AS GOAL IN SELF ACTION (action_a) SELECT DEFAULT DO IDLE ACTION (action_b) SELECT DEFAULT DO IDLE", start="define", agent=self.agent).goal
        self.assertEqual(goal, parsed)

        # A goal can have conditions (which are ordered as written)
        q1 = SlotQuery(self.agent, AndQuery(self.agent, [NameQuery(self.agent, "THEME"), FillerQuery(self.agent, LiteralQuery(self.agent, 123))]))
        q2 = SlotQuery(self.agent, AndQuery(self.agent, [NameQuery(self.agent, "THEME"), FillerQuery(self.agent, LiteralQuery(self.agent, 456))]))
        c1: Condition = Condition.build(self.g, [ExistsStatement.instance(self.g, q1)], Goal.Status.SATISFIED, Condition.Logic.AND, 1)
        c2: Condition = Condition.build(self.g, [ExistsStatement.instance(self.g, q2)], Goal.Status.ABANDONED, Condition.Logic.AND, 2)
        goal: Goal = Goal.define(self.g, "XYZ", 0.5, 0.5, [], [c1, c2], [])
        parsed: Goal = Grammar.parse(self.agent, "DEFINE XYZ() AS GOAL IN SELF WHEN EXISTS THEME = 123 THEN satisfied WHEN EXISTS THEME = 456 THEN abandoned", start="define", agent=self.agent).goal
        self.assertEqual(goal, parsed)

    def test_find_something_to_do(self):
        graph = self.g
        goal1 = Goal.define(graph, "FIND-SOMETHING-TO-DO", 0.1, 0.5, [
            Action.build(graph,
                         "acknowledge input",
                         ExistsStatement.instance(graph, Grammar.parse(self.agent,
                                                                     "(@^ SELF.INPUT-TMR AND ACKNOWLEDGED = False)", start="logical_slot_query")),
                         ForEachStatement.instance(graph, Grammar.parse(self.agent,
                                                                      "(@^ SELF.INPUT-TMR AND ACKNOWLEDGED = False)", start="logical_slot_query"),
                                                   "$tmr", [
                                                       AddFillerStatement.instance(graph, self.agent.identity, "HAS-GOAL",
                                                                                   MakeInstanceStatement.instance(graph,
                                                                                                                  "SELF",
                                                                                                                  "SELF.UNDERSTAND-TMR",
                                                                                                                  [
                                                                                                                      "$tmr"])),
                                                       AssignFillerStatement.instance(graph, "$tmr", "ACKNOWLEDGED",
                                                                                      True)
                                                   ])
                         ),
            Action.build(graph, "idle", Action.DEFAULT, Action.IDLE)
        ], [], [])

        script = '''
        DEFINE FIND-SOMETHING-TO-DO()
            AS GOAL
            IN SELF
            PRIORITY 0.1
            ACTION (acknowledge input)
                SELECT IF EXISTS (@^ SELF.INPUT-TMR AND ACKNOWLEDGED = FALSE)
                DO FOR EACH $tmr IN (@^ SELF.INPUT-TMR AND ACKNOWLEDGED = FALSE)
                | SELF[HAS-GOAL] += @SELF:SELF.UNDERSTAND-TMR($tmr)
                | $tmr[ACKNOWLEDGED] = True
            ACTION (idle)
                SELECT DEFAULT
                DO IDLE
        '''

        parsed: Goal = Grammar.parse(self.agent, script, start="define", agent=self.agent).goal
        self.assertEqual(goal1, parsed)


class BootstrapGrammarTestCase(unittest.TestCase):

    class TestAgent(Agent):
        def __init__(self, g, agent):
            from backend.models.statement import StatementHierarchy
            Network.__init__(self)
            self.register(g)
            self.register(StatementHierarchy().build())

            self.exe = g
            self.internal = g
            self.ontology = g
            self.wo_memory = g
            self.lt_memory = g
            self.identity = agent

    def setUp(self):
        from backend.models.graph import Graph
        self.g = Graph("SELF")
        self.agentFrame = self.g.register("AGENT")

        self.agent = AgendaGrammarTestCase.TestAgent(self.g, self.agentFrame)

    def test_bootstrap_comments(self):
        input = '''
        // A comment
        @SELF.AGENT += {myslot 123}; // More comments
        @SELF.AGENT += {myslot 123}; // More comments
        @SELF.AGENT += {myslot 123};
        '''

        bootstrap = Grammar.parse(self.agent, input, start="bootstrap", agent=self.agent)
        self.assertEqual(3, len(bootstrap))

    def test_bootstrap_multiple(self):
        from backend.models.bootstrap import Bootstrap

        input = '''
        @SELF.AGENT += {myslot 123};
        
        @SELF.AGENT += {myslot 123}
        ;
        
        
        @SELF.AGENT += {myslot 123};
        '''

        bootstrap = Grammar.parse(self.agent, input, start="bootstrap", agent=self.agent)
        self.assertEqual(3, len(bootstrap))
        for b in bootstrap:
            self.assertIsInstance(b, Bootstrap)

    def test_declare_knowledge(self):
        from backend.models.bootstrap import BootstrapDeclareKnowledge, BootstrapTriple

        bootstrap = BootstrapDeclareKnowledge(self.agent, "MYGRAPH", "MYFRAME")
        parsed = Grammar.parse(self.agent, "@MYGRAPH.MYFRAME = {}", start="declare_knowledge", agent=self.agent)
        self.assertEqual(bootstrap, parsed)

        bootstrap = BootstrapDeclareKnowledge(self.agent, "MYGRAPH", "MYFRAME", index=123)
        parsed = Grammar.parse(self.agent, "@MYGRAPH.MYFRAME.123 = {}", start="declare_knowledge", agent=self.agent)
        self.assertEqual(bootstrap, parsed)

        bootstrap = BootstrapDeclareKnowledge(self.agent, "MYGRAPH", "MYFRAME", index=True)
        parsed = Grammar.parse(self.agent, "@MYGRAPH.MYFRAME.? = {}", start="declare_knowledge", agent=self.agent)
        self.assertEqual(bootstrap, parsed)

        bootstrap = BootstrapDeclareKnowledge(self.agent, "MYGRAPH", "MYFRAME", isa="ONT.ALL")
        parsed = Grammar.parse(self.agent, "@MYGRAPH.MYFRAME = {ISA @ONT.ALL}", start="declare_knowledge", agent=self.agent)
        self.assertEqual(bootstrap, parsed)

        bootstrap = BootstrapDeclareKnowledge(self.agent, "MYGRAPH", "MYFRAME", isa=["ONT.ALL", "ONT.OTHER"])
        parsed = Grammar.parse(self.agent, "@MYGRAPH.MYFRAME = {ISA @ONT.ALL; ISA @ONT.OTHER}", start="declare_knowledge", agent=self.agent)
        self.assertEqual(bootstrap, parsed)

        bootstrap = BootstrapDeclareKnowledge(self.agent, "MYGRAPH", "MYFRAME", properties=[BootstrapTriple("MYPROP", Identifier.parse("ONT.ALL"))])
        parsed = Grammar.parse(self.agent, "@MYGRAPH.MYFRAME = {MYPROP @ONT.ALL}", start="declare_knowledge", agent=self.agent)
        self.assertEqual(bootstrap, parsed)

        bootstrap = BootstrapDeclareKnowledge(self.agent, "MYGRAPH", "MYFRAME", properties=[BootstrapTriple("MYPROP", Identifier.parse("ONT.ALL")), BootstrapTriple("OTHERPROP", Literal("VALUE"))])
        parsed = Grammar.parse(self.agent, "@MYGRAPH.MYFRAME = {MYPROP @ONT.ALL; OTHERPROP \"VALUE\"}", start="declare_knowledge", agent=self.agent)
        self.assertEqual(bootstrap, parsed)

        bootstrap = BootstrapDeclareKnowledge(self.agent, "MYGRAPH", "MYFRAME", properties=[BootstrapTriple("MYPROP", Identifier.parse("ONT.ALL"), facet="SEM")])
        parsed = Grammar.parse(self.agent, "@MYGRAPH.MYFRAME = {MYPROP SEM @ONT.ALL}", start="declare_knowledge", agent=self.agent)
        self.assertEqual(bootstrap, parsed)

    def test_append_knowledge(self):
        from backend.models.bootstrap import BootstrapAppendKnowledge, BootstrapTriple

        f = self.g.register("FRAME")

        bootstrap = BootstrapAppendKnowledge(self.agent, "SELF.FRAME", properties=[BootstrapTriple("MYPROP", Identifier.parse("ONT.ALL"))])
        parsed = Grammar.parse(self.agent, "@SELF.FRAME += {MYPROP @ONT.ALL}", start="append_knowledge", agent=self.agent)
        self.assertEqual(bootstrap, parsed)

        bootstrap = BootstrapAppendKnowledge(self.agent, "SELF.FRAME", properties=[BootstrapTriple("MYPROP", Identifier.parse("ONT.ALL")), BootstrapTriple("OTHERPROP", Literal("VALUE"))])
        parsed = Grammar.parse(self.agent, "@SELF.FRAME += {MYPROP @ONT.ALL; OTHERPROP \"VALUE\"}", start="append_knowledge", agent=self.agent)
        self.assertEqual(bootstrap, parsed)

        bootstrap = BootstrapAppendKnowledge(self.agent, "SELF.FRAME", properties=[BootstrapTriple("MYPROP", Identifier.parse("ONT.ALL"), facet="SEM")])
        parsed = Grammar.parse(self.agent, "@SELF.FRAME += {MYPROP SEM @ONT.ALL}", start="append_knowledge", agent=self.agent)
        self.assertEqual(bootstrap, parsed)

    def test_register_mp(self):
        from backend.models.bootstrap import BootstrapRegisterMP

        bootstrap = BootstrapRegisterMP(TestAgentMethod)
        parsed = Grammar.parse(self.agent, "REGISTER MP tests.models.GrammarTestCase.TestAgentMethod", start="register_mp", agent=self.agent)
        self.assertEqual(bootstrap, parsed)

        bootstrap = BootstrapRegisterMP(TestAgentMethod, name="TestMP")
        parsed = Grammar.parse(self.agent, "REGISTER MP tests.models.GrammarTestCase.TestAgentMethod AS TestMP", start="register_mp", agent=self.agent)
        self.assertEqual(bootstrap, parsed)


class TestAgentMethod(AgentMethod):
    pass