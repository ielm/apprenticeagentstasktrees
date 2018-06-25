import json

from backend.models.tmr import TMR
from backend.service import app, n, ontology

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

        response = self.app.post("/view", data="VIEW TEST SHOW FRAMES WHERE $=@TEST.FRAME.1")
        self.assertEqual(json.loads(response.data), [{"name": "FRAME.1", "relations": [], "attributes": []}])

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