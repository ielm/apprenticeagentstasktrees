from backend.models.graph import Filler, Frame, Graph, Identifier, Literal, Network, Slot
from backend.models.graph import FrameParseError, UnknownFrameError

import unittest


class IdentifierTestCase(unittest.TestCase):

    def test_identifier_str(self):
        self.assertEqual("ONT.CONCEPT", str(Identifier("ONT", "CONCEPT")))
        self.assertEqual("TMR.CONCEPT.1", str(Identifier("TMR", "CONCEPT", instance=1)))

    def test_identifier_repr(self):
        self.assertEqual("@ONT.CONCEPT", repr(Identifier("ONT", "CONCEPT")))
        self.assertEqual("@TMR.CONCEPT.1", repr(Identifier("TMR", "CONCEPT", instance=1)))

    def test_identifier_equals(self):
        identifier = Identifier("TMR", "CONCEPT", instance=1)

        self.assertEqual(identifier, Identifier("TMR", "CONCEPT", instance=1))
        self.assertEqual(identifier, Frame(Identifier("TMR", "CONCEPT", instance=1)))
        self.assertEqual(identifier, "TMR.CONCEPT.1")
        self.assertEqual(identifier, "TMR.CONCEPT.1")
        self.assertEqual(identifier, "CONCEPT.1")
        self.assertEqual(Identifier("ONT", "CONCEPT"), "ONT.CONCEPT")

    def test_identifier_resolve(self):
        n = Network()

        g1 = n.register("G1")
        g2 = n.register("G2")

        frame = g1.register("CONCEPT")

        self.assertEqual(frame, Identifier("G1", "CONCEPT").resolve(g1))
        self.assertEqual(frame, Identifier("G1", "CONCEPT").resolve(g2, network=n))

        with self.assertRaises(UnknownFrameError):
            self.assertEqual(frame, Identifier("G1", "CONCEPT").resolve(g2))

    def test_identifier_parse(self):
        self.assertEqual(Identifier.parse("ONT.CONCEPT.1"), Identifier("ONT", "CONCEPT", instance=1))
        self.assertEqual(Identifier.parse("ONT.CONCEPT.1234"), Identifier("ONT", "CONCEPT", instance=1234))
        self.assertEqual(Identifier.parse("ONT.CONCEPT"), Identifier("ONT", "CONCEPT"))
        self.assertEqual(Identifier.parse("ONT.CONCEPT.XYZ"), Identifier("ONT", "CONCEPT.XYZ"))
        self.assertEqual(Identifier.parse("CONCEPT"), Identifier(None, "CONCEPT"))


class LiteralTestCase(unittest.TestCase):

    def test_literal_equals(self):
        self.assertEqual(Literal(123), 123)
        self.assertEqual(Literal(123), Literal(123))
        self.assertNotEqual(Literal(123), 124)


