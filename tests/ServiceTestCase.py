import json

from backend.main import app

import unittest


class ServiceTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    @unittest.skip("This requires both the ontosem and corenlp service to be running, otherwise it will fail.")
    def test_learn(self):

        from backend.config import networking
        networking["ontosem-port"] = "5001"

        from backend.treenode import TreeNode
        TreeNode.id = 1

        rv = self.app.post("/learn", data=json.dumps([["u", "We will build a chair."], ["a", "get-screwdriver"]]), content_type='application/json')
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
                                "combination": "Sequential",
                                "children": [],
                                "attributes": ["ROBOT"]
                            }
                        ]
                    }
                ]
            }
        }

        self.assertEqual(tree, expected)