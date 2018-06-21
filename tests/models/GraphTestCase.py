from backend.models.graph import Frame, Graph, Identifier, Network
from backend.models.query import FrameQuery, SlotQuery

import unittest


class NetworkTestCase(unittest.TestCase):

    def test_network_assign_graph(self):
        n = Network()
        g = Graph("NMSP")

        n["NMSP"] = g
        self.assertEqual(n["NMSP"], g)

    def test_network_contains(self):
        n = Network()
        g = Graph("NMSP")

        n["NMSP"] = g
        self.assertTrue("NMSP" in n)
        self.assertFalse("XYZ" in n)

    def test_network_assign_non_graph(self):
        n = Network()

        with self.assertRaises(TypeError):
            n["NMSP"] = 123

    def test_network_assign_incorrect_namespace(self):
        n = Network()
        g = Graph("NMSP")

        with self.assertRaises(Network.NamespaceError):
            n["XYZ"] = g

    def test_network_length(self):
        n = Network()
        self.assertEqual(0, len(n))

        n["A"] = Graph("A")
        self.assertEqual(1, len(n))

        n["B"] = Graph("B")
        self.assertEqual(2, len(n))

    def test_network_delete_graph(self):
        n = Network()
        n["NMSP"] = Graph("NMSP")

        self.assertEqual(1, len(n))

        del n["NMSP"]
        self.assertEqual(0, len(n))

    def test_network_iter(self):
        n = Network()
        n["A"] = Graph("A")
        n["B"] = Graph("B")

        result = ""
        for graph in n:
            result += graph
        self.assertEqual(result, "AB")

    def test_network_register_convenience(self):
        n = Network()
        g = n.register("ABC")

        self.assertEqual(type(g), Graph)
        self.assertTrue("ABC" in n)
        self.assertEqual(g, n["ABC"])

        with self.assertRaises(TypeError):
            n.register(123)

    def test_network_register_existing_graph(self):
        n = Network()
        g = Graph("ABC")
        n.register(g)

        self.assertTrue("ABC" in n)
        self.assertEqual(g, n["ABC"])

    def test_network_lookup_with_identifier(self):
        n = Network()

        g1 = n.register("TEST1")
        g2 = n.register("TEST2")

        f1 = Frame("OBJECT.1")
        f2 = Frame("OBJECT.1")

        g1["OBJECT.1"] = f1
        g2["OBJECT.1"] = f2

        result = n.lookup(Identifier("TEST2", "OBJECT", instance=1))
        self.assertEqual(result, f2)

    def test_network_lookup_explicit(self):
        n = Network()

        g1 = n.register("TEST1")
        g2 = n.register("TEST2")

        f1 = Frame("OBJECT.1")
        f2 = Frame("OBJECT.1")

        g1["OBJECT.1"] = f1
        g2["OBJECT.1"] = f2

        result = n.lookup("TEST2.OBJECT.1")
        self.assertEqual(result, f2)

    def test_network_lookup_with_graph(self):
        n = Network()

        g1 = n.register("TEST1")
        g2 = n.register("TEST2")

        f1 = Frame("OBJECT.1")
        f2 = Frame("OBJECT.1")

        g1["OBJECT.1"] = f1
        g2["OBJECT.1"] = f2

        result = n.lookup("OBJECT.1", graph="TEST2")
        self.assertEqual(result, f2)

    def test_network_lookup_with_redundant_graph(self):
        n = Network()

        g1 = n.register("TEST1")
        g2 = n.register("TEST2")

        f1 = Frame("OBJECT.1")
        f2 = Frame("OBJECT.1")

        g1["OBJECT.1"] = f1
        g2["OBJECT.1"] = f2

        result = n.lookup("TEST2.OBJECT.1", graph="TEST2")
        self.assertEqual(result, f2)

    def test_network_lookup_with_misleading_graph(self):
        n = Network()

        g1 = n.register("TEST1")
        g2 = n.register("TEST2")

        f1 = Frame("OBJECT.1")
        f2 = Frame("OBJECT.1")

        g1["OBJECT.1"] = f1
        g2["OBJECT.1"] = f2

        result = n.lookup("TEST2.OBJECT.1", graph="TEST1")
        self.assertEqual(result, f2)

    def test_network_lookup_with_unknown_graph_information(self):
        n = Network()

        with self.assertRaises(Exception):
            n.lookup("OBJECT-1")

        with self.assertRaises(Exception):
            n.lookup("OBJECT.1")