class FillerTestCase(unittest.TestCase):

    def test_filler_handles_input_types(self):
        self.assertTrue(type(Filler(123)._value) == Literal)
        self.assertTrue(type(Filler(Literal("xyz"))._value) == Literal)
        self.assertTrue(type(Filler("ONT.CONCEPT.1")._value) == Identifier)
        self.assertTrue(type(Filler(Identifier("ONT", "CONCEPT", instance=1))._value) == Identifier)
        self.assertTrue(type(Filler(Literal("ONT.CONCEPT.1"))._value) == Literal)

    def test_filler_equals_operator(self):
        # Use "==" as shorthand for compare(..., isa=False, intersection=True)
        g = Graph("TEST")
        f1 = Frame("OBJECT-1")
        f2 = Frame("OBJECT-2", isa="OBJECT-1")
        f3 = Frame("OBJECT-3")

        g["OBJECT-1"] = f1
        g["OBJECT-2"] = f2
        g["OBJECT-3"] = f3

        f = Filler("OBJECT-2")
        f3["REL"] = f

        self.assertTrue(f == g["OBJECT-2"])
        self.assertFalse(f == g["OBJECT-1"])
        self.assertTrue(f == ["OBJECT-1", "OBJECT-2"])

    def test_filler_isa_operator(self):
        # Use "^" as shorthand for compare(..., isa=True, intersection=True)
        g = Graph("TEST")
        f1 = Frame("OBJECT-1")
        f2 = Frame("OBJECT-2", isa="OBJECT-1")
        f3 = Frame("OBJECT-3")

        g["OBJECT-1"] = f1
        g["OBJECT-2"] = f2
        g["OBJECT-3"] = f3

        f = Filler("OBJECT-2")
        f3["REL"] = f

        self.assertTrue(f ^ "OBJECT-1")
        self.assertTrue(f ^ "OBJECT-2")
        self.assertFalse(f ^ "OBJECT-3")
        self.assertTrue(f ^ ["OBJECT-1", f3])

    def test_filler_compares_to_filler(self):
        f1 = Filler(Literal("value1"))
        f2 = Filler(Literal("value1"))
        f3 = Filler(Literal("value2"))

        self.assertTrue(f1.compare(f2))
        self.assertFalse(f1.compare(f3))

    def test_filler_compares_to_value(self):
        f = Filler(Literal("value1"))

        self.assertTrue(f.compare("value1"))
        self.assertFalse(f.compare("value2"))

    def test_filler_compares_to_frame(self):
        f = Filler("TEST.OBJECT.1")

        self.assertTrue(f.compare(Frame("TEST.OBJECT.1")))
        self.assertFalse(f.compare(Frame("TEST.OBJECT.2")))

    def test_filler_compares_to_resolvable_frame(self):
        g = Graph("TEST")

        f = Filler("TEST.OBJECT-1")
        f._graph = g

        g["OBJECT-1"] = Frame("OBJECT-1")

        self.assertTrue(f.compare(g["OBJECT-1"]))

    def test_filler_compares_by_resolving(self):
        g = Graph("TEST")

        g["OBJECT-1"] = Frame("OBJECT-1")
        g["OBJECT-2"] = Frame("OBJECT-2")

        f = Filler("OBJECT-1")
        f._frame = g["OBJECT-2"]

        self.assertTrue(f.compare(g["OBJECT-1"]))

    def test_filler_compares_with_isa(self):
        g = Graph("TEST")
        f1 = Frame("OBJECT-1")
        f2 = Frame("OBJECT-2", isa="OBJECT-1")
        f3 = Frame("OBJECT-3")

        g["OBJECT-1"] = f1
        g["OBJECT-2"] = f2
        g["OBJECT-3"] = f3

        f = Filler("OBJECT-2")
        f3["REL"] = f

        self.assertTrue(f.compare(g["OBJECT-1"], isa=True))
        self.assertFalse(f.compare(g["OBJECT-1"], isa=False))

    def test_filler_compare_ignores_isa(self):
        f = Filler("OBJECT-2")

        self.assertFalse(f.compare("XYZ", isa=True))
        self.assertFalse(f.compare("XYZ", isa=False))

    def test_filler_compares_set_inclusion(self):
        f = Filler("A")

        self.assertTrue(f.compare(["A", "B", "C"], intersection=True))
        self.assertTrue(f.compare(["A"], intersection=True))
        self.assertTrue(f.compare("A", intersection=True))
        self.assertFalse(f.compare(["B", "C"], intersection=True))
        self.assertFalse(f.compare(["A", "B", "C"], intersection=False))

    def test_filler_resolves_identifier(self):
        fa = Frame("A")
        fb = Frame("B")

        fa["REL"] = Identifier(None, "B")

        g = Graph("TEST")
        g["A"] = fa
        g["B"] = fb

        self.assertEqual(fa["REL"][0].resolve(), fb)

    def test_filler_resolve(self):
        fa = Frame("A")
        fb = Frame("B")

        fa["REL"] = "B"

        g = Graph("TEST")
        g["A"] = fa
        g["B"] = fb

        self.assertEqual(fa["REL"][0].resolve(), fb)

    def test_filler_resolve_absolute_name(self):
        fa = Frame("A")
        fb = Frame("B")

        fa["REL"] = "TEST.B"

        g = Graph("TEST")
        g["A"] = fa
        g["B"] = fb

        self.assertEqual(fa["REL"][0].resolve(), fb)

    def test_filler_resolve_cross_network(self):
        fa = Frame("A")
        fb = Frame("B")

        fa["REL"] = "TEST2.B"

        n = Network()
        g1 = n.register("TEST1")
        g1["A"] = fa

        g2 = n.register("TEST2")
        g2["B"] = fb

        self.assertEqual(fa["REL"][0].resolve(), fb)

    def test_filler_resolve_on_non_frame(self):
        g = Graph("TEST")
        g["A"] = Frame("A")
        g["A"]["ATTR"] = 1

        self.assertEqual(g["A"]["ATTR"][0].resolve(), 1)


