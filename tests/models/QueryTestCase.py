# # from backend.models.graph import Filler, Frame, Identifier, Network, Slot
# # from backend.models.ontology import Ontology
# from backend.models.query import AndQuery, ExactQuery, FillerQuery, FrameQuery, IdentifierQuery, LiteralQuery, NameQuery, NotQuery, OrQuery, Query, SlotQuery
# from ontograph import graph
# from ontograph.Frame import Frame
# from ontograph.Index import Identifier
# from types import LambdaType
# from typing import Union
#
#
# import unittest
#
#
# class TestQuery(Query):
#
#     def __init__(self, result: Union[bool, LambdaType]):
#         self.result = result
#
#     def compare(self, other):
#         if isinstance(self.result, bool):
#             return self.result
#         return self.result(other)
#
#
# class ParseQueryTestCase(unittest.TestCase):
#
#     def setUp(self):
#         graph.reset()
#
#     def test_parse(self):
#         f = Frame("@TEST.FRAME.1")
#         f["SLOT"] = 123
#
#         q = Query.parse(None, "SHOW FRAMES WHERE (@=@TEST.FRAME.1 AND SLOT=123)")
#         result = q.search()
#         self.assertEqual(result, [f])
#
#
# class AndQueryTestCase(unittest.TestCase):
#
#     def setUp(self):
#         graph.reset()
#
#     def test_and_query_all_match(self):
#         query = AndQuery([TestQuery(True), TestQuery(True)])
#
#         self.assertTrue(query.compare("any value"))
#
#     def test_and_query_some_match(self):
#         query = AndQuery([TestQuery(True), TestQuery(False)])
#
#         self.assertFalse(query.compare("any value"))
#
#     def test_and_query_none_match(self):
#         query = AndQuery([TestQuery(False), TestQuery(False)])
#
#         self.assertFalse(query.compare("any value"))
#
#     def test_and_query_no_queries(self):
#         query = AndQuery([])
#
#         self.assertFalse(query.compare("any value"))
#
#
# class OrQueryTestCase(unittest.TestCase):
#
#     def setUp(self):
#         graph.reset()
#
#     def test_or_query_all_match(self):
#         query = OrQuery([TestQuery(True), TestQuery(True)])
#
#         self.assertTrue(query.compare("any value"))
#
#     def test_or_query_some_match(self):
#         query = OrQuery([TestQuery(True), TestQuery(False)])
#
#         self.assertTrue(query.compare("any value"))
#
#     def test_or_query_none_match(self):
#         query = OrQuery([TestQuery(False), TestQuery(False)])
#
#         self.assertFalse(query.compare("any value"))
#
#     def test_or_query_no_queries(self):
#         query = OrQuery([])
#
#         self.assertFalse(query.compare("any value"))
#
#
# class ExactQueryTestCase(unittest.TestCase):
#
#     def setUp(self):
#         graph.reset()
#
#     def test_exactly_query_all_match(self):
#         query = ExactQuery([TestQuery(True), TestQuery(True)])
#
#         self.assertTrue(query.compare([1, 2]))
#
#     def test_exactly_query_not_exactly(self):
#         query = ExactQuery([TestQuery(lambda x: x == 1), TestQuery(lambda x: x == 2)])
#
#         self.assertFalse(query.compare([1, 1]))
#         self.assertFalse(query.compare([2, 2]))
#
#     def test_exactly_query_some_match(self):
#         query = ExactQuery([TestQuery(lambda x: x == 1), TestQuery(lambda x: x == 2)])
#
#         self.assertFalse(query.compare([1]))
#
#     def test_exactly_query_not_enough_match(self):
#         query = ExactQuery([TestQuery(lambda x: x == 1), TestQuery(lambda x: x == 2)])
#
#         self.assertFalse(query.compare([1, 2, 3]))
#
#     def test_exactly_query_no_match(self):
#         query = ExactQuery([TestQuery(lambda x: x == 1), TestQuery(lambda x: x == 2)])
#
#         self.assertFalse(query.compare([0, 3]))
#
#     def test_exactly_query_duplicates_fail(self):
#         query = ExactQuery([TestQuery(lambda x: x == 1), TestQuery(lambda x: x == 2)])
#
#         self.assertFalse(query.compare([1, 1, 2]))
#
#     def test_exactly_query_no_match_if_input_is_empty(self):
#         query = ExactQuery([TestQuery(lambda x: x == 1), TestQuery(lambda x: x == 2)])
#
#         self.assertFalse(query.compare([]))
#
#     def test_exactly_query_no_match_if_input_is_not_list(self):
#         query = ExactQuery([TestQuery(lambda x: x == 1), TestQuery(lambda x: x == 2)])
#
#         self.assertFalse(query.compare(1))
#
#
# class NotQueryTestCase(unittest.TestCase):
#
#     def setUp(self):
#         graph.reset()
#
#     def test_not_query(self):
#         self.assertTrue(NotQuery(TestQuery(False)).compare("any value"))
#         self.assertFalse(NotQuery(TestQuery(True)).compare("any value"))
#
#
# class FrameQueryTestCase(unittest.TestCase):
#
#     def setUp(self):
#         graph.reset()
#
#     def test_frame_query_identifier(self):
#         query = FrameQuery(IdentifierQuery("ONT.EVENT", IdentifierQuery.Comparator.EQUALS, set=False))
#
#         self.assertTrue(query.compare(Frame("ONT.EVENT")))
#         self.assertFalse(query.compare(Frame("ONT.OBJECT")))
#
#     def test_frame_query_identifier_isa(self):
#         all = Frame("@ONT.ALL")
#         object = Frame("@ONT.OBJECT").add_parent("@ONT.ALL")
#         event = Frame("@ONT.EVENT").add_parent("@ONT.ALL")
#         pevent = Frame("@ONT.PHYSICAL-EVENT").add_parent("@ONT.EVENT")
#
#         query = FrameQuery(IdentifierQuery("@ONT.EVENT", IdentifierQuery.Comparator.ISA))
#
#         self.assertTrue(query.compare(pevent))
#         self.assertFalse(query.compare(object))
#
#     def test_frame_query_slot(self):
#         query = FrameQuery(SlotQuery(NameQuery("SLOT")))
#
#         frame1 = Frame("@TEST.FRAME.1")
#         frame2 = Frame("@TEST.FRAME.2")
#         frame3 = Frame("@TEST.FRAME.3")
#
#         frame1["SLOT"] = 123
#         frame2["OTHER"] = 123
#
#         self.assertTrue(query.compare(frame1))
#         self.assertFalse(query.compare(frame2))
#         self.assertFalse(query.compare(frame3))
#
#     def test_frame_and(self):
#         query = FrameQuery(AndQuery([IdentifierQuery("FRAME1", IdentifierQuery.Comparator.EQUALS, set=False), SlotQuery(NameQuery("SLOT"))]))
#
#         frame1 = Frame("FRAME1")
#         frame2 = Frame("FRAME2")
#
#         frame1["SLOT"] = 123
#         frame2["SLOT"] = 123
#
#         self.assertTrue(query.compare(frame1))
#         self.assertFalse(query.compare(frame2))
#
#     def test_frame_or(self):
#         query = FrameQuery(OrQuery([IdentifierQuery("FRAME1", IdentifierQuery.Comparator.EQUALS, set=False), SlotQuery( NameQuery("SLOT"))]))
#
#         frame1 = Frame("FRAME1")
#         frame2 = Frame("FRAME2")
#
#         frame1["OTHER"] = 123
#         frame2["SLOT"] = 123
#
#         self.assertTrue(query.compare(frame1))
#         self.assertTrue(query.compare(frame2))
#
#     def test_frame_not(self):
#         query = FrameQuery(NotQuery(IdentifierQuery("FRAME1", IdentifierQuery.Comparator.EQUALS, set=False)))
#
#         frame1 = Frame("FRAME1")
#         frame2 = Frame("FRAME2")
#
#         frame1["SLOT"] = 123
#         frame2["OTHER"] = 123
#
#         self.assertFalse(query.compare(frame1))
#         self.assertTrue(query.compare(frame2))
#
#     def test_frame_exact_slots(self):
#         query = FrameQuery(ExactQuery([SlotQuery(NameQuery("SLOT"))]))
#
#         frame1 = Frame("@TEST.FRAME.1")
#         frame2 = Frame("@TEST.FRAME.2")
#
#         frame1["SLOT"] = 123
#
#         frame2["SLOT"] = 123
#         frame2["OTHER"] = 123
#
#         self.assertTrue(query.compare(frame1))
#         self.assertFalse(query.compare(frame2))
#
#     def test_frame_exact_as_inner_query(self):
#         query = FrameQuery(AndQuery([IdentifierQuery("FRAME1", IdentifierQuery.Comparator.EQUALS, set=False), ExactQuery([SlotQuery(NameQuery("SLOT"))])]))
#
#         frame1 = Frame("FRAME1")
#         frame2 = Frame("FRAME2")
#         frame3 = Frame("FRAME3")
#
#         frame1["SLOT"] = 123
#
#         frame2["SLOT"] = 123
#         frame2["OTHER"] = 123
#
#         frame3["SLOT"] = 123
#
#         self.assertTrue(query.compare(frame1))
#         self.assertFalse(query.compare(frame2))
#         self.assertFalse(query.compare(frame3))
#
#
# class SlotQueryTestCase(unittest.TestCase):
#
#     def setUp(self):
#         graph.reset()
#
#     def test_slot_query_name(self):
#         query = SlotQuery(NameQuery("AGENT"))
#
#         self.assertTrue(query.compare(Frame("@TEST.FRAME.1")["AGENT"]))
#         self.assertFalse(query.compare(Frame("@TEST.FRAME.1")["THEME"]))
#
#     def test_slot_query_filler(self):
#         query = SlotQuery(FillerQuery(LiteralQuery(123)))
#
#         f = Frame("@TEST.FRAME.1")
#         f["SLOT1"] = [123, "x", "y"]
#         f["SLOT2"] = [123, 456, "y"]
#         f["SLOT3"] = [123, 456, 789]
#         f["SLOT4"] = ["x", "y"]
#
#         self.assertTrue(query.compare(f["SLOT1"]))
#         self.assertTrue(query.compare(f["SLOT2"]))
#         self.assertTrue(query.compare(f["SLOT3"]))
#         self.assertFalse(query.compare(f["SLOT4"]))
#
#     def test_slot_and(self):
#         query = SlotQuery(AndQuery([NameQuery("SLOT"), FillerQuery(LiteralQuery(123))]))
#
#         f = Frame("@TEST.FRAME.1")
#         f["SLOT"] = [123, "x", "y"]
#         self.assertTrue(query.compare(f["SLOT"]))
#
#         f["SLOT"] = [123, 456, "y"]
#         self.assertTrue(query.compare(f["SLOT"]))
#
#         f["OTHER"] = [123, 456, 789]
#         self.assertFalse(query.compare(f["OTHER"]))
#
#         f["SLOT"] = ["x", "y"]
#         self.assertFalse(query.compare(f["SLOT"]))
#
#     def test_slot_or(self):
#         query = SlotQuery(OrQuery([NameQuery("SLOT"), FillerQuery(LiteralQuery(123))]))
#
#         f = Frame("@TEST.FRAME.1")
#         f["SLOT"] = [123, "x", "y"]
#         self.assertTrue(query.compare(f["SLOT"]))
#
#         f["SLOT"] = [123, 456, "y"]
#         self.assertTrue(query.compare(f["SLOT"]))
#
#         f["OTHER"] = [123, 456, 789]
#         self.assertTrue(query.compare(f["OTHER"]))
#
#         f["SLOT"] = ["x", "y"]
#         self.assertTrue(query.compare(f["SLOT"]))
#
#     def test_slot_not(self):
#         query = SlotQuery(NotQuery(NameQuery("SLOT")))
#
#         f = Frame("@TEST.FRAME.1")
#         f["SLOT"] = [123, "x", "y"]
#         self.assertFalse(query.compare(f["SLOT"]))
#
#         f["SLOT"] = [123, 456, "y"]
#         self.assertFalse(query.compare(f["SLOT"]))
#
#         f["OTHER"] = [123, 456, 789]
#         self.assertTrue(query.compare(f["OTHER"]))
#
#         f["SLOT"] = ["x", "y"]
#         self.assertFalse(query.compare(f["SLOT"]))
#
#     def test_slot_exact_fillers(self):
#         query = SlotQuery(ExactQuery([FillerQuery(LiteralQuery(123))]))
#
#         f = Frame("@TEST.FRAME.1")
#         f["SLOT"] = [123]
#         self.assertTrue(query.compare(f["SLOT"]))
#
#         f["SLOT"] = [123, "x", "y"]
#         self.assertFalse(query.compare(f["SLOT"]))
#
#         f["SLOT"] = [123, 456, "y"]
#         self.assertFalse(query.compare(f["SLOT"]))
#
#         f["SLOT"] = [123, 456, 789]
#         self.assertFalse(query.compare(f["SLOT"]))
#
#         f["SLOT"] = ["x", "y"]
#         self.assertFalse(query.compare(f["SLOT"]))
#
#     def test_slot_exact_as_inner_query(self):
#         query = SlotQuery(AndQuery([NameQuery("SLOT"), ExactQuery([FillerQuery(LiteralQuery(123))])]))
#
#         f = Frame("@TEST.FRAME.1")
#         f["SLOT"] = [123]
#         self.assertTrue(query.compare(f["SLOT"]))
#
#         f["OTHER"] = [123]
#         self.assertFalse(query.compare(f["OTHER"]))
#
#         f["SLOT"] = [123, "x", "y"]
#         self.assertFalse(query.compare(f["SLOT"]))
#
#         f["SLOT"] = [123, 456, "y"]
#         self.assertFalse(query.compare(f["SLOT"]))
#
#         f["SLOT"] = [123, 456, 789]
#         self.assertFalse(query.compare(f["SLOT"]))
#
#         f["SLOT"] = ["x", "y"]
#         self.assertFalse(query.compare(f["SLOT"]))
#
#     def test_slot_query_compare_frame(self):
#         query = SlotQuery(NameQuery("SLOT"))
#
#         frame1 = Frame("@TEST.FRAME.1")
#         frame2 = Frame("@TEST.FRAME.2")
#
#         frame1["SLOT"] = 123
#         frame2["OTHER"] = 123
#
#         self.assertTrue(query.compare(frame1))
#         self.assertFalse(query.compare(frame2))
#
#
# class NameQueryTestCase(unittest.TestCase):
#
#     def setUp(self):
#         graph.reset()
#
#     def test_name_query_compare_slot(self):
#         query = NameQuery("NAME1")
#
#         f = Frame("@TEST.FRAME.1")
#
#         self.assertTrue(query.compare(f["NAME1"]))
#         self.assertFalse(query.compare(f["NAME2"]))
#
#
# class FillerQueryTestCase(unittest.TestCase):
#
#     def setUp(self):
#         graph.reset()
#
#     def test_filler_query_compare_literal(self):
#         query = FillerQuery(LiteralQuery(123))
#
#         self.assertTrue(query.compare(123))
#         self.assertFalse(query.compare("123"))
#
#     def test_filler_query_compare_identifier(self):
#         query = FillerQuery(IdentifierQuery("ONT.ALL", IdentifierQuery.Comparator.EQUALS, set=False))
#
#         self.assertTrue(query.compare("ONT.ALL"))
#         self.assertFalse(query.compare("123"))
#
#     def test_filler_query_compare_slot(self):
#         query = FillerQuery(LiteralQuery(123))
#
#         f = Frame("@TEST.FRAME.1")
#         f["SLOT1"] = 123
#         f["SLOT2"] = [123, 456]
#         f["SLOT3"] = []
#
#         self.assertTrue(query.compare(f["SLOT1"]))
#         self.assertTrue(query.compare(f["SLOT2"]))
#         self.assertFalse(query.compare(f["SLOT3"]))
#
#
# class LiteralQueryTestCase(unittest.TestCase):
#
#     def setUp(self):
#         graph.reset()
#
#     def test_literal_query_compare(self):
#         query = LiteralQuery(123)
#
#         self.assertTrue(query.compare(123))
#         self.assertFalse(query.compare("123"))
#
#
# class IdentifierQueryTestCase(unittest.TestCase):
#
#     def setUp(self):
#         graph.reset()
#
#         Frame("@ONT.ALL")
#         Frame("@ONT.EVENT").add_parent("@ONT.ALL")
#         Frame("@ONT.OBJECT").add_parent("@ONT.ALL")
#         Frame("@ONT.PHYSICAL-EVENT").add_parent("@ONT.EVENT")
#
#     def test_identifier_query_equals(self):
#         query = IdentifierQuery(Identifier("@GRAPH.NAME.123"), IdentifierQuery.Comparator.EQUALS, set=False)
#
#         self.assertTrue(query.compare(Identifier("@GRAPH.NAME.123")))
#         self.assertTrue(query.compare("@GRAPH.NAME.123"))
#         self.assertFalse(query.compare(Identifier("@GRAPH.NAME")))
#
#     def test_identifier_query_exact_parsed(self):
#         query = IdentifierQuery( "@GRAPH.NAME.123", IdentifierQuery.Comparator.EQUALS, set=False)
#
#         self.assertTrue(query.compare(Identifier("@GRAPH.NAME.123")))
#         self.assertTrue(query.compare("@GRAPH.NAME.123"))
#         self.assertFalse(query.compare(Identifier("@GRAPH.NAME")))
#
#     def test_identifier_query_exact_frame(self):
#         query = IdentifierQuery(Frame("@GRAPH.NAME.123"), IdentifierQuery.Comparator.EQUALS, set=False)
#
#         self.assertTrue(query.compare(Identifier("@GRAPH.NAME.123")))
#         self.assertTrue(query.compare("@GRAPH.NAME.123"))
#         self.assertFalse(query.compare(Identifier("@GRAPH.NAME")))
#
#     def test_identifier_query_isa(self):
#         query = IdentifierQuery(Identifier("@ONT.EVENT"), IdentifierQuery.Comparator.ISA)
#
#         self.assertTrue(query.compare(Identifier("@ONT.PHYSICAL-EVENT")))
#         self.assertTrue(query.compare("@ONT.EVENT"))
#         self.assertFalse(query.compare(Identifier("@ONT.OBJECT")))
#
#     def test_identifier_query_isa_parsed(self):
#         query = IdentifierQuery("@ONT.EVENT", IdentifierQuery.Comparator.ISA)
#
#         self.assertTrue(query.compare(Identifier("@ONT.PHYSICAL-EVENT")))
#         self.assertTrue(query.compare("@ONT.EVENT"))
#         self.assertFalse(query.compare(Identifier("ONT.OBJECT")))
#
#     def test_identifier_query_isa_frame(self):
#         query = IdentifierQuery(Frame("@ONT.EVENT"), IdentifierQuery.Comparator.ISA)
#
#         self.assertTrue(query.compare(Identifier("@ONT.PHYSICAL-EVENT")))
#         self.assertTrue(query.compare("@ONT.EVENT"))
#         self.assertFalse(query.compare(Identifier("@ONT.OBJECT")))
#
#     def test_identifier_query_parent(self):
#         query = IdentifierQuery(Identifier("@ONT.ALL"), IdentifierQuery.Comparator.ISPARENT)
#
#         self.assertTrue(query.compare(Identifier("@ONT.EVENT")))
#         self.assertTrue(query.compare("@ONT.EVENT"))
#         self.assertFalse(query.compare(Identifier("@ONT.PHYSICAL-EVENT")))
#
#     def test_identifier_query_parent_parsed(self):
#         query = IdentifierQuery("@ONT.ALL", IdentifierQuery.Comparator.ISPARENT)
#
#         self.assertTrue(query.compare(Identifier("@ONT.EVENT")))
#         self.assertTrue(query.compare("@ONT.EVENT"))
#         self.assertFalse(query.compare(Identifier("@ONT.PHYSICAL-EVENT")))
#
#     def test_identifier_query_parent_frame(self):
#         query = IdentifierQuery(Frame("@ONT.ALL"), IdentifierQuery.Comparator.ISPARENT)
#
#         self.assertTrue(query.compare(Identifier("@ONT.EVENT")))
#         self.assertTrue(query.compare("@ONT.EVENT"))
#         self.assertFalse(query.compare(Identifier("@ONT.PHYSICAL-EVENT")))
#
#     def test_identifier_query_subclasses(self):
#         query = IdentifierQuery(Identifier("@ONT.EVENT"), IdentifierQuery.Comparator.SUBCLASSES)
#
#         self.assertTrue(query.compare(Identifier("@ONT.ALL")))
#         self.assertTrue(query.compare("@ONT.ALL"))
#         self.assertFalse(query.compare(Identifier("@ONT.PHYSICAL-EVENT")))
#
#     def test_identifier_query_subclasses_parsed(self):
#         query = IdentifierQuery("@ONT.EVENT", IdentifierQuery.Comparator.SUBCLASSES)
#
#         self.assertTrue(query.compare(Identifier("@ONT.ALL")))
#         self.assertTrue(query.compare("@ONT.ALL"))
#         self.assertFalse(query.compare(Identifier("@ONT.PHYSICAL-EVENT")))
#
#     def test_identifier_query_subclasses_frame(self):
#         query = IdentifierQuery(Frame("@ONT.EVENT"), IdentifierQuery.Comparator.SUBCLASSES)
#
#         self.assertTrue(query.compare(Identifier("@ONT.ALL")))
#         self.assertTrue(query.compare("@ONT.ALL"))
#         self.assertFalse(query.compare(Identifier("@ONT.PHYSICAL-EVENT")))
#
#     def test_identifier_query_expand_sets(self):
#         Frame("@ONT.SET").add_parent("@ONT.ALL")
#
#         f1 = Frame("@OTHER.OBJECT.?").add_parent("@ONT.OBJECT")
#         f2 = Frame("@OTHER.OBJECT.?").add_parent("@ONT.OBJECT")
#         f3 = Frame("@OTHER.OBJECT.?").add_parent("@ONT.OBJECT")
#
#         set = Frame("@OTHER.SET.?")
#         set["ELEMENTS"] = [f1, f2]
#
#         self.assertTrue(IdentifierQuery(set, IdentifierQuery.Comparator.EQUALS).compare(set))
#         self.assertTrue(IdentifierQuery(f1, IdentifierQuery.Comparator.EQUALS).compare(set))
#         self.assertTrue(IdentifierQuery(f2, IdentifierQuery.Comparator.EQUALS).compare(set))
#         self.assertFalse(IdentifierQuery(f3, IdentifierQuery.Comparator.EQUALS).compare(set))
#
#     def test_identifier_query_starting_from_concept(self):
#         Frame("@ONT.PHYSICAL-OBJECT").add_parent("@ONT.OBJECT")
#
#         f = Frame("@OTHER.OBJECT.?").add_parent("@ONT.OBJECT")
#
#         self.assertFalse(IdentifierQuery("@ONT.PHYSICAL-OBJECT", IdentifierQuery.Comparator.SUBCLASSES).compare(f))
#         self.assertTrue(IdentifierQuery("@ONT.PHYSICAL-OBJECT", IdentifierQuery.Comparator.SUBCLASSES, from_concept=True).compare(f))