class GraphTestCase(unittest.TestCase):

    def test_graph_add_non_frame(self):
        g = Graph("NMSP")

        with self.assertRaises(TypeError):
            g["FRAME.1"] = 123

    def test_graph_add_frame_with_incorrect_name(self):
        g = Graph("NMSP")

        with self.assertRaises(Network.NamespaceError):
            g["XYZ"] = Frame("FRAME.1")

    def test_graph_namespace_prepended(self):
        g = Graph("NMSP")

        g["FRAME.1"] = Frame("FRAME.1")
        self.assertEqual(list(g.keys()), ["NMSP.FRAME.1"])

    def test_graph_lookup_by_identifier(self):
        g = Graph("NMSP")
        g["FRAME.1"] = Frame("FRAME.1")

        f = g[Identifier("NMSP", "FRAME", instance=1)]
        self.assertIsNotNone(f)

    def test_graph_lookup_by_full_name(self):
        g = Graph("NMSP")
        g["FRAME.1"] = Frame("FRAME.1")

        f = g["NMSP.FRAME.1"]
        self.assertIsNotNone(f)

    def test_graph_lookup_by_partial_name(self):
        g = Graph("NMSP")
        g["FRAME.1"] = Frame("FRAME.1")

        f = g["FRAME.1"]
        self.assertIsNotNone(f)

    def test_graph_contains_by_full_name(self):
        g = Graph("NMSP")
        g["FRAME.1"] = Frame("FRAME.1")

        self.assertIn("NMSP.FRAME.1", g)

    def test_graph_contains_by_partial_name(self):
        g = Graph("NMSP")
        g["FRAME.1"] = Frame("FRAME.1")

        self.assertIn("FRAME.1", g)

    def test_graph_does_not_contain(self):
        g = Graph("NMSP")

        self.assertNotIn("NMSP.FRAME.1", g)

    def test_graph_delete_by_full_name(self):
        g = Graph("NMSP")
        g["FRAME.1"] = Frame("FRAME.1")

        del g["NMSP.FRAME.1"]
        self.assertNotIn("NMSP.FRAME.1", g)

    def test_graph_delete_by_partial_name(self):
        g = Graph("NMSP")
        g["FRAME.1"] = Frame("FRAME.1")

        del g["FRAME.1"]
        self.assertNotIn("NMSP.FRAME.1", g)

    def test_graph_length(self):
        g = Graph("NMSP")

        self.assertEqual(0, len(g))

        g["FRAME.1"] = Frame("FRAME.1")
        self.assertEqual(1, len(g))

    def test_graph_iter(self):
        g = Graph("NMSP")
        g["FRAME.1"] = Frame("FRAME.1")
        g["FRAME.2"] = Frame("FRAME.2")

        result = ""
        for frame in g:
            result += frame
        self.assertEqual(result, "NMSP.FRAME.1NMSP.FRAME.2")

    def test_clear(self):
        g = Graph("NMSP")
        g["FRAME.1"] = Frame("FRAME.1")
        g["FRAME.2"] = Frame("FRAME.2")

        self.assertEqual(2, len(g))

        g.clear()
        self.assertEqual(0, len(g))

    def test_graph_register_convenience(self):
        g = Graph("NMSP")
        f = g.register("FRAME.1")

        self.assertEqual(type(f), Frame)
        self.assertTrue("FRAME.1" in g)
        self.assertEqual(f, g["FRAME.1"])

        with self.assertRaises(TypeError):
            g.register(123)

        f = g.register("FRAME.2", isa="FRAME.1")
        self.assertTrue(f.isa("NMSP.FRAME.1"))

    def test_graph_search(self):
        n = Network()

        g = n.register(Graph("NMSP"))
        f1 = g.register("FRAME.1")
        f2 = g.register("FRAME.2")

        f1["SLOT"] = 123

        query = FrameQuery(n, slot=SlotQuery(n, name="SLOT"))
        results = g.search(query)

        self.assertEqual(results, [f1])


class NetworkComprehensiveExampleTestCase(unittest.TestCase):

    def test_comprehsive_example(self):
        n = Network()

        ontology = n.register("ONT")
        tmr = n.register("TMR")

        all = ontology.register("ALL")
        object = ontology.register("OBJECT", isa="ALL")
        event = ontology.register("EVENTAL", isa="ALL")
        pobject = ontology.register("PHYSICAL-OBJECT", isa="OBJECT")

        event1 = tmr.register("EVENT.1", isa="ONT.EVENT")
        human1 = tmr.register("HUMAN.1", isa="ONT.PHYSICAL-OBJECT")
        thing1 = tmr.register("THING.1", isa="ONT.PHYSICAL-OBJECT")
        thing2 = tmr.register("THING.2", isa="ONT.PHYSICAL-OBJECT")

        event1["AGENT"] = "HUMAN.1"
        event1["THEME"] = "THING.1"
        event1["THEME"] += "THING.2"

        self.assertTrue(event1["THEME"] ^ "ONT.OBJECT")
        self.assertTrue(event1["AGENT"] == "HUMAN.1")