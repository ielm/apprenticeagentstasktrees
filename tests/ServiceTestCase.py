import json

from backend.models.tmr import TMR
from backend.service import app, graph_to_json, n, ontology

import unittest


class ServiceTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    def test_list_network(self):
        n.register(TMR.new(ontology, namespace="TMR1"))
        n.register(TMR.new(ontology, namespace="TMR2"))

        response = self.app.get("/network")

        expected = n._storage.keys()

        self.assertEqual(set(json.loads(response.data)), expected)

    def test_view(self):
        g = n.register("TEST")

        f1 = g.register("TEST.FRAME.1")
        f2 = g.register("TEST.FRAME.2")

        response = self.app.post("/view", data="VIEW TEST SHOW FRAMES WHERE @=TEST.FRAME.1")
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
        g = n.register("TEST")

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
        g = n.register("TEST")

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

    @unittest.skip("This requires both the ontosem and corenlp service to be running, otherwise it will fail.")
    def test_input(self):

        from backend.config import networking
        networking["ontosem-port"] = "5001"

        self.app.delete("/reset")

        rv = self.app.post("/input", data=json.dumps([["u", "We will build a chair."], ["a", "get-screwdriver"]]), content_type='application/json')
        expected = {
            '*LCT.learning': ['WM.BUILD.1']
        }
        self.assertEqual(json.loads(rv.data), expected)

        rv = self.app.get("/htn?instance=WM.BUILD.1")
        tree = json.loads(rv.data)

        expected = {
            "nodes": {
                "id": 0,
                "parent": None,
                "name": "Start",
                "combination": "Sequential",
                "attributes": [],
                "children": [
                    {
                        "id": 1,
                        "parent": 0,
                        "name": "BUILD CHAIR",
                        "combination": "Sequential",
                        "attributes": [],
                        "children": [
                            {
                                "id": 2,
                                "parent": 1,
                                "name": "GET(screwdriver)",
                                "combination": "",
                                "children": [],
                                "attributes": ["robot"]
                            }
                        ]
                    }
                ]
            }
        }

        self.assertEqual(tree, expected)

    # The following is removed for now; we will support something like this again in the future, but not exactly
    # in this form.
    #
    # @unittest.skip("This requires both the ontosem and corenlp service to be running, otherwise it will fail.")
    # def test_query(self):
    #     from backend.config import networking
    #     networking["ontosem-port"] = "5001"
    #
    #     from backend.treenode import TreeNode
    #     TreeNode.id = 1
    #
    #     self.app.delete("/alpha/reset")
    #
    #     input = [
    #         ["u", "We will build a chair."],
    #         ["u", "First, we will build the front leg of the chair."],
    #         ["u", "Get a foot bracket."],
    #         ["u", "We have assembled a front leg."],
    #         ["u", "Now we will assemble the back."],
    #         ["a", "get-top-bracket"],
    #         ["u", "We have assembled the back."],
    #         ["u", "We finished assembling the chair."],
    #     ]
    #
    #     rv = self.app.post("/learn", data=json.dumps(input), content_type='application/json')
    #     tree = json.loads(rv.data)
    #
    #     self.assertEqual(tree["nodes"]["children"][0]["children"][1]["name"], "BUILD BACK-OF-OBJECT")
    #     self.assertEqual(tree["nodes"]["children"][0]["children"][0]["name"], "BUILD ARTIFACT-LEG")
    #
    #     input = [
    #         ["u", "We will build the back first."]
    #     ]
    #
    #     rv = self.app.post("/query", data=json.dumps(input), content_type='application/json')
    #     tree = json.loads(rv.data)
    #
    #     self.assertEqual(tree["nodes"]["children"][0]["children"][0]["name"], "BUILD BACK-OF-OBJECT")
    #     self.assertEqual(tree["nodes"]["children"][0]["children"][1]["name"], "BUILD ARTIFACT-LEG")
    #
    #     rv = self.app.get("/alpha/gettree?format=json")
    #     tree = json.loads(rv.data)
    #
    #     self.assertEqual(tree["nodes"]["children"][0]["children"][1]["name"], "BUILD BACK-OF-OBJECT")
    #     self.assertEqual(tree["nodes"]["children"][0]["children"][0]["name"], "BUILD ARTIFACT-LEG")