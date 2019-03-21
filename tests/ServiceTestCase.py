import json

from backend.models.tmr import TMR
from backend.service.service import agent, app, graph_to_json
from ontograph import graph
from ontograph.Frame import Frame
from ontograph.Space import Space

import unittest


class ServiceTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()
        self.app = app.test_client()

    def test_list_network(self):
        response = self.app.get("/network")

        expected = set(map(lambda s: s.name, graph))

        self.assertEqual(set(json.loads(response.data)), expected)

    def test_view(self):
        f1 = Frame("@TEST.FRAME.1")
        f2 = Frame("@TEST.FRAME.2")

        response = self.app.post("/view", data="FROM * SEARCH FOR @ = @TEST.FRAME.1;")
        self.assertEqual(json.loads(response.data), [{"type": "Frame", "graph": "TEST", "name": "@TEST.FRAME.1", "relations": [], "attributes": []}])

    def test_graph_to_json_types(self):
        # from backend.models.view import View

        Frame("@G1.TEST.1")
        Frame("@ONT.ALL")

        g3 = TMR.from_contents(namespace="TMR#1").space()
        Frame("@TMR#1.TEST.3")

        # g4 = View(None, g3).view()

        self.assertEqual(json.loads(graph_to_json(Space("G1"))), [{"type": "Frame", "graph": "G1", "name": "@G1.TEST.1", "relations": [], "attributes": []}])
        self.assertEqual(json.loads(graph_to_json(Space("ONT"))), [{"type": "OntologyFrame", "graph": "ONT", "name": "@ONT.ALL", "relations": [], "attributes": []}])
        self.assertEqual(json.loads(graph_to_json(Space("TMR#1"))), [{"type": "TMRFrame", "graph": "TMR#1", "name": "@TMR#1.TEST.3", "relations": [], "attributes": []}])
        # self.assertEqual(json.loads(graph_to_json(g4)), [{"type": "TMRFrame", "graph": "TMR#1", "name": "@TMR#1.TEST.3", "relations": [], "attributes": []}])

    def test_graph_to_json_relations(self):
        f1 = Frame("@TEST.FRAME.1")
        f2 = Frame("@TEST.FRAME.2")

        f1["REL"] = f2

        expected = [{
            "type": "Frame",
            "graph": "TEST",
            "name": "@TEST.FRAME.1",
            "relations": [{
                "slot": "REL",
                "graph": "TEST",
                "value": "@TEST.FRAME.2"
            }],
            "attributes": []
        }, {
            "type": "Frame",
            "graph": "TEST",
            "name": "@TEST.FRAME.2",
            "relations": [],
            "attributes": []
        }]

        self.assertEqual(json.loads(graph_to_json(Space("TEST"))), expected)

    def test_graph_to_json_attributes(self):
        f = Frame("@TEST.FRAME.1")
        f["ATTR"] = 123

        expected = [{
            "type": "Frame",
            "graph": "TEST",
            "name": "@TEST.FRAME.1",
            "relations": [],
            "attributes": [{
                "slot": "ATTR",
                "value": 123
            }]
        }]

        self.assertEqual(json.loads(graph_to_json(Space("TEST"))), expected)