class SlotTestCase(unittest.TestCase):

    def test_slot_initialize_empty(self):
        fs = Slot("SLOT")

        self.assertEqual(list(), fs._storage)

    def test_slot_initialize_single_filler(self):
        f1 = Filler("value1")
        fs = Slot("SLOT", f1)

        self.assertEqual([f1], fs._storage)

    def test_v_initialize_single_value(self):
        fs = Slot("SLOT", "value1")

        self.assertEqual([Filler("value1")], fs._storage)
        self.assertEqual(["value1"], fs._storage)

    def test_slot_initialize_multiple_fillers(self):
        f1 = Filler("value1")
        f2 = Filler("value2")
        fs = Slot("SLOT", [f1, f2])

        self.assertEqual([f1, f2], fs._storage)

    def test_slot_initialize_multiple_values(self):
        fs = Slot("SLOT", ["value1", "value2"])

        self.assertEqual([Filler("value1"), Filler("value2")], fs._storage)
        self.assertEqual(["value1", "value2"], fs._storage)

    def test_slot_equals_operator(self):
        # Use "==" as shorthand for compare(..., isa=False, intersection=True)

        f1 = Filler("value1")
        f2 = Filler("value2")

        self.assertTrue(Slot("SLOT", [f1, f2]) == Slot("SLOT", [f1, f2]))
        self.assertTrue(Slot("SLOT", [f1, f2]) == Slot("SLOT", [f1]))
        self.assertFalse(Slot("SLOT", [f1, f2]) == Slot("SLOT", ["xyz"]))

    def test_slot_isa_operator(self):
        # Use "^" as shorthand for compare(..., isa=True, intersection=True)

        g = Graph("TEST")
        f1 = Frame("OBJECT-1")
        f2 = Frame("OBJECT-2", isa="OBJECT-1")
        f3 = Frame("OBJECT-3")

        g["OBJECT-1"] = f1
        g["OBJECT-2"] = f2
        g["OBJECT-3"] = f3

        f = Filler("OBJECT-2")
        f3["REL"] = f

        self.assertTrue(f3["REL"] ^ g["OBJECT-1"])
        self.assertFalse(f3["REL"] ^ g["OBJECT-3"])
        self.assertTrue(f3["REL"] ^ ["OBJECT-1", g["OBJECT-3"]])

    def test_slot_compares_to_fillers(self):
        f1 = Filler("value1")
        f2 = Filler("value2")

        self.assertTrue(Slot("SLOT", [f1, f2]).compare(Slot("SLOT", [f1, f2])))

    def test_slot_compares_to_lists(self):
        f1 = Filler(Literal("value1"))
        f2 = Filler(Literal("value2"))

        self.assertTrue(Slot("SLOT", [f1, f2]).compare([f1, f2]))
        self.assertTrue(Slot("SLOT", [f1, f2]).compare([f1._value, f2._value]))

    def test_slot_compares_to_single_filler(self):
        f1 = Filler(Literal("value1"))
        f2 = Filler(Literal("value2"))

        self.assertTrue(Slot("SLOT", [f1]).compare(f1))
        self.assertFalse(Slot("SLOT", [f2]).compare(f1))

    def test_slot_compares_to_single_value(self):
        f1 = Filler("value1")
        f2 = Filler("value2")

        self.assertTrue(Slot("SLOT", [f1]).compare("value1"))
        self.assertFalse(Slot("SLOT", [f2]).compare("value1"))

    def test_slot_compares_intersection(self):
        f1 = Filler("value1")
        f2 = Filler("value2")

        self.assertTrue(Slot("SLOT", [f1]).compare(["value1", "value2"], intersection=True))
        self.assertFalse(Slot("SLOT", [f1]).compare(["value1", "value2"], intersection=False))
        self.assertFalse(Slot("SLOT", [f1]).compare(["value2"], intersection=True))

    def test_slot_compares_isa(self):
        g = Graph("TEST")
        f1 = Frame("OBJECT-1")
        f2 = Frame("OBJECT-2", isa="OBJECT-1")
        f3 = Frame("OBJECT-3")

        g["OBJECT-1"] = f1
        g["OBJECT-2"] = f2
        g["OBJECT-3"] = f3

        f = Filler("OBJECT-2")
        f3["REL"] = f

        self.assertTrue(f3["REL"].compare(g["OBJECT-1"], isa=True))
        self.assertFalse(f3["REL"].compare(g["OBJECT-1"], isa=False))

    def test_slot_length(self):
        f1 = Filler("value1")
        f2 = Filler("value2")

        self.assertEqual(0, len(Slot("SLOT")))
        self.assertEqual(2, len(Slot("SLOT", [f1, f2])))

    def test_slot_contains_filler(self):
        f1 = Filler("value1")
        f2 = Filler("value2")

        self.assertTrue(f1 in Slot("SLOT", [f1]))
        self.assertTrue(Filler(f1._value) in Slot("SLOT", [f1]))
        self.assertTrue(f1 in Slot("SLOT", [f1, f2]))
        self.assertFalse(f2 in Slot("SLOT", [f1]))

    def test_slot_contains_value(self):
        f1 = Filler("value1")
        f2 = Filler("value2")

        self.assertTrue("value1" in Slot("SLOT", [f1]))
        self.assertTrue("value1" in Slot("SLOT", [f1, f2]))
        self.assertFalse("value2" in Slot("SLOT", [f1]))

    def test_slot_iterable(self):
        f1 = Filler(1)
        f2 = Filler(2)

        self.assertEqual([3, 4], list(map(lambda filler: filler.resolve().value + 2, Slot("SLOT", [f1, f2]))))

    def test_slot_add_fillers(self):
        slot = Slot("SLOT")

        self.assertEqual(0, len(slot))

        slot += 123

        self.assertEqual(123, slot)

        slot += 456

        self.assertEqual(123, slot)
        self.assertEqual(456, slot)

    def test_slot_remove_fillers(self):
        slot = Slot("SLOT")
        slot += 123
        slot += 123
        slot += 456

        self.assertEqual(123, slot)
        self.assertEqual(456, slot)

        slot -= 456

        self.assertEqual(123, slot)
        self.assertNotEqual(456, slot)

        slot -= 123

        self.assertNotEqual(123, slot)
        self.assertNotEqual(456, slot)
        self.assertEqual(0, len(slot))

    def test_slot_add_slot(self):
        slot1 = Slot("SLOT")
        slot1 += 123

        slot2 = Slot("SLOT")
        slot2 += 234
        slot2 += 345

        slot = slot1 + slot2
        self.assertEqual(slot, 123)
        self.assertEqual(slot, 234)
        self.assertEqual(slot, 345)

        self.assertEqual(slot1, 123)
        self.assertNotEqual(slot1, 234)
        self.assertNotEqual(slot1, 345)

        self.assertNotEqual(slot2, 123)
        self.assertEqual(slot2, 234)
        self.assertEqual(slot2, 345)


