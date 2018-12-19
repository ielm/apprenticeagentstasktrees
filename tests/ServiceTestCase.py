import json

from backend.models.tmr import TMR
from backend.service import agent, app, graph_to_json

import unittest


class ServiceTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    def test_list_network(self):
        response = self.app.get("/network")

        expected = agent._storage.keys()

        self.assertEqual(set(json.loads(response.data)), expected)

    def test_view(self):
        g = agent.register("TEST")

        f1 = g.register("TEST.FRAME.1")
        f2 = g.register("TEST.FRAME.2")

        response = self.app.post("/view", data="VIEW TEST SHOW FRAMES WHERE @=@TEST.FRAME.1")
        self.assertEqual(json.loads(response.data), [{"type": "Frame", "graph": "TEST", "name": "FRAME.1", "relations": [], "attributes": []}])

    def test_graph_to_json_types(self):
        from backend.models.fr import FR
        from backend.models.graph import Graph, Network
        from backend.models.ontology import Ontology
        from backend.models.view import View

        net = Network()

        g1 = net.register(Graph("G1"))
        g1.register("TEST.1", generate_index=False)

        g2 = net.register(Ontology("ONT"))
        g2.register("ALL", generate_index=False)

        g3 = net.register(TMR.new(g2, namespace="TMR#1"))
        g3.register("TEST.3", generate_index=False)

        g4 = net.register(FR("FR#1", g2))
        g4.register("TEST.4", generate_index=False)

        g5 = View(net, g4).view()

        self.assertEqual(json.loads(graph_to_json(g1)), [{"type": "Frame", "graph": "G1", "name": "TEST.1", "relations": [], "attributes": []}])
        self.assertEqual(json.loads(graph_to_json(g2)), [{"type": "OntologyFrame", "graph": "ONT", "name": "ALL", "relations": [], "attributes": []}])
        self.assertEqual(json.loads(graph_to_json(g3)), [{"type": "TMRInstance", "graph": "TMR#1", "name": "TEST.3", "relations": [], "attributes": []}])
        self.assertEqual(json.loads(graph_to_json(g4)), [{"type": "FRInstance", "graph": "FR#1", "name": "TEST.4", "relations": [], "attributes": []}])
        self.assertEqual(json.loads(graph_to_json(g5)), [{"type": "FRInstance", "graph": "FR#1", "name": "TEST.4", "relations": [], "attributes": []}])

    def test_graph_to_json_relations(self):
        g = agent.register("TEST")

        f1 = g.register("TEST.FRAME.1")
        f2 = g.register("TEST.FRAME.2")

        f1["REL"] = f2

        expected = [{
            "type": "Frame",
            "graph": "TEST",
            "name": "FRAME.1",
            "relations": [{
                "slot": "REL",
                "graph": "TEST",
                "value": "FRAME.2"
            }],
            "attributes": []
        }, {
            "type": "Frame",
            "graph": "TEST",
            "name": "FRAME.2",
            "relations": [],
            "attributes": []
        }]

        self.assertEqual(json.loads(graph_to_json(g)), expected)

    def test_graph_to_json_attributes(self):
        g = agent.register("TEST")

        f = g.register("TEST.FRAME.1")
        f["ATTR"] = 123

        expected = [{
            "type": "Frame",
            "graph": "TEST",
            "name": "FRAME.1",
            "relations": [],
            "attributes": [{
                "slot": "ATTR",
                "value": 123
            }]
        }]

        self.assertEqual(json.loads(graph_to_json(g)), expected)
