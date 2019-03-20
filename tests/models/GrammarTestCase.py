# from backend.agent import Agent
# from backend.models.bootstrap import Bootstrap
# from backend.models.agenda import Condition, Effect, Goal, Plan, Step
# from backend.models.grammar import Grammar
# from backend.models.mps import AgentMethod
# from backend.models.output import OutputXMRTemplate
# from backend.models.path import Path
# from backend.models.query import AndQuery, ExactQuery, FillerQuery, FrameQuery, IdentifierQuery, LiteralQuery, NameQuery, NotQuery, OrQuery, SlotQuery
# from backend.models.statement import AddFillerStatement, AssertStatement, AssignFillerStatement, AssignVariableStatement, ExistsStatement, ExpectationStatement, ForEachStatement, IsStatement, MakeInstanceStatement, MeaningProcedureStatement, OutputXMRStatement, TransientFrameStatement
# from backend.models.view import View
# from backend.models.xmr import XMR
# from ontograph import graph
# from ontograph.Frame import Frame
# from ontograph.Index import Identifier
# from ontograph.Query import IdComparator
# from ontograph.Space import Space
#
# import unittest
#
#
# @DeprecationWarning
# class GrammarTestCase(unittest.TestCase):
#
#     def setUp(self):
#         class TestAgent(Agent):
#             def __init__(self):
#                 pass
#
#         graph.reset()
#         self.a = TestAgent()
#
#     @DeprecationWarning
#     def test_parse_instance(self):
#         self.assertEqual(1, Grammar.parse(self.a, "1", start="instance"))
#         self.assertEqual(123, Grammar.parse(self.a, "123", start="instance"))
#
#     @DeprecationWarning
#     def test_parse_name(self):
#         self.assertEqual("EVENT", Grammar.parse(self.a, "EVENT", start="name"))
#         self.assertEqual("EvEnT", Grammar.parse(self.a, "EvEnT", start="name"))
#         self.assertEqual("Ev-EnT", Grammar.parse(self.a, "Ev-EnT", start="name"))
#         self.assertEqual("EvEn_T", Grammar.parse(self.a, "EvEn_T", start="name"))
#         self.assertEqual("*EvEnT", Grammar.parse(self.a, "*EvEnT", start="name"))
#
#     @DeprecationWarning
#     def test_parse_graph(self):
#         self.assertEqual("WM", Grammar.parse(self.a, "WM", start="graph"))
#         self.assertEqual("TmR", Grammar.parse(self.a, "TmR", start="graph"))
#         self.assertEqual("TMR#123456", Grammar.parse(self.a, "TMR#123456", start="graph"))
#         self.assertEqual("XMR#123456", Grammar.parse(self.a, "XMR#123456", start="graph"))
#         self.assertEqual("XMR-TEMPLATE#123456", Grammar.parse(self.a, "XMR-TEMPLATE#123456", start="graph"))
#
#     @DeprecationWarning
#     def test_parse_identifier(self):
#         self.assertEqual(Identifier("@WM.EVENT.1"), Grammar.parse(self.a, "@WM.EVENT.1", start="identifier"))
#         self.assertEqual(Identifier("@EVENT.1"), Grammar.parse(self.a, "@EVENT.1", start="identifier"))
#         self.assertEqual(Identifier("@WM.EVENT"), Grammar.parse(self.a, "@WM.EVENT", start="identifier"))
#         self.assertEqual(Identifier("@EVENT"), Grammar.parse(self.a, "@EVENT", start="identifier"))
#         with self.assertRaises(Exception):
#             Grammar.parse(self.a, "True", start="identifier")
#         with self.assertRaises(Exception):
#             Grammar.parse(self.a, "False", start="identifier")
#
#     @DeprecationWarning
#     def test_parse_integer(self):
#         self.assertEqual(1, Grammar.parse(self.a, "1", start="integer"))
#         self.assertEqual(123, Grammar.parse(self.a, "123", start="integer"))
#
#     @DeprecationWarning
#     def test_parse_double(self):
#         self.assertEqual(1.0, Grammar.parse(self.a, "1.0", start="double"))
#         self.assertEqual(1.01, Grammar.parse(self.a, "1.01", start="double"))
#
#     @DeprecationWarning
#     def test_parse_string(self):
#         self.assertEqual("test", Grammar.parse(self.a, "\"test\"", start="string"))
#         self.assertEqual("123", Grammar.parse(self.a, "\"123\"", start="string"))
#         self.assertEqual("12ac3b3", Grammar.parse(self.a, "\"12ac3b3\"", start="string"))
#
#     @DeprecationWarning
#     def test_parse_literal(self):
#         self.assertEqual(1, Grammar.parse(self.a, "1", start="literal"))
#         self.assertEqual(1.0, Grammar.parse(self.a, "1.0", start="literal"))
#         self.assertEqual("test", Grammar.parse(self.a, "\"test\"", start="literal"))
#         self.assertEqual("123", Grammar.parse(self.a, "\"123\"", start="literal"))
#         self.assertEqual("12ac3b3", Grammar.parse(self.a, "\"12ac3b3\"", start="literal"))
#         self.assertEqual(True, Grammar.parse(self.a, "True", start="literal"))
#         self.assertEqual(True, Grammar.parse(self.a, "TRUE", start="literal"))
#         self.assertEqual(False, Grammar.parse(self.a, "False", start="literal"))
#         self.assertEqual(False, Grammar.parse(self.a, "FaLsE", start="literal"))
#
#     @DeprecationWarning
#     def test_parse_literal_query(self):
#         self.assertEqual(LiteralQuery(123), Grammar.parse(self.a, "=123", start="literal_query"))
#         self.assertEqual(LiteralQuery(123), Grammar.parse(self.a, "= 123", start="literal_query"))
#
#     @DeprecationWarning
#     def test_parse_identifier_query(self):
#         self.assertEqual(IdentifierQuery("@WM.HUMAN.1", IdentifierQuery.Comparator.EQUALS), Grammar.parse(self.a, "=@WM.HUMAN.1", start="identifier_query"))
#         self.assertEqual(IdentifierQuery("@WM.HUMAN.1", IdentifierQuery.Comparator.EQUALS), Grammar.parse(self.a, "= @WM.HUMAN.1", start="identifier_query"))
#         self.assertEqual(IdentifierQuery("@WM.HUMAN.1", IdentifierQuery.Comparator.EQUALS, set=False), Grammar.parse(self.a, "=! @WM.HUMAN.1", start="identifier_query"))
#         self.assertEqual(IdentifierQuery("@WM.HUMAN.1", IdentifierQuery.Comparator.ISA), Grammar.parse(self.a, "^@WM.HUMAN.1", start="identifier_query"))
#         self.assertEqual(IdentifierQuery("@WM.HUMAN.1", IdentifierQuery.Comparator.ISA), Grammar.parse(self.a, "^ @WM.HUMAN.1", start="identifier_query"))
#         self.assertEqual(IdentifierQuery("@WM.HUMAN.1", IdentifierQuery.Comparator.ISA, set=False), Grammar.parse(self.a, "^! @WM.HUMAN.1", start="identifier_query"))
#         self.assertEqual(IdentifierQuery("@WM.HUMAN.1", IdentifierQuery.Comparator.ISPARENT), Grammar.parse(self.a, "^.@WM.HUMAN.1", start="identifier_query"))
#         self.assertEqual(IdentifierQuery("@WM.HUMAN.1", IdentifierQuery.Comparator.ISPARENT), Grammar.parse(self.a, "^. @WM.HUMAN.1", start="identifier_query"))
#         self.assertEqual(IdentifierQuery("@WM.HUMAN.1", IdentifierQuery.Comparator.ISPARENT, set=False), Grammar.parse(self.a, "^.! @WM.HUMAN.1", start="identifier_query"))
#         self.assertEqual(IdentifierQuery("@WM.HUMAN.1", IdentifierQuery.Comparator.SUBCLASSES), Grammar.parse(self.a, ">@WM.HUMAN.1", start="identifier_query"))
#         self.assertEqual(IdentifierQuery("@WM.HUMAN.1", IdentifierQuery.Comparator.SUBCLASSES), Grammar.parse(self.a, "> @WM.HUMAN.1", start="identifier_query"))
#         self.assertEqual(IdentifierQuery("@WM.HUMAN.1", IdentifierQuery.Comparator.SUBCLASSES, set=False), Grammar.parse(self.a, ">! @WM.HUMAN.1", start="identifier_query"))
#         self.assertEqual(IdentifierQuery("@WM.HUMAN.1", IdentifierQuery.Comparator.SUBCLASSES, from_concept=True), Grammar.parse(self.a, "~> @WM.HUMAN.1", start="identifier_query"))
#
#     @DeprecationWarning
#     def test_parse_filler_query(self):
#         self.assertEqual(FillerQuery(LiteralQuery(123)), Grammar.parse(self.a, "=123", start="filler_query"))
#         self.assertEqual(FillerQuery(IdentifierQuery("@WM.HUMAN.1", IdentifierQuery.Comparator.EQUALS)), Grammar.parse(self.a, "=@WM.HUMAN.1", start="filler_query"))
#
#     @DeprecationWarning
#     def test_parse_slot_query(self):
#         nq = NameQuery("THEME")
#         fq1 = FillerQuery(LiteralQuery(123))
#         fq2 = FillerQuery(LiteralQuery(456))
#
#         self.assertEqual(SlotQuery(nq), Grammar.parse(self.a, "HAS THEME", start="slot_query"))
#         self.assertEqual(SlotQuery(nq), Grammar.parse(self.a, "has THEME", start="slot_query"))
#         self.assertEqual(SlotQuery(fq1), Grammar.parse(self.a, "* = 123", start="slot_query"))
#         self.assertEqual(SlotQuery(fq1), Grammar.parse(self.a, "* (= 123)", start="slot_query"))
#         self.assertEqual(SlotQuery(AndQuery([NameQuery("*CTX.SLOT"), fq1])), Grammar.parse(self.a, "*CTX.SLOT = 123", start="slot_query"))
#         self.assertEqual(SlotQuery(AndQuery([fq1, fq2])), Grammar.parse(self.a, "* (= 123 AND = 456)", start="slot_query"))
#         self.assertEqual(SlotQuery(AndQuery([fq1, fq2])), Grammar.parse(self.a, "* (= 123 and = 456)", start="slot_query"))
#         self.assertEqual(SlotQuery(OrQuery([fq1, fq2])), Grammar.parse(self.a, "* (= 123 OR = 456)", start="slot_query"))
#         self.assertEqual(SlotQuery(OrQuery([fq1, fq2])), Grammar.parse(self.a, "* (= 123 or = 456)", start="slot_query"))
#         self.assertEqual(SlotQuery(NotQuery(fq1)), Grammar.parse(self.a, "* NOT = 123", start="slot_query"))
#         self.assertEqual(SlotQuery(NotQuery(fq1)), Grammar.parse(self.a, "* not = 123", start="slot_query"))
#         self.assertEqual(SlotQuery(NotQuery(fq1)), Grammar.parse(self.a, "* NOT (= 123)", start="slot_query"))
#         self.assertEqual(SlotQuery(ExactQuery([fq1, fq2])), Grammar.parse(self.a, "* EXACTLY (= 123 AND = 456)", start="slot_query"))
#         self.assertEqual(SlotQuery(ExactQuery([fq1, fq2])), Grammar.parse(self.a, "* exactly (= 123 AND = 456)", start="slot_query"))
#         self.assertEqual(SlotQuery(AndQuery([nq, ExactQuery([fq1, fq2])])), Grammar.parse(self.a, "THEME EXACTLY (= 123 AND = 456)", start="slot_query"))
#
#     @DeprecationWarning
#     def test_parse_frame_query(self):
#         iq = IdentifierQuery("@WM.HUMAN.1", IdentifierQuery.Comparator.EQUALS)
#         sq1 = SlotQuery( AndQuery([NameQuery("THEME"), FillerQuery(LiteralQuery(123))]))
#         sq2 = SlotQuery(AndQuery([NameQuery("THEME"), FillerQuery(LiteralQuery(456))]))
#
#         self.assertEqual(FrameQuery(sq1), Grammar.parse(self.a, "WHERE THEME = 123", start="frame_query"))
#         self.assertEqual(FrameQuery(sq1), Grammar.parse(self.a, "where THEME = 123", start="frame_query"))
#         self.assertEqual(FrameQuery(sq1), Grammar.parse(self.a, "SHOW FRAMES WHERE THEME = 123", start="frame_query"))
#         self.assertEqual(FrameQuery(sq1), Grammar.parse(self.a, "show frames where THEME = 123", start="frame_query"))
#         self.assertEqual(FrameQuery(sq1), Grammar.parse(self.a, "WHERE (THEME = 123)", start="frame_query"))
#         self.assertEqual(FrameQuery(AndQuery([sq1, sq2])), Grammar.parse(self.a, "WHERE (THEME = 123 AND THEME = 456)", start="frame_query"))
#         self.assertEqual(FrameQuery(AndQuery([sq1, sq2])), Grammar.parse(self.a, "WHERE (THEME = 123 and THEME = 456)", start="frame_query"))
#         self.assertEqual(FrameQuery(OrQuery([sq1, sq2])), Grammar.parse(self.a, "WHERE (THEME = 123 OR THEME = 456)", start="frame_query"))
#         self.assertEqual(FrameQuery(OrQuery([sq1, sq2])), Grammar.parse(self.a, "WHERE (THEME = 123 or THEME = 456)", start="frame_query"))
#         self.assertEqual(FrameQuery(NotQuery(sq1)), Grammar.parse(self.a, "WHERE NOT THEME = 123", start="frame_query"))
#         self.assertEqual(FrameQuery(NotQuery(sq1)), Grammar.parse(self.a, "WHERE not THEME = 123", start="frame_query"))
#         self.assertEqual(FrameQuery(NotQuery(sq1)), Grammar.parse(self.a, "WHERE NOT (THEME = 123)", start="frame_query"))
#         self.assertEqual(FrameQuery(ExactQuery([sq1, sq2])), Grammar.parse(self.a, "WHERE EXACTLY (THEME = 123 AND THEME = 456)", start="frame_query"))
#         self.assertEqual(FrameQuery(ExactQuery([sq1, sq2])), Grammar.parse(self.a, "WHERE exactly (THEME = 123 AND THEME = 456)", start="frame_query"))
#         self.assertEqual(FrameQuery(iq), Grammar.parse(self.a, "WHERE @ =@WM.HUMAN.1", start="frame_query"))
#         self.assertEqual(FrameQuery(AndQuery([iq, sq1])), Grammar.parse(self.a, "WHERE (@ =@WM.HUMAN.1 AND THEME = 123)", start="frame_query"))
#         self.assertEqual(FrameQuery(OrQuery([iq, sq1])), Grammar.parse(self.a, "WHERE (@ =@WM.HUMAN.1 OR THEME = 123)", start="frame_query"))
#         self.assertEqual(FrameQuery(NotQuery(iq)), Grammar.parse(self.a, "WHERE NOT (@ =@WM.HUMAN.1)", start="frame_query"))
#         self.assertEqual(FrameQuery(NotQuery(iq)), Grammar.parse(self.a, "WHERE NOT @ =@WM.HUMAN.1", start="frame_query"))
#         self.assertEqual(FrameQuery(IdentifierQuery("@ONT.EVENT", IdentifierQuery.Comparator.ISA)), Grammar.parse(self.a, "WHERE @^@ONT.EVENT", start="frame_query"))
#
#     @DeprecationWarning
#     def test_parse_view_graph(self):
#         self.assertEqual(View(self.a, Space("TEST")), Grammar.parse(self.a, "VIEW TEST SHOW ALL"))
#         self.assertEqual(View(self.a, Space("TEST")), Grammar.parse(self.a, "view TEST show all"))
#         self.assertEqual(View(self.a, Space("TMR#123")), Grammar.parse(self.a, "view TMR#123 show all"))
#
#     @DeprecationWarning
#     def test_parse_view_graph_with_query(self):
#         query = FrameQuery(IdentifierQuery("@TEST.FRAME.1", IdentifierQuery.Comparator.EQUALS))
#         self.assertEqual(View(self.a, Space("TEST"), query=query), Grammar.parse(self.a, "VIEW TEST SHOW FRAMES WHERE @=@TEST.FRAME.1"))
#         self.assertEqual(View(self.a, Space("TEST"), query=query), Grammar.parse(self.a, "view TEST show frames where @=@TEST.FRAME.1"))
#
#     @DeprecationWarning
#     def test_parse_follow(self):
#         self.assertEqual(Path().to("REL"), Grammar.parse(self.a, "[REL]->", start="path"))
#         self.assertEqual(Path().to("*"), Grammar.parse(self.a, "[*]->", start="path"))
#         self.assertEqual(Path().to("REL1").to("REL2"), Grammar.parse(self.a, "[REL1]->[REL2]->", start="path"))
#         self.assertEqual(Path().to("REL1").to("REL2"), Grammar.parse(self.a, "[REL1]-> [REL2]->", start="path"))
#         self.assertEqual(Path().to("REL1").to("REL2"), Grammar.parse(self.a, "[REL1]-> THEN [REL2]->", start="path"))
#         self.assertEqual(Path().to("REL", recursive=True), Grammar.parse(self.a, "[REL*]->", start="path"))
#         self.assertEqual(Path().to("REL", recursive=True), Grammar.parse(self.a, "[REL *]->", start="path"))
#         self.assertEqual(Path().to("REL", comparator=FrameQuery(IdentifierQuery("@TEST.FRAME.1", IdentifierQuery.Comparator.EQUALS))), Grammar.parse(self.a, "[REL]->TO @ = @TEST.FRAME.1", start="path"))
#         self.assertEqual(Path().to("REL", comparator=FrameQuery(IdentifierQuery("@TEST.FRAME.1", IdentifierQuery.Comparator.EQUALS))), Grammar.parse(self.a, "[REL]-> TO @ = @TEST.FRAME.1", start="path"))
#         self.assertEqual(Path().to("REL", comparator=FrameQuery(IdentifierQuery("@TEST.FRAME.1", IdentifierQuery.Comparator.EQUALS))).to("OTHER"), Grammar.parse(self.a, "[REL]-> TO @ = @TEST.FRAME.1 [OTHER]->", start="path"))
#         self.assertEqual(Path().to("REL", comparator=FrameQuery(IdentifierQuery("@TEST.FRAME.1", IdentifierQuery.Comparator.EQUALS))).to("OTHER"), Grammar.parse(self.a, "[REL]-> TO @ = @TEST.FRAME.1 THEN [OTHER]->", start="path"))
#
#     @DeprecationWarning
#     def test_parse_view_graph_with_path(self):
#         self.assertEqual(View(self.a, Space("TEST"), follow=Path().to("REL")), Grammar.parse(self.a, "VIEW TEST SHOW ALL FOLLOW [REL]->"))
#         self.assertEqual(View(self.a, Space("TEST"), follow=Path().to("REL").to("OTHER")), Grammar.parse(self.a, "view TEST SHOW ALL FOLLOW [REL]->[OTHER]->"))
#         self.assertEqual(View(self.a, Space("TEST"), follow=[Path().to("REL1"), Path().to("REL2")]), Grammar.parse(self.a, "view TEST SHOW ALL FOLLOW [REL1]-> AND FOLLOW [REL2]->"))
#
#
# @DeprecationWarning
# class AgendaGrammarTestCase(unittest.TestCase):
#
#     class TestAgent(Agent):
#         def __init__(self, g, agent):
#
#             self.exe = g
#             self.internal = g
#             self.ontology = g
#             self.wo_memory = g
#             self.lt_memory = g
#             self.identity = agent
#
#     def setUp(self):
#         graph.reset()
#         self.agentFrame = Frame("@SELF.AGENT")
#
#         self.agent = AgendaGrammarTestCase.TestAgent(Space("SELF"), self.agentFrame)
#
#     @DeprecationWarning
#     def test_statement_instance(self):
#         space = Space("SELF")
#         concept = Frame("@SELF.MYCONCEPT")
#         instance = Frame("@SELF.FRAME.?")
#
#         # SELF refers to the agent's identity
#         self.assertEqual(self.agentFrame, Grammar.parse(self.agent, "SELF", start="statement_instance"))
#
#         # An instance can be created on a specified graph (by name); here "SELF" is the graph name, and SELF.MYCONCEPT is an identifier to make an instance of
#         self.assertEqual(MakeInstanceStatement.instance(space, "SELF", concept, []), Grammar.parse(self.agent, "@SELF:@SELF.MYCONCEPT()", start="statement_instance"))
#
#         # Graph names don't need to be known; a few have unique identifiers, but must be followed by the "!" to be
#         # registered as such;  AGENT.INTERNAL, AGENT.EXE, AGENT.ONTOLOGY, AGENT.WM, and AGENT.LT are valid
#         self.assertEqual(MakeInstanceStatement.instance(space, "SELF", concept, []), Grammar.parse(self.agent, "@AGENT.INTERNAL!:@SELF.MYCONCEPT()", start="statement_instance"))
#
#         # If a fully qualified identifier is not provided, the agent's SELF graph will be assumed
#         # self.assertEqual(MakeInstanceStatement.instance(space, "SELF", concept, []), Grammar.parse(self.agent, "@SELF:@MYCONCEPT()", start="statement_instance"))
#
#         # New instances can include arguments
#         self.assertEqual(MakeInstanceStatement.instance(space, "SELF", concept, ["$arg1", "$arg2"]), Grammar.parse(self.agent, "@SELF:@SELF.MYCONCEPT($arg1, $arg2)", start="statement_instance"))
#
#         # A simple identifier is also a valid statement instance
#         self.assertEqual(instance, Grammar.parse(self.agent, "@SELF.FRAME.1", start="statement_instance"))
#
#         # Any variable can also be used
#         self.assertEqual("$var1", Grammar.parse(self.agent, "$var1", start="statement_instance"))
#
#     @DeprecationWarning
#     def test_is_statement(self):
#         f = Frame("@SELF.FRAME")
#
#         self.assertEqual(IsStatement.instance(Space("SELF"), f, "SLOT", 123), Grammar.parse(self.agent, "@SELF.FRAME[SLOT] == 123", start="is_statement"))
#
#     @DeprecationWarning
#     def test_make_instance_statement(self):
#         space = Space("SELF")
#         concept = Frame("@SELF.MYCONCEPT")
#         self.assertEqual(MakeInstanceStatement.instance(space, space.name, concept, []), Grammar.parse(self.agent, "@SELF:@SELF.MYCONCEPT()", start="make_instance_statement"))
#         self.assertEqual(MakeInstanceStatement.instance(space, space.name, concept, []), Grammar.parse(self.agent, "@AGENT.INTERNAL!:@SELF.MYCONCEPT()", start="make_instance_statement"))
#         self.assertEqual(MakeInstanceStatement.instance(space, space.name, concept, ["$arg1", "$arg2"]), Grammar.parse(self.agent, "@SELF:@SELF.MYCONCEPT($arg1, $arg2)", start="make_instance_statement"))
#
#     @DeprecationWarning
#     def test_add_filler_statement(self):
#         space = Space("SELF")
#         f = Frame("@SELF.FRAME")
#
#         statement = AddFillerStatement.instance(space, self.agentFrame, "SLOT", 123)
#         parsed = Grammar.parse(self.agent, "SELF[SLOT] += 123", start="add_filler_statement")
#         self.assertEqual(statement, parsed)
#
#         statement = AddFillerStatement.instance(space, self.agentFrame, "SLOT", f)
#         parsed = Grammar.parse(self.agent, "SELF[SLOT] += @SELF.FRAME", start="add_filler_statement")
#         self.assertEqual(statement, parsed)
#
#         statement = AddFillerStatement.instance(space, f, "SLOT", 123)
#         parsed = Grammar.parse(self.agent, "@SELF.FRAME[SLOT] += 123", start="add_filler_statement")
#         self.assertEqual(statement, parsed)
#
#     @DeprecationWarning
#     def test_assert_statement(self):
#         Bootstrap.bootstrap_resource(None, "backend.resources", "exe.knowledge")
#
#         space = Space("SELF")
#         f = Frame("@SELF.FRAME")
#
#         resolution1 = MakeInstanceStatement.instance(space, "TEST", "@TEST.MYGOAL", [])
#         resolution2 = MakeInstanceStatement.instance(space, "TEST", "@TEST.MYGOAL", ["$var1", "$var2"])
#
#         statement = AssertStatement.instance(space, ExistsStatement.instance(space, SlotQuery(NameQuery("XYZ"))), [resolution1])
#         parsed = Grammar.parse(self.agent, "ASSERT EXISTS HAS XYZ ELSE IMPASSE WITH @TEST:@TEST.MYGOAL()", start="assert_statement")
#         self.assertEqual(statement, parsed)
#
#         statement = AssertStatement.instance(space, IsStatement.instance(space, f, "SLOT", 123), [resolution1])
#         parsed = Grammar.parse(self.agent, "ASSERT @SELF.FRAME[SLOT] == 123 ELSE IMPASSE WITH @TEST:@TEST.MYGOAL()", start="assert_statement")
#         self.assertEqual(statement, parsed)
#
#         statement = AssertStatement.instance(space, MeaningProcedureStatement.instance(space, "some_mp", ["$var1"]), [resolution1])
#         parsed = Grammar.parse(self.agent, "ASSERT SELF.some_mp($var1) ELSE IMPASSE WITH @TEST:@TEST.MYGOAL()", start="assert_statement")
#         self.assertEqual(statement, parsed)
#
#         statement = AssertStatement.instance(space, ExistsStatement.instance(space, SlotQuery(NameQuery("XYZ"))), [resolution1, resolution2])
#         parsed = Grammar.parse(self.agent, "ASSERT EXISTS HAS XYZ ELSE IMPASSE WITH @TEST:@TEST.MYGOAL() OR @TEST:@TEST.MYGOAL($var1, $var2)", start="assert_statement")
#         self.assertEqual(statement, parsed)
#
#     @DeprecationWarning
#     def test_assign_filler_statement(self):
#         space = Space("SELF")
#         f = Frame("@SELF.FRAME")
#
#         statement = AssignFillerStatement.instance(space, self.agentFrame, "SLOT", 123)
#         parsed = Grammar.parse(self.agent, "SELF[SLOT] = 123", start="assign_filler_statement")
#         self.assertEqual(statement, parsed)
#
#         statement = AssignFillerStatement.instance(space, self.agentFrame, "SLOT", f)
#         parsed = Grammar.parse(self.agent, "SELF[SLOT] = @SELF.FRAME", start="assign_filler_statement")
#         self.assertEqual(statement, parsed)
#
#         statement = AssignFillerStatement.instance(space, f, "SLOT", 123)
#         parsed = Grammar.parse(self.agent, "@SELF.FRAME[SLOT] = 123", start="assign_filler_statement")
#         self.assertEqual(statement, parsed)
#
#     @DeprecationWarning
#     def test_assign_variable_statement(self):
#         from backend.models.bootstrap import BootstrapTriple
#
#         space = Space("SELF")
#         f = Frame("@SELF.FRAME")
#
#         statement = AssignVariableStatement.instance(space, "$var1", 123)
#         parsed = Grammar.parse(self.agent, "$var1 = 123", start="assign_variable_statement")
#         self.assertEqual(statement, parsed)
#
#         statement = AssignVariableStatement.instance(space, "$var1", "test")
#         parsed = Grammar.parse(self.agent, "$var1 = \"test\"", start="assign_variable_statement")
#         self.assertEqual(statement, parsed)
#
#         statement = AssignVariableStatement.instance(space, "$var1", f)
#         parsed = Grammar.parse(self.agent, "$var1 = @SELF.FRAME", start="assign_variable_statement")
#         self.assertEqual(statement, parsed)
#
#         statement = AssignVariableStatement.instance(space, "$var1", "$var2")
#         parsed = Grammar.parse(self.agent, "$var1 = $var2", start="assign_variable_statement")
#         self.assertEqual(statement, parsed)
#
#         statement = AssignVariableStatement.instance(space, "$var1", MeaningProcedureStatement.instance(space, "TestMP", []))
#         parsed = Grammar.parse(self.agent, "$var1 = SELF.TestMP()", start="assign_variable_statement")
#         self.assertEqual(statement, parsed)
#
#         statement = AssignVariableStatement.instance(space, "$var1", ExistsStatement.instance(space, IdentifierQuery("@EXE.TEST.1", IdentifierQuery.Comparator.EQUALS)))
#         parsed = Grammar.parse(self.agent, "$var1 = EXISTS @ = @EXE.TEST.1", start="assign_variable_statement")
#         self.assertEqual(statement, parsed)
#
#         statement = AssignVariableStatement.instance(space, "$var1", [[123, "test", "$var2", MeaningProcedureStatement.instance(space, "TestMP", [])]])
#         parsed = Grammar.parse(self.agent, "$var1 = [123, \"test\", $var2, SELF.TestMP()]", start="assign_variable_statement")
#         self.assertIsInstance(parsed.frame["ASSIGN"][0], list)
#         self.assertEqual(statement, parsed)
#
#         statement = AssignVariableStatement.instance(space, "$var1", [[]])
#         parsed = Grammar.parse(self.agent, "$var1 = []", start="assign_variable_statement")
#         self.assertIsInstance(parsed.frame["ASSIGN"][0], list)
#         self.assertEqual(statement, parsed)
#
#         statement = AssignVariableStatement.instance(space, "$var1", TransientFrameStatement.instance(space, [BootstrapTriple("SLOT", 123)]))
#         parsed = Grammar.parse(self.agent, "$var1 = {SLOT 123;}", start="assign_variable_statement")
#         self.assertEqual(statement, parsed)
#
#     @DeprecationWarning
#     def test_exists_statement(self):
#         statement = ExistsStatement.instance(Space("SELF"), SlotQuery(AndQuery([NameQuery("THEME"), FillerQuery(LiteralQuery(123))])))
#         parsed = Grammar.parse(self.agent, "EXISTS THEME = 123", start="exists_statement")
#         self.assertEqual(statement, parsed)
#
#     @DeprecationWarning
#     def test_expectation_statement(self):
#         space = Space("SELF")
#         Bootstrap.bootstrap_resource(None, "backend.resources", "exe.knowledge")
#
#         statement = ExpectationStatement.instance(space, ExistsStatement.instance(space, SlotQuery(NameQuery("XYZ"))))
#         parsed = Grammar.parse(self.agent, "EXPECT EXISTS HAS XYZ", start="expectation_statement")
#         self.assertEqual(statement, parsed)
#
#         statement = ExpectationStatement.instance(space, MeaningProcedureStatement.instance(space, "test_mp", ["$var1"]))
#         parsed = Grammar.parse(self.agent, "EXPECT SELF.test_mp($var1)", start="expectation_statement")
#         self.assertEqual(statement, parsed)
#
#         statement = ExpectationStatement.instance(space, IsStatement.instance(space, Identifier("@SELF.FRAME.1"), "SLOT", 123))
#         parsed = Grammar.parse(self.agent, "EXPECT @SELF.FRAME.1[SLOT] == 123", start="expectation_statement")
#         self.assertEqual(statement, parsed)
#
#     @DeprecationWarning
#     def test_foreach_statement(self):
#         space = Space("SELF")
#         Bootstrap.bootstrap_resource(None, "backend.resources", "exe.knowledge")
#
#         query = SlotQuery(AndQuery([NameQuery("THEME"), FillerQuery(LiteralQuery(123))]))
#         statement = ForEachStatement.instance(space, query, "$var", AddFillerStatement.instance(space, "$var", "SLOT", 456))
#         parsed = Grammar.parse(self.agent, "FOR EACH $var IN THEME = 123 | $var[SLOT] += 456", start="foreach_statement")
#         self.assertEqual(statement, parsed)
#
#         query = SlotQuery(AndQuery([NameQuery("THEME"), FillerQuery(LiteralQuery(123))]))
#         statement = ForEachStatement.instance(space, query, "$var", [AddFillerStatement.instance(space, "$var", "SLOT", 456), AddFillerStatement.instance(space, "$var", "SLOT", 456)])
#         parsed = Grammar.parse(self.agent, "FOR EACH $var IN THEME = 123 | $var[SLOT] += 456 | $var[SLOT] += 456", start="foreach_statement")
#         self.assertEqual(statement, parsed)
#
#     @DeprecationWarning
#     def test_mp_statement(self):
#         space = Space("SELF")
#
#         statement = MeaningProcedureStatement.instance(space, "mp1", [])
#         parsed = Grammar.parse(self.agent, "SELF.mp1()", start="mp_statement")
#         self.assertEqual(statement, parsed)
#
#         statement = MeaningProcedureStatement.instance(space, "mp1", ["$var1", "$var2"])
#         parsed = Grammar.parse(self.agent, "SELF.mp1($var1, $var2)", start="mp_statement")
#         self.assertEqual(statement, parsed)
#
#         statement = MeaningProcedureStatement.instance(space, "mp1", [123, Identifier("@SELF.TEST")])
#         parsed = Grammar.parse(self.agent, "SELF.mp1(123, @SELF.TEST)", start="mp_statement")
#         self.assertEqual(statement, parsed)
#
#     @DeprecationWarning
#     def test_output_statement(self):
#         template = OutputXMRTemplate.build("test-xmr", XMR.Type.ACTION, "@SELF.TEST-CAPABILITY", ["$var1", "$var2", "$var3", "$var4"])
#
#         statement = OutputXMRStatement.instance(self.agent.exe, template, [1, "abc", "$var1", Identifier("@SELF.TEST")], self.agent.identity)
#         parsed = Grammar.parse(self.agent, "OUTPUT test-xmr(1, \"abc\", $var1, @SELF.TEST) BY SELF", start="output_statement")
#         self.assertEqual(statement, parsed)
#
#     @DeprecationWarning
#     def test_transientframe_statement(self):
#         from backend.models.bootstrap import BootstrapTriple
#
#         property1 = BootstrapTriple("SLOTA", 123)
#         property2 = BootstrapTriple("SLOTA", 456)
#         property3 = BootstrapTriple("SLOTB", "abc")
#         property4 = BootstrapTriple("SLOTC", "$var1")
#         property5 = BootstrapTriple("SLOTD", Identifier("@TEST.FRAME.1"))
#
#         statement = TransientFrameStatement.instance(self.agent.exe, [property1])
#         parsed = Grammar.parse(self.agent, "{SLOTA 123;}", start="transient_statement")
#         self.assertEqual(statement, parsed)
#
#         statement = TransientFrameStatement.instance(self.agent.exe, [property1, property2])
#         parsed = Grammar.parse(self.agent, "{SLOTA 123; SLOTA 456;}", start="transient_statement")
#         self.assertEqual(statement, parsed)
#
#         statement = TransientFrameStatement.instance(self.agent.exe, [property3, property4, property5])
#         parsed = Grammar.parse(self.agent, "{SLOTB \"abc\"; SLOTC $var1; SLOTD @TEST.FRAME.1;}", start="transient_statement")
#         self.assertEqual(statement, parsed)
#
#     @DeprecationWarning
#     def test_plan(self):
#         space = Space("SELF")
#         Bootstrap.bootstrap_resource(None, "backend.resources", "exe.knowledge")
#
#         plan = Plan.build(space, "testplan", Plan.DEFAULT, Step.build(space, 1, Step.IDLE))
#         parsed = Grammar.parse(self.agent, "PLAN (testplan) SELECT DEFAULT STEP DO IDLE", start="plan")
#         self.assertEqual(plan, parsed)
#
#         query = SlotQuery(AndQuery([NameQuery("THEME"), FillerQuery(LiteralQuery(123))]))
#         plan = Plan.build(space, "testplan", ExistsStatement.instance(space, query), Step.build(space, 1, Step.IDLE))
#         parsed = Grammar.parse(self.agent, "PLAN (testplan) SELECT IF EXISTS THEME = 123 STEP DO IDLE", start="plan")
#         self.assertEqual(plan, parsed)
#
#         statement = MeaningProcedureStatement.instance(space, "mp1", ["$var1"])
#         plan = Plan.build(space, "testplan", statement, Step.build(space, 1, Step.IDLE))
#         parsed = Grammar.parse(self.agent, "PLAN (testplan) SELECT IF SELF.mp1($var1) STEP DO IDLE", start="plan")
#         self.assertEqual(plan, parsed)
#
#         statement = MeaningProcedureStatement.instance(space, "mp1", ["$var1"])
#         plan = Plan.build(space, "testplan", statement, Step.build(space, 1, Step.IDLE), negate=True)
#         parsed = Grammar.parse(self.agent, "PLAN (testplan) SELECT IF NOT SELF.mp1($var1) STEP DO IDLE", start="plan")
#         self.assertEqual(plan, parsed)
#
#         statement = MeaningProcedureStatement.instance(space, "mp1", [])
#         plan = Plan.build(space, "testplan", Plan.DEFAULT, Step.build(space, 1, [statement, statement]))
#         parsed = Grammar.parse(self.agent, "PLAN (testplan) SELECT DEFAULT STEP DO SELF.mp1() DO SELF.mp1()", start="plan")
#         self.assertEqual(plan, parsed)
#
#         statement = MeaningProcedureStatement.instance(space, "mp1", [])
#         plan = Plan.build(space, "testplan", Plan.DEFAULT, [Step.build(space, 1, [statement]), Step.build(space, 2, [statement])])
#         parsed = Grammar.parse(self.agent, "PLAN (testplan) SELECT DEFAULT STEP DO SELF.mp1() STEP DO SELF.mp1()", start="plan")
#         self.assertEqual(plan, parsed)
#
#     @DeprecationWarning
#     def test_condition(self):
#         space = Space("SELF")
#         Bootstrap.bootstrap_resource(None, "backend.resources", "exe.knowledge")
#
#         query = SlotQuery(AndQuery([NameQuery("THEME"), FillerQuery(LiteralQuery(123))]))
#
#         condition = Condition.build(space, [ExistsStatement.instance(space, query)], Goal.Status.SATISFIED, logic=Condition.Logic.AND, order=1)
#         parsed = Grammar.parse(self.agent, "WHEN EXISTS THEME = 123 THEN satisfied", start="condition")
#         self.assertEqual(condition, parsed)
#
#         condition = Condition.build(space, [ExistsStatement.instance(space, query), ExistsStatement.instance(space, query)], Goal.Status.SATISFIED, logic=Condition.Logic.AND, order=1)
#         parsed = Grammar.parse(self.agent, "WHEN EXISTS THEME = 123 AND EXISTS THEME = 123 THEN satisfied", start="condition")
#         self.assertEqual(condition, parsed)
#
#         condition = Condition.build(space, [ExistsStatement.instance(space, query), ExistsStatement.instance(space, query)], Goal.Status.SATISFIED, logic=Condition.Logic.OR, order=1)
#         parsed = Grammar.parse(self.agent, "WHEN EXISTS THEME = 123 OR EXISTS THEME = 123 THEN satisfied", start="condition")
#         self.assertEqual(condition, parsed)
#
#         condition = Condition.build(space, [], Goal.Status.SATISFIED, on=Condition.On.EXECUTED)
#         parsed = Grammar.parse(self.agent, "WHEN EXECUTED THEN satisfied", start="condition")
#         self.assertEqual(condition, parsed)
#
#     @DeprecationWarning
#     def test_define_goal(self):
#         space = Space("SELF")
#         Bootstrap.bootstrap_resource(None, "backend.resources", "exe.knowledge")
#
#         # A goal has a name and a destination graph, and a default priority
#         goal: Goal = Grammar.parse(self.agent, "DEFINE XYZ() AS GOAL IN SELF", start="define").goal
#         self.assertTrue(goal.frame in space)
#         self.assertEqual(goal.name(), "XYZ")
#         self.assertEqual(goal.priority(), 0.5)
#
#         # A goal can be overwritten
#         goal: Goal = Grammar.parse(self.agent, "DEFINE XYZ() AS GOAL IN SELF", start="define").goal
#         self.assertTrue(goal.frame in space)
#         self.assertEqual(goal.name(), "XYZ")
#         self.assertEqual(2, len(space)) # One is the agent, the other is the overwritten goal
#
#         # A goal can have parameters
#         goal: Goal = Goal.define(space, "XYZ", 0.5, 0.5, [], [], ["$var1", "$var2"], [])
#         parsed: Goal = Grammar.parse(self.agent, "DEFINE XYZ($var1, $var2) AS GOAL IN SELF", start="define").goal
#         self.assertEqual(goal, parsed)
#
#         # A goal can have a numeric priority
#         goal: Goal = Goal.define(space, "XYZ", 0.9, 0.5, [], [], [], [])
#         parsed: Goal = Grammar.parse(self.agent, "DEFINE XYZ() AS GOAL IN SELF PRIORITY 0.9", start="define").goal
#         self.assertEqual(goal, parsed)
#
#         # A goal can have a statement priority
#         goal: Goal = Goal.define(space, "XYZ", MeaningProcedureStatement.instance(space, "mp1", []).frame, 0.5, [], [], [], [])
#         parsed: Goal = Grammar.parse(self.agent, "DEFINE XYZ() AS GOAL IN SELF PRIORITY SELF.mp1()", start="define").goal
#         self.assertEqual(goal.frame["PRIORITY"].singleton()["CALLS"].singleton(), parsed.frame["PRIORITY"].singleton()["CALLS"].singleton())
#
#         # A goal can have a numeric resources
#         goal: Goal = Goal.define(space, "XYZ", 0.5, 0.9, [], [], [], [])
#         parsed: Goal = Grammar.parse(self.agent, "DEFINE XYZ() AS GOAL IN SELF RESOURCES 0.9", start="define").goal
#         self.assertEqual(goal, parsed)
#
#         # A goal can have a statement resources
#         goal: Goal = Goal.define(space, "XYZ", 0.5, MeaningProcedureStatement.instance(space, "mp1", []).frame, [], [], [], [])
#         parsed: Goal = Grammar.parse(self.agent, "DEFINE XYZ() AS GOAL IN SELF RESOURCES SELF.mp1()", start="define").goal
#         self.assertEqual(goal.frame["RESOURCES"].singleton()["CALLS"].singleton(), parsed.frame["RESOURCES"].singleton()["CALLS"].singleton())
#
#         # A goal can have plans (plans)
#         a1: Plan = Plan.build(space, "plan_a", Plan.DEFAULT, Step.build(space, 1, Step.IDLE))
#         a2: Plan = Plan.build(space, "plan_b", Plan.DEFAULT, Step.build(space, 1, Step.IDLE))
#         goal: Goal = Goal.define(space, "XYZ", 0.5, 0.5, [a1, a2], [], [], [])
#         parsed: Goal = Grammar.parse(self.agent, "DEFINE XYZ() AS GOAL IN SELF PLAN (plan_a) SELECT DEFAULT STEP DO IDLE PLAN (plan_b) SELECT DEFAULT STEP DO IDLE", start="define").goal
#         self.assertEqual(goal, parsed)
#
#         # A goal can have conditions (which are ordered as written)
#         q1 = SlotQuery(AndQuery([NameQuery("THEME"), FillerQuery(LiteralQuery(123))]))
#         q2 = SlotQuery(AndQuery([NameQuery("THEME"), FillerQuery(LiteralQuery(456))]))
#         c1: Condition = Condition.build(space, [ExistsStatement.instance(space, q1)], Goal.Status.SATISFIED, Condition.Logic.AND, 1)
#         c2: Condition = Condition.build(space, [ExistsStatement.instance(space, q2)], Goal.Status.ABANDONED, Condition.Logic.AND, 2)
#         goal: Goal = Goal.define(space, "XYZ", 0.5, 0.5, [], [c1, c2], [], [])
#         parsed: Goal = Grammar.parse(self.agent, "DEFINE XYZ() AS GOAL IN SELF WHEN EXISTS THEME = 123 THEN satisfied WHEN EXISTS THEME = 456 THEN abandoned", start="define").goal
#         self.assertEqual(goal, parsed)
#
#         # A goal can have effects
#         e1: Effect = Effect.build(space, [AddFillerStatement.instance(space, "TEST.FRAME.1", "SLOT", 123)])
#         e2: Effect = Effect.build(space, [AddFillerStatement.instance(space, "TEST.FRAME.1", "SLOT", 456)])
#         goal: Goal = Goal.define(space, "XYZ", 0.5, 0.5, [], [], [], [e1, e2])
#         parsed: Goal = Grammar.parse(self.agent, "DEFINE XYZ() AS GOAL IN SELF EFFECT DO @TEST.FRAME.1[SLOT] = 123 DO @TEST.FRAME.1[SLOT] = $var1", start="define").goal
#         self.assertEqual(goal, parsed)
#
#     @DeprecationWarning
#     def test_find_something_to_do(self):
#         space = Space("SELF")
#         Bootstrap.bootstrap_resource(None, "backend.resources", "exe.knowledge")
#
#         goal1 = Goal.define(space, "FIND-SOMETHING-TO-DO", 0.1, 0.5, [
#             Plan.build(space,
#                          "acknowledge input",
#                          ExistsStatement.instance(space, Grammar.parse(self.agent, "(@^ @SELF.INPUT-TMR AND ACKNOWLEDGED = False)", start="logical_slot_query")),
#                          Step.build(space, 1,
#                                     ForEachStatement.instance(
#                                         space,
#                                         Grammar.parse(self.agent, "(@^ @SELF.INPUT-TMR AND ACKNOWLEDGED = False)", start="logical_slot_query"),
#                                         "$tmr",
#                                         [
#                                             AddFillerStatement.instance(space, self.agent.identity, "HAS-GOAL",
#                                                                         MakeInstanceStatement.instance(space, "SELF", "SELF.UNDERSTAND-TMR", ["$tmr"])),
#                                            AssignFillerStatement.instance(space, "$tmr", "ACKNOWLEDGED", True)
#                                         ])
#                          )),
#             Plan.build(space, "idle", Plan.DEFAULT, [Step.build(space, 1, Step.IDLE), Step.build(space, 2, Step.IDLE)])
#         ], [], [], [])
#
#         script = '''
#         DEFINE FIND-SOMETHING-TO-DO()
#             AS GOAL
#             IN SELF
#             PRIORITY 0.1
#             PLAN (acknowledge input)
#                 SELECT IF EXISTS (@^ @SELF.INPUT-TMR AND ACKNOWLEDGED = FALSE)
#                 STEP
#                     DO FOR EACH $tmr IN (@^ @SELF.INPUT-TMR AND ACKNOWLEDGED = FALSE)
#                     | SELF[HAS-GOAL] += @SELF:@SELF.UNDERSTAND-TMR($tmr)
#                     | $tmr[ACKNOWLEDGED] = True
#             PLAN (idle)
#                 SELECT DEFAULT
#                 STEP
#                     DO IDLE
#                 STEP
#                     DO IDLE
#         '''
#
#         parsed: Goal = Grammar.parse(self.agent, script, start="define").goal
#         self.assertEqual(goal1, parsed)
#
#
# @DeprecationWarning
# class BootstrapGrammarTestCase(unittest.TestCase):
#
#     def setUp(self):
#         graph.reset()
#         self.agentFrame = Frame("@SELF.AGENT")
#
#         self.agent = AgendaGrammarTestCase.TestAgent(Space("SELF"), self.agentFrame)
#
#     @DeprecationWarning
#     def test_bootstrap_comments(self):
#         input = '''
#         // A comment
#         @SELF.AGENT += {myslot 123}; // More comments
#         @SELF.AGENT += {myslot 123}; // More comments
#         @SELF.AGENT += {myslot 123};
#         '''
#
#         bootstrap = Grammar.parse(self.agent, input, start="bootstrap")
#         self.assertEqual(3, len(bootstrap))
#
#     @DeprecationWarning
#     def test_bootstrap_multiple(self):
#         from backend.models.bootstrap import Bootstrap
#
#         input = '''
#         @SELF.AGENT += {myslot 123};
#
#         @SELF.AGENT += {myslot 123}
#         ;
#
#
#         @SELF.AGENT += {myslot 123};
#         '''
#
#         bootstrap = Grammar.parse(self.agent, input, start="bootstrap")
#         self.assertEqual(3, len(bootstrap))
#         for b in bootstrap:
#             self.assertIsInstance(b, Bootstrap)
#
#     @DeprecationWarning
#     def test_declare_knowledge(self):
#         from backend.models.bootstrap import BootstrapDeclareKnowledge, BootstrapTriple
#
#         bootstrap = BootstrapDeclareKnowledge("MYGRAPH", "MYFRAME")
#         parsed = Grammar.parse(self.agent, "@MYGRAPH.MYFRAME = {}", start="declare_knowledge")
#         self.assertEqual(bootstrap, parsed)
#
#         bootstrap = BootstrapDeclareKnowledge("MYGRAPH", "MYFRAME", index=123)
#         parsed = Grammar.parse(self.agent, "@MYGRAPH.MYFRAME.123 = {}", start="declare_knowledge")
#         self.assertEqual(bootstrap, parsed)
#
#         bootstrap = BootstrapDeclareKnowledge("MYGRAPH", "MYFRAME", index=True)
#         parsed = Grammar.parse(self.agent, "@MYGRAPH.MYFRAME.? = {}", start="declare_knowledge")
#         self.assertEqual(bootstrap, parsed)
#
#         bootstrap = BootstrapDeclareKnowledge("MYGRAPH", "MYFRAME", isa="@ONT.ALL")
#         parsed = Grammar.parse(self.agent, "@MYGRAPH.MYFRAME = {ISA @ONT.ALL}", start="declare_knowledge")
#         self.assertEqual(bootstrap, parsed)
#
#         bootstrap = BootstrapDeclareKnowledge("MYGRAPH", "MYFRAME", isa=["@ONT.ALL", "@ONT.OTHER"])
#         parsed = Grammar.parse(self.agent, "@MYGRAPH.MYFRAME = {ISA @ONT.ALL; ISA @ONT.OTHER}", start="declare_knowledge")
#         self.assertEqual(bootstrap, parsed)
#
#         bootstrap = BootstrapDeclareKnowledge("MYGRAPH", "MYFRAME", properties=[BootstrapTriple("MYPROP", Identifier("@ONT.ALL"))])
#         parsed = Grammar.parse(self.agent, "@MYGRAPH.MYFRAME = {MYPROP @ONT.ALL}", start="declare_knowledge")
#         self.assertEqual(bootstrap, parsed)
#
#         bootstrap = BootstrapDeclareKnowledge("MYGRAPH", "MYFRAME", properties=[BootstrapTriple("MYPROP", Identifier("@ONT.ALL")), BootstrapTriple("OTHERPROP", "VALUE")])
#         parsed = Grammar.parse(self.agent, "@MYGRAPH.MYFRAME = {MYPROP @ONT.ALL; OTHERPROP \"VALUE\"}", start="declare_knowledge")
#         self.assertEqual(bootstrap, parsed)
#
#         bootstrap = BootstrapDeclareKnowledge("MYGRAPH", "MYFRAME", properties=[BootstrapTriple("MYPROP", Identifier("@ONT.ALL"), facet="SEM")])
#         parsed = Grammar.parse(self.agent, "@MYGRAPH.MYFRAME = {MYPROP SEM @ONT.ALL}", start="declare_knowledge")
#         self.assertEqual(bootstrap, parsed)
#
#     @DeprecationWarning
#     def test_append_knowledge(self):
#         from backend.models.bootstrap import BootstrapAppendKnowledge, BootstrapTriple
#
#         bootstrap = BootstrapAppendKnowledge("@SELF.FRAME", properties=[BootstrapTriple("MYPROP", Identifier("@ONT.ALL"))])
#         parsed = Grammar.parse(self.agent, "@SELF.FRAME += {MYPROP @ONT.ALL}", start="append_knowledge")
#         self.assertEqual(bootstrap, parsed)
#
#         bootstrap = BootstrapAppendKnowledge("@SELF.FRAME", properties=[BootstrapTriple("MYPROP", Identifier("@ONT.ALL")), BootstrapTriple("OTHERPROP", "VALUE")])
#         parsed = Grammar.parse(self.agent, "@SELF.FRAME += {MYPROP @ONT.ALL; OTHERPROP \"VALUE\"}", start="append_knowledge")
#         self.assertEqual(bootstrap, parsed)
#
#         bootstrap = BootstrapAppendKnowledge("@SELF.FRAME", properties=[BootstrapTriple("MYPROP", Identifier("@ONT.ALL"), facet="SEM")])
#         parsed = Grammar.parse(self.agent, "@SELF.FRAME += {MYPROP SEM @ONT.ALL}", start="append_knowledge")
#         self.assertEqual(bootstrap, parsed)
#
#     @DeprecationWarning
#     def test_register_mp(self):
#         from backend.models.bootstrap import BootstrapRegisterMP
#
#         bootstrap = BootstrapRegisterMP(TestAgentMethod)
#         parsed = Grammar.parse(self.agent, "REGISTER MP tests.models.GrammarTestCase.TestAgentMethod", start="register_mp")
#         self.assertEqual(bootstrap, parsed)
#
#         bootstrap = BootstrapRegisterMP(TestAgentMethod, name="TestMP")
#         parsed = Grammar.parse(self.agent, "REGISTER MP tests.models.GrammarTestCase.TestAgentMethod AS TestMP", start="register_mp")
#         self.assertEqual(bootstrap, parsed)
#
#     @DeprecationWarning
#     def test_add_trigger(self):
#         from backend.models.bootstrap import BootstrapAddTrigger
#
#         query = SlotQuery(AndQuery([NameQuery("THEME"), FillerQuery(LiteralQuery(123))]))
#
#         bootstrap = BootstrapAddTrigger("@SELF.AGENDA.1", "@EXE.MYGOAL.1", query)
#         parsed = Grammar.parse(self.agent, "ADD TRIGGER TO @SELF.AGENDA.1 INSTANTIATE @EXE.MYGOAL.1 WHEN THEME = 123", start="add_trigger")
#         self.assertEqual(bootstrap, parsed)
#
#
# @DeprecationWarning
# class OutputXMRTemplateGrammarTestCase(unittest.TestCase):
#
#     def setUp(self):
#         graph.reset()
#         self.agentFrame = Frame("@SELF.AGENT")
#
#         self.agent = AgendaGrammarTestCase.TestAgent(Space("SELF"), self.agentFrame)
#
#     @DeprecationWarning
#     def test_parse_type(self):
#         type = XMR.Type.ACTION
#         parsed = Grammar.parse(self.agent, "TYPE PHYSICAL", start="output_xmr_template_type")
#         self.assertEqual(type, parsed)
#
#         type = XMR.Type.MENTAL
#         parsed = Grammar.parse(self.agent, "TYPE MENTAL", start="output_xmr_template_type")
#         self.assertEqual(type, parsed)
#
#         type = XMR.Type.LANGUAGE
#         parsed = Grammar.parse(self.agent, "TYPE VERBAL", start="output_xmr_template_type")
#         self.assertEqual(type, parsed)
#
#     @DeprecationWarning
#     def test_parse_requires(self):
#         requires = Identifier("@EXE.TEST-CAPABILITY")
#         parsed = Grammar.parse(self.agent, "REQUIRES @EXE.TEST-CAPABILITY", start="output_xmr_template_requires")
#         self.assertEqual(requires, parsed)
#
#         requires = Identifier("@EXE.TEST-CAPABILITY.1")
#         parsed = Grammar.parse(self.agent, "REQUIRES @EXE.TEST-CAPABILITY.1", start="output_xmr_template_requires")
#         self.assertEqual(requires, parsed)
#
#     @DeprecationWarning
#     def test_parse_root(self):
#         requires = Identifier("@OUT.TEST-ROOT")
#         parsed = Grammar.parse(self.agent, "ROOT @OUT.TEST-ROOT", start="output_xmr_template_root")
#         self.assertEqual(requires, parsed)
#
#         requires = Identifier("@OUT.TEST-ROOT.1")
#         parsed = Grammar.parse(self.agent, "ROOT @OUT.TEST-ROOT.1", start="output_xmr_template_root")
#         self.assertEqual(requires, parsed)
#
#     @DeprecationWarning
#     def test_parse_include(self):
#         from backend.models.bootstrap import BootstrapDeclareKnowledge, BootstrapTriple
#
#         property1 = BootstrapTriple("MYPROP", Identifier("@ONT.ALL"))
#         property2 = BootstrapTriple("OTHERPROP", "$var1")
#         property3 = BootstrapTriple("AGENT", self.agent.identity.id)
#
#         include = [BootstrapDeclareKnowledge("OUT", "MYFRAME", index=1, properties=[property1, property2])]
#         parsed = Grammar.parse(self.agent, "INCLUDE @OUT.MYFRAME.1 = {MYPROP @ONT.ALL; OTHERPROP \"$var1\"}", start="output_xmr_template_include")
#         self.assertEqual(include, parsed)
#
#         include = [BootstrapDeclareKnowledge("OUT", "MYFRAME", index=1), BootstrapDeclareKnowledge("OUT", "MYFRAME", index=2)]
#         parsed = Grammar.parse(self.agent, "INCLUDE @OUT.MYFRAME.1 = {} @OUT.MYFRAME.2 = {}", start="output_xmr_template_include")
#         self.assertEqual(include, parsed)
#
#         include = [BootstrapDeclareKnowledge("OUT", "MYFRAME", index=1, properties=[property3])]
#         parsed = Grammar.parse(self.agent, "INCLUDE @OUT.MYFRAME.1 = {AGENT @SELF}", start="output_xmr_template_include")
#         self.assertEqual(include, parsed)
#
#     @DeprecationWarning
#     def test_parse_template(self):
#         from backend.models.bootstrap import BootstrapDeclareKnowledge, BootstrapDefineOutputXMRTemplate, BootstrapTriple
#
#         input = '''
#         DEFINE get-item-template($var1, $var2) AS TEMPLATE
#             TYPE PHYSICAL
#             REQUIRES @EXE.GET-CAPABILITY
#             ROOT @OUT.POSSESSION-EVENT.1
#
#             INCLUDE
#
#             @OUT.POSSESSION-EVENT.1 = {
#                 AGENT  @SELF;
#                 THEME  $var1;
#                 OTHER  @OUT.OBJECT.1;
#             }
#
#             @OUT.OBJECT.1 = {}
#         '''
#
#         name = "get-item-template"
#         type = XMR.Type.ACTION
#         capability = "@EXE.GET-CAPABILITY"
#         params = ["$var1", "$var2"]
#         root = "@OUT.POSSESSION-EVENT.1"
#
#         property1 = BootstrapTriple("AGENT", Identifier("@SELF.AGENT"))
#         property2 = BootstrapTriple("THEME", "$var1")
#         property3 = BootstrapTriple("OTHER", Identifier("@OUT.OBJECT.1"))
#         frames = [
#             BootstrapDeclareKnowledge("OUT", "POSSESSION-EVENT", index=1, properties=[property1, property2, property3]),
#             BootstrapDeclareKnowledge("OUT", "OBJECT", index=1)
#         ]
#
#         bootstrap = BootstrapDefineOutputXMRTemplate(name, type, capability, params, root, frames)
#         parsed = Grammar.parse(self.agent, input, start="output_xmr_template")
#         self.assertEqual(bootstrap, parsed)
#
#
# class TestAgentMethod(AgentMethod):
#     pass