class FrameTestCase(unittest.TestCase):

    def test_frame_handles_input_types(self):
        self.assertEqual(Frame("ONT.TEST").name(), "ONT.TEST")
        self.assertEqual(Frame(Identifier("ONT", "TEST")).name(), "ONT.TEST")

    def test_frame_assign_and_retrieve_value(self):
        f = Frame("TEST")
        f["SLOT"] = "VALUE"

        self.assertEqual(Slot, type(f["SLOT"]))
        self.assertEqual(Filler, type(f["SLOT"]._storage[0]))
        self.assertEqual("VALUE", f["SLOT"]._storage[0]._value)

    def test_frame_assign_fillers(self):
        f = Frame("TEST")
        f["SLOT"] = Slot("SLOT", Literal("VALUE"))

        self.assertEqual("VALUE", f["SLOT"])

    def test_frame_overwrite_fillers(self):
        f = Frame("TEST")

        f["SLOT"] = Slot("SLOT", "VALUE1")
        self.assertEqual("VALUE1", f["SLOT"])

        f["SLOT"] = Slot("SLOT", "VALUE2")
        self.assertEqual("VALUE2", f["SLOT"])

    def test_frame_retrieve_empty_value(self):
        f = Frame("TEST")

        self.assertEqual(f["SLOT"], Slot("SLOT"))

    def test_frame_slot_defined(self):
        f = Frame("TEST")
        f["SLOT"] = "VALUE"

        self.assertTrue("SLOT" in f)
        self.assertFalse("OTHER" in f)

    def test_add_fillers_to_existing_slot(self):
        f = Frame("TEST")

        f["SLOT"] = "value1"
        self.assertEqual("value1", f["SLOT"])

        f["SLOT"] += "value2"
        self.assertEqual(["value1", "value2"], f["SLOT"])

    def test_slot_contains(self):
        f = Frame("TEST")
        f["SLOT"] = ["value1", "value2"]

        self.assertTrue("value1" in f["SLOT"])
        self.assertTrue("value2" in f["SLOT"])
        self.assertFalse("value3" in f["SLOT"])

    def test_delete_slot(self):
        f = Frame("TEST")
        f["SLOT"] = "value"

        del f["SLOT"]
        self.assertEqual([], f["SLOT"])
        self.assertFalse("SLOT" in f)

    def test_length(self):
        f = Frame("TEST")
        self.assertEqual(0, len(f))

        f["SLOT"] = "value"
        self.assertEqual(1, len(f))

    def test_iterable_slots(self):
        f = Frame("TEST")
        f["SLOT1"] = "value"
        f["SLOT2"] = "value"

        result = ""
        for slot in f:
            result += slot
        self.assertEqual(result, "SLOT1SLOT2")

    def test_frame_name(self):
        g = Graph("TEST")
        g["A"] = Frame("A")

        self.assertEqual(g["A"].name(), "TEST.A")

    def test_frame_name_unknown_graph(self):
        f = Frame("A")

        self.assertEqual(f.name(), "A")

    def test_frame_ancestors(self):
        fa = Frame("A")
        fb = Frame("B", isa="A")
        fc = Frame("C", isa="B")

        g = Graph("TEST")
        g["A"] = fa
        g["B"] = fb
        g["C"] = fc

        self.assertEqual(fc.ancestors(), ["TEST.B", "TEST.A"])

    def test_frame_multiple_ancestors(self):
        fa1 = Frame("A1")
        fa2 = Frame("A2")
        fb = Frame("B", isa="A1")
        fc = Frame("C", isa=["B", "A2"])

        g = Graph("TEST")
        g["A1"] = fa1
        g["A2"] = fa2
        g["B"] = fb
        g["C"] = fc

        self.assertEqual(fc.ancestors(), ["TEST.B", "TEST.A1", "TEST.A2"])

    def test_frame_cross_network_ancestors(self):
        n = Network()

        o = n.register("ONT")
        o["ALL"] = Frame("ALL")
        o["OBJECT"] = Frame("OBJECT", isa="ALL")

        g = n.register("TEST")
        g["OBJECT-1"] = Frame("OBJECT-1", isa="ONT.OBJECT")
        g["OBJECT-2"] = Frame("OBJECT-2", isa="OBJECT-1")

        self.assertEqual(g["OBJECT-2"].ancestors(), ["TEST.OBJECT-1", "ONT.OBJECT", "ONT.ALL"])

    def test_frame_isa(self):
        fa = Frame("A")
        fb = Frame("B", isa="A")
        fc = Frame("C", isa="B")

        g = Graph("TEST")
        g["A"] = fa
        g["B"] = fb
        g["C"] = fc

        self.assertTrue(fc.isa("TEST.A"))
        self.assertTrue(fc.isa("TEST.B"))
        self.assertTrue(fc.isa("TEST.C"))
        self.assertFalse(fc.isa("TEST.OTHER"))

    def test_frame_isa_shorthand(self):
        fa = Frame("A")
        fb = Frame("B", isa="A")
        fc = Frame("C", isa="B")

        g = Graph("TEST")
        g["A"] = fa
        g["B"] = fb
        g["C"] = fc

        self.assertTrue(fc.isa("A"))
        self.assertTrue(fc.isa("B"))
        self.assertTrue(fc.isa("C"))
        self.assertFalse(fc.isa("OTHER"))

    def test_frame_isa_with_frame_input(self):
        fa = Frame("A")
        fb = Frame("B", isa="A")
        fc = Frame("C", isa="B")

        g = Graph("TEST")
        g["A"] = fa
        g["B"] = fb
        g["C"] = fc

        self.assertTrue(fc.isa(fa))
        self.assertTrue(fc.isa(fb))
        self.assertTrue(fc.isa(fc))
        self.assertFalse(fc.isa(Frame("OTHER")))

    def test_frame_isa_operator(self):
        fa = Frame("A")
        fb = Frame("B", isa="A")
        fc = Frame("C", isa="B")

        g = Graph("TEST")
        g["A"] = fa
        g["B"] = fb
        g["C"] = fc

        self.assertTrue(fc ^ fa)
        self.assertTrue(fc ^ fb)
        self.assertTrue(fc ^ fc)
        self.assertFalse(fc ^ "OTHER")

    def test_frame_concept(self):
        g = Graph("TEST")
        fa = g.register("A")
        fb = g.register("B", isa="A")

        self.assertEqual(fb.concept(), "TEST.A")
        self.assertEqual(fb.concept(full_path=False), "A")

    def test_frame_concept_explicit_path(self):
        g = Graph("TEST")
        fa = g.register("A")
        fb = g.register("B", isa="TEST.A")

        self.assertEqual(fb.concept(), "TEST.A")
        self.assertEqual(fb.concept(full_path=False), "A")

    def test_frame_concept_multiple_inheritance(self):
        g = Graph("TEST")
        fa1 = g.register("A1")
        fa2 = g.register("A2")
        fb = g.register("B", isa=["A1", "A2"])

        self.assertEquals(fb.concept(), "TEST.A1&TEST.A2")
        self.assertEquals(fb.concept(full_path=False), "A1&A2")
