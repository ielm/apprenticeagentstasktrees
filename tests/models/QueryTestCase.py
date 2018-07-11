from backend.models.graph import Filler, Frame, Identifier, Network, Slot
from backend.models.ontology import Ontology
from backend.models.query import AndQuery, ExactQuery, FillerQuery, FrameQuery, IdentifierQuery, LiteralQuery, NameQuery, NotQuery, OrQuery, Query, SlotQuery
from types import LambdaType
from typing import Union


import unittest


class TestQuery(Query):

    def __init__(self, result: Union[bool, LambdaType]):
        super().__init__(None)
        self.result = result

    def compare(self, other):
        if isinstance(self.result, bool):
            return self.result
        return self.result(other)


class ParseQueryTestCase(unittest.TestCase):

    def test_parse(self):
        n = Network()
        g = n.register("GRAPH")
        f = g.register("GRAPH.FRAME.1")
        f["SLOT"] = 123

        q = Query.parse(n, "SHOW FRAMES WHERE (@=GRAPH.FRAME.1 AND SLOT=123)")
        result = g.search(q)
        self.assertEqual(result, [f])


class AndQueryTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()

    def test_and_query_all_match(self):
        query = AndQuery(self.n, [TestQuery(True), TestQuery(True)])

        self.assertTrue(query.compare("any value"))

    def test_and_query_some_match(self):
        query = AndQuery(self.n, [TestQuery(True), TestQuery(False)])

        self.assertFalse(query.compare("any value"))

    def test_and_query_none_match(self):
        query = AndQuery(self.n, [TestQuery(False), TestQuery(False)])

        self.assertFalse(query.compare("any value"))

    def test_and_query_no_queries(self):
        query = AndQuery(self.n, [])

        self.assertFalse(query.compare("any value"))


class OrQueryTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()

    def test_or_query_all_match(self):
        query = OrQuery(self.n, [TestQuery(True), TestQuery(True)])

        self.assertTrue(query.compare("any value"))

    def test_or_query_some_match(self):
        query = OrQuery(self.n, [TestQuery(True), TestQuery(False)])

        self.assertTrue(query.compare("any value"))

    def test_or_query_none_match(self):
        query = OrQuery(self.n, [TestQuery(False), TestQuery(False)])

        self.assertFalse(query.compare("any value"))

    def test_or_query_no_queries(self):
        query = OrQuery(self.n, [])

        self.assertFalse(query.compare("any value"))


class ExactQueryTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()

    def test_exactly_query_all_match(self):
        query = ExactQuery(self.n, [TestQuery(True), TestQuery(True)])

        self.assertTrue(query.compare([1, 2]))

    def test_exactly_query_not_exactly(self):
        query = ExactQuery(self.n, [TestQuery(lambda x: x == 1), TestQuery(lambda x: x == 2)])

        self.assertFalse(query.compare([1, 1]))
        self.assertFalse(query.compare([2, 2]))

    def test_exactly_query_some_match(self):
        query = ExactQuery(self.n, [TestQuery(lambda x: x == 1), TestQuery(lambda x: x == 2)])

        self.assertFalse(query.compare([1]))

    def test_exactly_query_not_enough_match(self):
        query = ExactQuery(self.n, [TestQuery(lambda x: x == 1), TestQuery(lambda x: x == 2)])

        self.assertFalse(query.compare([1, 2, 3]))

    def test_exactly_query_no_match(self):
        query = ExactQuery(self.n, [TestQuery(lambda x: x == 1), TestQuery(lambda x: x == 2)])

        self.assertFalse(query.compare([0, 3]))

    def test_exactly_query_duplicates_fail(self):
        query = ExactQuery(self.n, [TestQuery(lambda x: x == 1), TestQuery(lambda x: x == 2)])

        self.assertFalse(query.compare([1, 1, 2]))

    def test_exactly_query_no_match_if_input_is_empty(self):
        query = ExactQuery(self.n, [TestQuery(lambda x: x == 1), TestQuery(lambda x: x == 2)])

        self.assertFalse(query.compare([]))

    def test_exactly_query_no_match_if_input_is_not_list(self):
        query = ExactQuery(self.n, [TestQuery(lambda x: x == 1), TestQuery(lambda x: x == 2)])

        self.assertFalse(query.compare(1))


class NotQueryTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()

    def test_not_query(self):
        self.assertTrue(NotQuery(self.n, TestQuery(False)).compare("any value"))
        self.assertFalse(NotQuery(self.n, TestQuery(True)).compare("any value"))


class FrameQueryTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()

    def test_frame_query_identifier(self):
        query = FrameQuery(self.n, IdentifierQuery(self.n, "ONT.EVENT", IdentifierQuery.Comparator.EQUALS, set=False))

        self.assertTrue(query.compare(Frame("ONT.EVENT")))
        self.assertFalse(query.compare(Frame("ONT.OBJECT")))

    def test_frame_query_identifier_isa(self):
        g = self.n.register("ONT")
        all = g.register("ALL")
        object = g.register("OBJECT", isa="ONT.ALL")
        event = g.register("EVENT", isa="ONT.ALL")
        pevent = g.register("PHYSICAL-EVENT", isa="ONT.EVENT")

        query = FrameQuery(self.n, IdentifierQuery(self.n, "ONT.EVENT", IdentifierQuery.Comparator.ISA))

        self.assertTrue(query.compare(pevent))
        self.assertFalse(query.compare(object))

    def test_frame_query_slot(self):
        query = FrameQuery(self.n, SlotQuery(self.n, NameQuery(self.n, "SLOT")))

        frame1 = Frame("FRAME1")
        frame2 = Frame("FRAME2")
        frame3 = Frame("FRAME3")

        frame1["SLOT"] = 123
        frame2["OTHER"] = 123

        self.assertTrue(query.compare(frame1))
        self.assertFalse(query.compare(frame2))
        self.assertFalse(query.compare(frame3))

    def test_frame_and(self):
        query = FrameQuery(self.n, AndQuery(self.n, [IdentifierQuery(self.n, "FRAME1", IdentifierQuery.Comparator.EQUALS, set=False), SlotQuery(self.n, NameQuery(self.n, "SLOT"))]))

        frame1 = Frame("FRAME1")
        frame2 = Frame("FRAME2")

        frame1["SLOT"] = 123
        frame2["SLOT"] = 123

        self.assertTrue(query.compare(frame1))
        self.assertFalse(query.compare(frame2))

    def test_frame_or(self):
        query = FrameQuery(self.n, OrQuery(self.n, [IdentifierQuery(self.n, "FRAME1", IdentifierQuery.Comparator.EQUALS, set=False), SlotQuery(self.n, NameQuery(self.n, "SLOT"))]))

        frame1 = Frame("FRAME1")
        frame2 = Frame("FRAME2")

        frame1["OTHER"] = 123
        frame2["SLOT"] = 123

        self.assertTrue(query.compare(frame1))
        self.assertTrue(query.compare(frame2))

    def test_frame_not(self):
        query = FrameQuery(self.n, NotQuery(self.n, IdentifierQuery(self.n, "FRAME1", IdentifierQuery.Comparator.EQUALS, set=False)))

        frame1 = Frame("FRAME1")
        frame2 = Frame("FRAME2")

        frame1["SLOT"] = 123
        frame2["OTHER"] = 123

        self.assertFalse(query.compare(frame1))
        self.assertTrue(query.compare(frame2))

    def test_frame_exact_slots(self):
        query = FrameQuery(self.n, ExactQuery(self.n, [SlotQuery(self.n, NameQuery(self.n, "SLOT"))]))

        frame1 = Frame("FRAME1")
        frame2 = Frame("FRAME2")

        frame1["SLOT"] = 123

        frame2["SLOT"] = 123
        frame2["OTHER"] = 123

        self.assertTrue(query.compare(frame1))
        self.assertFalse(query.compare(frame2))

    def test_frame_exact_as_inner_query(self):
        query = FrameQuery(self.n, AndQuery(self.n,[IdentifierQuery(self.n, "FRAME1", IdentifierQuery.Comparator.EQUALS, set=False), ExactQuery(self.n, [SlotQuery(self.n, NameQuery(self.n, "SLOT"))])]))

        frame1 = Frame("FRAME1")
        frame2 = Frame("FRAME2")
        frame3 = Frame("FRAME3")

        frame1["SLOT"] = 123

        frame2["SLOT"] = 123
        frame2["OTHER"] = 123

        frame3["SLOT"] = 123

        self.assertTrue(query.compare(frame1))
        self.assertFalse(query.compare(frame2))
        self.assertFalse(query.compare(frame3))


class SlotQueryTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()

    def test_slot_query_name(self):
        query = SlotQuery(self.n, NameQuery(self.n, "AGENT"))

        self.assertTrue(query.compare(Slot("AGENT")))
        self.assertFalse(query.compare(Slot("THEME")))

    def test_slot_query_filler(self):
        query = SlotQuery(self.n, FillerQuery(self.n, LiteralQuery(self.n, 123)))

        self.assertTrue(query.compare(Slot("SLOT", values=[123, "x", "y"])))
        self.assertTrue(query.compare(Slot("SLOT", values=[123, 456, "y"])))
        self.assertTrue(query.compare(Slot("SLOT", values=[123, 456, 789])))
        self.assertFalse(query.compare(Slot("SLOT", values=["x", "y"])))

    def test_slot_and(self):
        query = SlotQuery(self.n, AndQuery(self.n, [NameQuery(self.n, "SLOT"), FillerQuery(self.n, LiteralQuery(self.n, 123))]))

        self.assertTrue(query.compare(Slot("SLOT", values=[123, "x", "y"])))
        self.assertTrue(query.compare(Slot("SLOT", values=[123, 456, "y"])))
        self.assertFalse(query.compare(Slot("OTHER", values=[123, 456, 789])))
        self.assertFalse(query.compare(Slot("SLOT", values=["x", "y"])))

    def test_slot_or(self):
        query = SlotQuery(self.n, OrQuery(self.n, [NameQuery(self.n, "SLOT"), FillerQuery(self.n, LiteralQuery(self.n, 123))]))

        self.assertTrue(query.compare(Slot("SLOT", values=[123, "x", "y"])))
        self.assertTrue(query.compare(Slot("SLOT", values=[123, 456, "y"])))
        self.assertTrue(query.compare(Slot("OTHER", values=[123, 456, 789])))
        self.assertTrue(query.compare(Slot("SLOT", values=["x", "y"])))

    def test_slot_not(self):
        query = SlotQuery(self.n, NotQuery(self.n, NameQuery(self.n, "SLOT")))

        self.assertFalse(query.compare(Slot("SLOT", values=[123, "x", "y"])))
        self.assertFalse(query.compare(Slot("SLOT", values=[123, 456, "y"])))
        self.assertTrue(query.compare(Slot("OTHER", values=[123, 456, 789])))
        self.assertFalse(query.compare(Slot("SLOT", values=["x", "y"])))

    def test_slot_exact_fillers(self):
        query = SlotQuery(self.n, ExactQuery(self.n, [FillerQuery(self.n, LiteralQuery(self.n, 123))]))

        self.assertTrue(query.compare(Slot("SLOT", values=[123])))
        self.assertFalse(query.compare(Slot("SLOT", values=[123, "x", "y"])))
        self.assertFalse(query.compare(Slot("SLOT", values=[123, 456, "y"])))
        self.assertFalse(query.compare(Slot("SLOT", values=[123, 456, 789])))
        self.assertFalse(query.compare(Slot("SLOT", values=["x", "y"])))

    def test_slot_exact_as_inner_query(self):
        query = SlotQuery(self.n, AndQuery(self.n, [NameQuery(self.n, "SLOT"), ExactQuery(self.n, [FillerQuery(self.n, LiteralQuery(self.n, 123))])]))

        self.assertTrue(query.compare(Slot("SLOT", values=[123])))
        self.assertFalse(query.compare(Slot("OTHER", values=[123])))
        self.assertFalse(query.compare(Slot("SLOT", values=[123, "x", "y"])))
        self.assertFalse(query.compare(Slot("SLOT", values=[123, 456, "y"])))
        self.assertFalse(query.compare(Slot("SLOT", values=[123, 456, 789])))
        self.assertFalse(query.compare(Slot("SLOT", values=["x", "y"])))

    def test_slot_query_compare_frame(self):
        query = SlotQuery(self.n, NameQuery(self.n, "SLOT"))

        frame1 = Frame("FRAME1")
        frame2 = Frame("FRAME1")

        frame1["SLOT"] = 123
        frame2["OTHER"] = 123

        self.assertTrue(query.compare(frame1))
        self.assertFalse(query.compare(frame2))


class NameQueryTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()

    def test_name_query_compare_slot(self):
        query = NameQuery(self.n, "NAME1")

        self.assertTrue(query.compare(Slot("NAME1")))
        self.assertFalse(query.compare(Slot("NAME2")))


class FillerQueryTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()

    def test_filler_query_compare_literal(self):
        query = FillerQuery(self.n, LiteralQuery(self.n, 123))

        self.assertTrue(query.compare(Filler(123)))
        self.assertFalse(query.compare(Filler("123")))

    def test_filler_query_compare_identifier(self):
        query = FillerQuery(self.n, IdentifierQuery(self.n, "ONT.ALL", IdentifierQuery.Comparator.EQUALS, set=False))

        self.assertTrue(query.compare(Filler("ONT.ALL")))
        self.assertFalse(query.compare(Filler("123")))

    def test_filler_query_compare_slot(self):
        query = FillerQuery(self.n, LiteralQuery(self.n, 123))

        self.assertTrue(query.compare(Slot("SLOT", values=123)))
        self.assertTrue(query.compare(Slot("SLOT", values=[123, 456])))
        self.assertFalse(query.compare(Slot("SLOT", values=[])))


class LiteralQueryTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()

    def test_literal_query_compare(self):
        query = LiteralQuery(self.n, 123)

        self.assertTrue(query.compare(123))
        self.assertFalse(query.compare("123"))


class IdentifierQueryTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()

        self.ontology = self.n.register(Ontology("ONT"))
        self.ontology.register("ALL")
        self.ontology.register("EVENT", isa="ONT.ALL")
        self.ontology.register("OBJECT", isa="ONT.ALL")
        self.ontology.register("PHYSICAL-EVENT", isa="ONT.EVENT")

    def test_identifier_query_equals(self):
        query = IdentifierQuery(self.n, Identifier("GRAPH", "NAME", instance=123), IdentifierQuery.Comparator.EQUALS, set=False)

        self.assertTrue(query.compare(Identifier("GRAPH", "NAME", instance=123)))
        self.assertTrue(query.compare("GRAPH.NAME.123"))
        self.assertTrue(query.compare(Filler("GRAPH.NAME.123")))
        self.assertFalse(query.compare(Identifier("GRAPH", "NAME")))

    def test_identifier_query_exact_parsed(self):
        query = IdentifierQuery(self.n, "GRAPH.NAME.123", IdentifierQuery.Comparator.EQUALS, set=False)

        self.assertTrue(query.compare(Identifier("GRAPH", "NAME", instance=123)))
        self.assertTrue(query.compare("GRAPH.NAME.123"))
        self.assertTrue(query.compare(Filler("GRAPH.NAME.123")))
        self.assertFalse(query.compare(Identifier("GRAPH", "NAME")))

    def test_identifier_query_exact_frame(self):
        query = IdentifierQuery(self.n, Frame("GRAPH.NAME.123"), IdentifierQuery.Comparator.EQUALS, set=False)

        self.assertTrue(query.compare(Identifier("GRAPH", "NAME", instance=123)))
        self.assertTrue(query.compare("GRAPH.NAME.123"))
        self.assertTrue(query.compare(Filler("GRAPH.NAME.123")))
        self.assertFalse(query.compare(Identifier("GRAPH", "NAME")))

    def test_identifier_query_isa(self):
        query = IdentifierQuery(self.n, Identifier("ONT", "EVENT"), IdentifierQuery.Comparator.ISA)

        self.assertTrue(query.compare(Identifier("ONT", "PHYSICAL-EVENT")))
        self.assertTrue(query.compare("ONT.EVENT"))
        self.assertTrue(query.compare(Filler("ONT.EVENT")))
        self.assertFalse(query.compare(Identifier("ONT", "OBJECT")))

    def test_identifier_query_isa_parsed(self):
        query = IdentifierQuery(self.n, "ONT.EVENT", IdentifierQuery.Comparator.ISA)

        self.assertTrue(query.compare(Identifier("ONT", "PHYSICAL-EVENT")))
        self.assertTrue(query.compare("ONT.EVENT"))
        self.assertTrue(query.compare(Filler("ONT.EVENT")))
        self.assertFalse(query.compare(Identifier("ONT", "OBJECT")))

    def test_identifier_query_isa_frame(self):
        query = IdentifierQuery(self.n, Frame("ONT.EVENT"), IdentifierQuery.Comparator.ISA)

        self.assertTrue(query.compare(Identifier("ONT", "PHYSICAL-EVENT")))
        self.assertTrue(query.compare("ONT.EVENT"))
        self.assertTrue(query.compare(Filler("ONT.EVENT")))
        self.assertFalse(query.compare(Identifier("ONT", "OBJECT")))

    def test_identifier_query_parent(self):
        query = IdentifierQuery(self.n, Identifier("ONT", "ALL"), IdentifierQuery.Comparator.ISPARENT)

        self.assertTrue(query.compare(Identifier("ONT", "EVENT")))
        self.assertTrue(query.compare("ONT.EVENT"))
        self.assertTrue(query.compare(Filler("ONT.EVENT")))
        self.assertFalse(query.compare(Identifier("ONT", "PHYSICAL-EVENT")))

    def test_identifier_query_parent_parsed(self):
        query = IdentifierQuery(self.n, "ONT.ALL", IdentifierQuery.Comparator.ISPARENT)

        self.assertTrue(query.compare(Identifier("ONT", "EVENT")))
        self.assertTrue(query.compare("ONT.EVENT"))
        self.assertTrue(query.compare(Filler("ONT.EVENT")))
        self.assertFalse(query.compare(Identifier("ONT", "PHYSICAL-EVENT")))

    def test_identifier_query_parent_frame(self):
        query = IdentifierQuery(self.n, Frame("ONT.ALL"), IdentifierQuery.Comparator.ISPARENT)

        self.assertTrue(query.compare(Identifier("ONT", "EVENT")))
        self.assertTrue(query.compare("ONT.EVENT"))
        self.assertTrue(query.compare(Filler("ONT.EVENT")))
        self.assertFalse(query.compare(Identifier("ONT", "PHYSICAL-EVENT")))

    def test_identifier_query_subclasses(self):
        query = IdentifierQuery(self.n, Identifier("ONT", "EVENT"), IdentifierQuery.Comparator.SUBCLASSES)

        self.assertTrue(query.compare(Identifier("ONT", "ALL")))
        self.assertTrue(query.compare("ONT.ALL"))
        self.assertTrue(query.compare(Filler("ONT.ALL")))
        self.assertFalse(query.compare(Identifier("ONT", "PHYSICAL-EVENT")))

    def test_identifier_query_subclasses_parsed(self):
        query = IdentifierQuery(self.n, "ONT.EVENT", IdentifierQuery.Comparator.SUBCLASSES)

        self.assertTrue(query.compare(Identifier("ONT", "ALL")))
        self.assertTrue(query.compare("ONT.ALL"))
        self.assertTrue(query.compare(Filler("ONT.ALL")))
        self.assertFalse(query.compare(Identifier("ONT", "PHYSICAL-EVENT")))

    def test_identifier_query_subclasses_frame(self):
        query = IdentifierQuery(self.n, Frame("ONT.EVENT"), IdentifierQuery.Comparator.SUBCLASSES)

        self.assertTrue(query.compare(Identifier("ONT", "ALL")))
        self.assertTrue(query.compare("ONT.ALL"))
        self.assertTrue(query.compare(Filler("ONT.ALL")))
        self.assertFalse(query.compare(Identifier("ONT", "PHYSICAL-EVENT")))

    def test_identifier_query_expand_sets(self):
        self.ontology.register("SET", isa="ONT.ALL")

        g = self.n.register("OTHER")
        f1 = g.register("OBJECT", isa="ONT.OBJECT", generate_index=True)
        f2 = g.register("OBJECT", isa="ONT.OBJECT", generate_index=True)
        f3 = g.register("OBJECT", isa="ONT.OBJECT", generate_index=True)

        set = g.register("SET", isa="ONT.SET")
        set["MEMBER-TYPE"] = [f1, f2]

        self.assertTrue(IdentifierQuery(self.n, set, IdentifierQuery.Comparator.EQUALS).compare(set))
        self.assertTrue(IdentifierQuery(self.n, f1, IdentifierQuery.Comparator.EQUALS).compare(set))
        self.assertTrue(IdentifierQuery(self.n, f2, IdentifierQuery.Comparator.EQUALS).compare(set))
        self.assertFalse(IdentifierQuery(self.n, f3, IdentifierQuery.Comparator.EQUALS).compare(set))

    def test_identifier_query_starting_from_concept(self):
        self.ontology.register("PHYSICAL-OBJECT", isa="ONT.OBJECT")

        g = self.n.register("OTHER")
        f = g.register("OBJECT", isa="ONT.OBJECT", generate_index=True)

        self.assertFalse(IdentifierQuery(self.n, "ONT.PHYSICAL-OBJECT", IdentifierQuery.Comparator.SUBCLASSES).compare(f))
        self.assertTrue(IdentifierQuery(self.n, "ONT.PHYSICAL-OBJECT", IdentifierQuery.Comparator.SUBCLASSES, from_concept=True).compare(f))