from backend.models.graph import Filler, Fillers, Frame, Graph, Network

import unittest


class FillerTestCase(unittest.TestCase):

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
        f1 = Filler("value1")
        f2 = Filler("value1")
        f3 = Filler("value2")

        self.assertTrue(f1.compare(f2))
        self.assertFalse(f1.compare(f3))

    def test_filler_compares_to_value(self):
        f = Filler("value1")

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


class FillersTestCase(unittest.TestCase):

    def test_fillers_initialize_empty(self):
        fs = Fillers()

        self.assertEqual(list(), fs._storage)

    def test_fillers_initialize_single_filler(self):
        f1 = Filler("value1")
        fs = Fillers(f1)

        self.assertEqual([f1], fs._storage)

    def test_fillers_initialize_single_value(self):
        fs = Fillers("value1")

        self.assertEqual([Filler("value1")], fs._storage)
        self.assertEqual(["value1"], fs._storage)

    def test_fillers_initialize_multiple_fillers(self):
        f1 = Filler("value1")
        f2 = Filler("value2")
        fs = Fillers([f1, f2])

        self.assertEqual([f1, f2], fs._storage)

    def test_fillers_initialize_multiple_values(self):
        fs = Fillers(["value1", "value2"])

        self.assertEqual([Filler("value1"), Filler("value2")], fs._storage)
        self.assertEqual(["value1", "value2"], fs._storage)

    def test_fillers_compares_to_fillers(self):
        f1 = Filler("value1")
        f2 = Filler("value2")

        self.assertEqual(Fillers([f1, f2]), Fillers([f1, f2]))

    def test_fillers_compares_to_lists(self):
        f1 = Filler("value1")
        f2 = Filler("value2")

        self.assertEqual(Fillers([f1, f2]), [f1, f2])
        self.assertEqual(Fillers([f1, f2]), [f1._value, f2._value])

    def test_fillers_compares_to_single_filler(self):
        f1 = Filler("value1")
        f2 = Filler("value2")

        self.assertEqual(Fillers([f1]), f1)
        self.assertNotEqual(Fillers([f2]), f1)

    def test_fillers_compares_to_single_value(self):
        f1 = Filler("value1")
        f2 = Filler("value2")

        self.assertEqual(Fillers([f1]), "value1")
        self.assertNotEqual(Fillers([f2]), "value1")

    def test_fillers_length(self):
        f1 = Filler("value1")
        f2 = Filler("value2")

        self.assertEqual(0, len(Fillers()))
        self.assertEqual(2, len(Fillers([f1, f2])))

    def test_fillers_contains_filler(self):
        f1 = Filler("value1")
        f2 = Filler("value2")

        self.assertTrue(f1 in Fillers([f1]))
        self.assertTrue(Filler(f1._value) in Fillers([f1]))
        self.assertTrue(f1 in Fillers([f1, f2]))
        self.assertFalse(f2 in Fillers([f1]))

    def test_fillers_contains_value(self):
        f1 = Filler("value1")
        f2 = Filler("value2")

        self.assertTrue("value1" in Fillers([f1]))
        self.assertTrue("value1" in Fillers([f1, f2]))
        self.assertFalse("value2" in Fillers([f1]))

    def test_fillers_iterable(self):
        f1 = Filler(1)
        f2 = Filler(2)

        self.assertEqual([3, 4], list(map(lambda filler: filler._value + 2, Fillers([f1, f2]))))

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


class FrameTestCase(unittest.TestCase):

    def test_frame_assign_and_retrieve_value(self):
        f = Frame("TEST")
        f["SLOT"] = "VALUE"

        self.assertEqual(Fillers, type(f["SLOT"]))
        self.assertEqual(Filler, type(f["SLOT"]._storage[0]))
        self.assertEqual("VALUE", f["SLOT"]._storage[0]._value)

    def test_frame_assign_fillers(self):
        f = Frame("TEST")
        f["SLOT"] = Fillers("VALUE")

        self.assertEqual("VALUE", f["SLOT"])

    def test_frame_overwrite_fillers(self):
        f = Frame("TEST")

        f["SLOT"] = Fillers("VALUE1")
        self.assertEqual("VALUE1", f["SLOT"])

        f["SLOT"] = Fillers("VALUE2")
        self.assertEqual("VALUE2", f["SLOT"])

    def test_frame_retrieve_empty_value(self):
        f = Frame("TEST")

        self.assertEqual(f["SLOT"], Fillers())

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

    '''
    intersection compare ([v1, v2] ~= [v2, v3])
    concept compare (v1.concept == v2.concept) or (v1.concept == v2, where v2 is a concept)
    concept inherit compare (v1.concept ^= v2.concept) ...
    '''