from backend.models.graph import Filler, Frame, Identifier, Network, Slot
from backend.models.ontology import Ontology
from backend.models.query import AndQuery, FillerQuery, FrameQuery, IdentifierQuery, LiteralQuery, NotQuery, OrQuery, Query, SlotQuery


import unittest


class TestQuery(Query):

    def __init__(self, result: bool):
        super().__init__(None)
        self.result = result

    def compare(self, other):
        return self.result


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
        query1 = FrameQuery(self.n, identifier=IdentifierQuery(self.n, identifier="ONT.EVENT"))
        query2 = FrameQuery(self.n, identifier=AndQuery(self.n, queries=[IdentifierQuery(self.n, identifier="ONT.EVENT")]))
        query3 = FrameQuery(self.n, identifier=OrQuery(self.n, queries=[IdentifierQuery(self.n, identifier="ONT.EVENT")]))
        query4 = FrameQuery(self.n, identifier=NotQuery(self.n, query=IdentifierQuery(self.n, identifier="ONT.EVENT")))

        self.assertTrue(query1.compare(Frame("ONT.EVENT")))
        self.assertTrue(query2.compare(Frame("ONT.EVENT")))
        self.assertTrue(query3.compare(Frame("ONT.EVENT")))
        self.assertFalse(query4.compare(Frame("ONT.EVENT")))

    def test_frame_query_slot(self):
        query1 = FrameQuery(self.n, slot=SlotQuery(self.n, name="SLOT"))
        query2 = FrameQuery(self.n, slot=AndQuery(self.n, queries=[SlotQuery(self.n, name="SLOT")]))
        query3 = FrameQuery(self.n, slot=OrQuery(self.n, queries=[SlotQuery(self.n, name="SLOT")]))
        query4 = FrameQuery(self.n, slot=NotQuery(self.n, query=SlotQuery(self.n, name="SLOT")))

        frame = Frame("ONT.EVENT")
        frame["SLOT"] = 1

        self.assertTrue(query1.compare(frame))
        self.assertTrue(query2.compare(frame))
        self.assertTrue(query3.compare(frame))
        self.assertFalse(query4.compare(frame))

    def test_frame_query_identifier_bad_type(self):
        query = FrameQuery(self.n, identifier=AndQuery(self.n, queries=[LiteralQuery(self.n, 123)]))

        self.assertFalse(query.compare(Frame("ANYTHING")))

    def test_frame_query_slot_bad_type(self):
        query = FrameQuery(self.n, slot=AndQuery(self.n, queries=[LiteralQuery(self.n, 123)]))

        self.assertFalse(query.compare(Frame("ANYTHING")))

    def test_frame_query_identifier_and_slot_are_anded(self):
        query = FrameQuery(self.n, identifier=IdentifierQuery(self.n, identifier="ONT.EVENT"), slot=SlotQuery(self.n, name="SLOT"))

        frame1 = Frame("ONT.EVENT")
        frame1["SLOT"] = 1

        frame2 = Frame("ONT.OBJECT")
        frame2["SLOT"] = 1

        frame3 = Frame("ONT.EVENT")

        self.assertTrue(query.compare(frame1))
        self.assertFalse(query.compare(frame2))
        self.assertFalse(query.compare(frame3))

    def test_frame_query_no_input_returns_false(self):
        query = FrameQuery(self.n)

        self.assertFalse(query.compare(Frame("ANYTHING")))


class SlotQueryTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()

    def test_slot_query_name(self):
        query = SlotQuery(self.n, name="AGENT")

        self.assertTrue(query.compare(Slot("AGENT")))
        self.assertFalse(query.compare(Slot("THEME")))

    def test_slot_query_intersects(self):
        filler1q = FillerQuery(self.n, LiteralQuery(self.n, 123))
        filler2q = FillerQuery(self.n, LiteralQuery(self.n, 456))
        filler3q = FillerQuery(self.n, LiteralQuery(self.n, 789))

        query = SlotQuery(self.n, queries=[filler1q, filler2q, filler3q], intersects=True, contains=False, equals=False)

        self.assertTrue(query.compare(Slot("SLOT", values=[123, "x", "y"])))
        self.assertTrue(query.compare(Slot("SLOT", values=[123, 456, "y"])))
        self.assertTrue(query.compare(Slot("SLOT", values=[123, 456, 789])))
        self.assertFalse(query.compare(Slot("SLOT", values=["x", "y"])))

    def test_slot_query_contains(self):
        filler1q = FillerQuery(self.n, LiteralQuery(self.n, 123))
        filler2q = FillerQuery(self.n, LiteralQuery(self.n, 456))
        filler3q = FillerQuery(self.n, LiteralQuery(self.n, 789))

        query = SlotQuery(self.n, queries=[filler1q, filler2q, filler3q], intersects=False, contains=True, equals=False)

        self.assertFalse(query.compare(Slot("SLOT", values=[123, "x", "y", "z"])))
        self.assertFalse(query.compare(Slot("SLOT", values=[123, 456, "y", "z"])))
        self.assertTrue(query.compare(Slot("SLOT", values=[123, 456, 789])))
        self.assertTrue(query.compare(Slot("SLOT", values=[123, 456, 789, "z"])))
        self.assertFalse(query.compare(Slot("SLOT", values=["x", "y", "z"])))

    def test_slot_query_equals(self):
        filler1q = FillerQuery(self.n, LiteralQuery(self.n, 123))
        filler2q = FillerQuery(self.n, LiteralQuery(self.n, 456))
        filler3q = FillerQuery(self.n, LiteralQuery(self.n, 789))

        query = SlotQuery(self.n, queries=[filler1q, filler2q, filler3q], intersects=False, contains=False, equals=True)

        self.assertFalse(query.compare(Slot("SLOT", values=[123, "x", "y", "z"])))
        self.assertFalse(query.compare(Slot("SLOT", values=[123, 456, "y", "z"])))
        self.assertTrue(query.compare(Slot("SLOT", values=[123, 456, 789])))
        self.assertFalse(query.compare(Slot("SLOT", values=[123, 456, 789, "z"])))
        self.assertFalse(query.compare(Slot("SLOT", values=["x", "y", "z"])))

    def test_slot_query_multiple_comparators_uses_toughest(self):
        filler1q = FillerQuery(self.n, LiteralQuery(self.n, 123))
        filler2q = FillerQuery(self.n, LiteralQuery(self.n, 456))
        filler3q = FillerQuery(self.n, LiteralQuery(self.n, 789))

        query = SlotQuery(self.n, queries=[filler1q, filler2q, filler3q], intersects=True, contains=False, equals=True)

        self.assertFalse(query.compare(Slot("SLOT", values=[123, "x", "y", "z"])))
        self.assertFalse(query.compare(Slot("SLOT", values=[123, 456, "y", "z"])))
        self.assertTrue(query.compare(Slot("SLOT", values=[123, 456, 789])))
        self.assertFalse(query.compare(Slot("SLOT", values=[123, 456, 789, "z"])))
        self.assertFalse(query.compare(Slot("SLOT", values=["x", "y", "z"])))

    def test_slot_query_no_comparators_defaults_to_false(self):
        filler1q = FillerQuery(self.n, LiteralQuery(self.n, 123))
        filler2q = FillerQuery(self.n, LiteralQuery(self.n, 456))
        filler3q = FillerQuery(self.n, LiteralQuery(self.n, 789))

        query = SlotQuery(self.n, queries=[filler1q, filler2q, filler3q], intersects=False, contains=False, equals=False)

        self.assertFalse(query.compare(Slot("SLOT", values=[123, "x", "y", "z"])))
        self.assertFalse(query.compare(Slot("SLOT", values=[123, 456, "y", "z"])))
        self.assertFalse(query.compare(Slot("SLOT", values=[123, 456, 789])))
        self.assertFalse(query.compare(Slot("SLOT", values=[123, 456, 789, "z"])))
        self.assertFalse(query.compare(Slot("SLOT", values=["x", "y", "z"])))

    def test_slot_query_comparators_without_query_are_ignored(self):
        query = SlotQuery(self.n, intersects=False, contains=False, equals=False)

        self.assertFalse(query.compare(Slot("SLOT", values=[123, "x", "y", "z"])))
        self.assertFalse(query.compare(Slot("SLOT", values=[123, 456, "y", "z"])))
        self.assertFalse(query.compare(Slot("SLOT", values=[123, 456, 789])))
        self.assertFalse(query.compare(Slot("SLOT", values=[123, 456, 789, "z"])))
        self.assertFalse(query.compare(Slot("SLOT", values=["x", "y", "z"])))

    def test_slot_query_name_and_comparators_are_anded(self):
        filler1q = FillerQuery(self.n, LiteralQuery(self.n, 123))
        filler2q = FillerQuery(self.n, LiteralQuery(self.n, 456))
        filler3q = FillerQuery(self.n, LiteralQuery(self.n, 789))

        query = SlotQuery(self.n, name="AGENT", queries=[filler1q, filler2q, filler3q], intersects=True, contains=False, equals=False)

        self.assertTrue(query.compare(Slot("AGENT", values=[123, "x", "y", "z"])))
        self.assertFalse(query.compare(Slot("THEME", values=[123, 456, "y", "z"])))
        self.assertFalse(query.compare(Slot("AGENT", values=["x", "y", "z"])))

    def test_slot_query_all_query_types(self):
        q1 = FillerQuery(self.n, LiteralQuery(self.n, 123))
        q2 = LiteralQuery(self.n, 456)
        q3 = IdentifierQuery(self.n, "ONT.ALL")

        query = SlotQuery(self.n, queries=[q1, q2, q3], intersects=True, contains=False, equals=False)

        self.assertTrue(query.compare(Slot("SLOT", values=[123, "y", "z"])))
        self.assertTrue(query.compare(Slot("SLOT", values=[456, "y", "z"])))
        self.assertTrue(query.compare(Slot("SLOT", values=[Identifier("ONT", "ALL"), "y", "z"])))


class FillerQueryTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()

    def test_filler_query_compare_literal(self):
        query = FillerQuery(self.n, LiteralQuery(self.n, 123))

        self.assertTrue(query.compare(Filler(123)))
        self.assertFalse(query.compare(Filler("123")))

    def test_filler_query_compare_identifier(self):
        query = FillerQuery(self.n, IdentifierQuery(self.n, identifier="ONT.ALL"))

        self.assertTrue(query.compare(Filler("ONT.ALL")))
        self.assertFalse(query.compare(Filler("123")))


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

    def test_identifier_query_no_input(self):
        query = IdentifierQuery(self.n)

        self.assertFalse(query.compare(Identifier("GRAPH", "NAME")))

    def test_identifier_query_exact(self):
        query = IdentifierQuery(self.n, identifier=Identifier("GRAPH", "NAME", instance=123))

        self.assertTrue(query.compare(Identifier("GRAPH", "NAME", instance=123)))
        self.assertTrue(query.compare("GRAPH.NAME.123"))
        self.assertFalse(query.compare(Identifier("GRAPH", "NAME")))

    def test_identifier_query_exact_parsed(self):
        query = IdentifierQuery(self.n, identifier="GRAPH.NAME.123")

        self.assertTrue(query.compare(Identifier("GRAPH", "NAME", instance=123)))
        self.assertTrue(query.compare("GRAPH.NAME.123"))
        self.assertFalse(query.compare(Identifier("GRAPH", "NAME")))

    def test_identifier_query_isa(self):
        query = IdentifierQuery(self.n, isa=Identifier("ONT", "EVENT"))

        self.assertTrue(query.compare(Identifier("ONT", "PHYSICAL-EVENT")))
        self.assertTrue(query.compare("ONT.EVENT"))
        self.assertFalse(query.compare(Identifier("ONT", "OBJECT")))

    def test_identifier_query_isa_parsed(self):
        query = IdentifierQuery(self.n, isa="ONT.EVENT")

        self.assertTrue(query.compare(Identifier("ONT", "PHYSICAL-EVENT")))
        self.assertTrue(query.compare("ONT.EVENT"))
        self.assertFalse(query.compare(Identifier("ONT", "OBJECT")))

    def test_identifier_query_parent(self):
        query = IdentifierQuery(self.n, parent=Identifier("ONT", "ALL"))

        self.assertTrue(query.compare(Identifier("ONT", "EVENT")))
        self.assertTrue(query.compare("ONT.EVENT"))
        self.assertFalse(query.compare(Identifier("ONT", "PHYSICAL-EVENT")))

    def test_identifier_query_parent_parsed(self):
        query = IdentifierQuery(self.n, parent="ONT.ALL")

        self.assertTrue(query.compare(Identifier("ONT", "EVENT")))
        self.assertTrue(query.compare("ONT.EVENT"))
        self.assertFalse(query.compare(Identifier("ONT", "PHYSICAL-EVENT")))

    def test_identifier_query_ors_inputs(self):
        query = IdentifierQuery(self.n, identifier="ONT.PHYSICAL-EVENT", parent="ONT.ALL")

        self.assertTrue(query.compare(Identifier("ONT", "EVENT")))
        self.assertTrue(query.compare("ONT.EVENT"))
        self.assertTrue(query.compare(Identifier("ONT", "PHYSICAL-EVENT")))