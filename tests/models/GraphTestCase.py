from backend.models.graph import Frame, Graph, Network

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


class GraphTestCase(unittest.TestCase):

    def test_graph_add_non_frame(self):
        g = Graph("NMSP")

        with self.assertRaises(TypeError):
            g["FRAME.1"] = 123

    def test_graph_namespace_prepended(self):
        g = Graph("NMSP")

        g["FRAME.1"] = Frame()
        self.assertEqual(list(g.keys()), ["NMSP.FRAME.1"])

    def test_graph_lookup_by_full_name(self):
        g = Graph("NMSP")
        g["FRAME.1"] = Frame()

        f = g["NMSP.FRAME.1"]
        self.assertIsNotNone(f)

    def test_graph_lookup_by_partial_name(self):
        g = Graph("NMSP")
        g["FRAME.1"] = Frame()

        f = g["FRAME.1"]
        self.assertIsNotNone(f)

    def test_graph_contains_by_full_name(self):
        g = Graph("NMSP")
        g["FRAME.1"] = Frame()

        self.assertIn("NMSP.FRAME.1", g)

    def test_graph_contains_by_partial_name(self):
        g = Graph("NMSP")
        g["FRAME.1"] = Frame()

        self.assertIn("FRAME.1", g)

    def test_graph_does_not_contain(self):
        g = Graph("NMSP")

        self.assertNotIn("NMSP.FRAME.1", g)

    def test_graph_delete_by_full_name(self):
        g = Graph("NMSP")
        g["FRAME.1"] = Frame()

        del g["NMSP.FRAME.1"]
        self.assertNotIn("NMSP.FRAME.1", g)

    def test_graph_delete_by_partial_name(self):
        g = Graph("NMSP")
        g["FRAME.1"] = Frame()

        del g["FRAME.1"]
        self.assertNotIn("NMSP.FRAME.1", g)

    def test_graph_length(self):
        g = Graph("NMSP")

        self.assertEqual(0, len(g))

        g["FRAME.1"] = Frame()
        self.assertEqual(1, len(g))

    def test_graph_iter(self):
        g = Graph("NMSP")
        g["FRAME.1"] = Frame()
        g["FRAME.2"] = Frame()

        result = ""
        for frame in g:
            result += frame
        self.assertEqual(result, "NMSP.FRAME.1NMSP.FRAME.2")

    def test_clear(self):
        g = Graph("NMSP")
        g["FRAME.1"] = Frame()
        g["FRAME.2"] = Frame()

        self.assertEqual(2, len(g))

        g.clear()
        self.assertEqual(0, len(g))