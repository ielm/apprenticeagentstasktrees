import json
import os

from backend.agent import Agent
from backend.utils.YaleUtils import bootstrap, format_learned_event_yale, lookup_by_visual_id, visual_input
from ontograph import graph
from ontograph.Frame import Frame
from ontograph.Space import Space
from tests.ApprenticeAgentsTestCase import ApprenticeAgentsTestCase

from unittest import skip


class YaleUtilsTestCase(ApprenticeAgentsTestCase):

    def setUp(self):
        graph.reset()

    def test_bootstrap(self):

        input = {
            "locations": [
                {
                    "id": "workspace-1",
                    "type": "WORKSPACE",
                    "objects": [
                        {
                            "id": 1,
                            "type": "dowel"             # DOWEL
                        }
                    ],
                    "faces": ["jake", "bob"]
                }, {
                    "id": "storage-1",
                    "type": "STORAGE",
                    "objects": [
                        {
                            "id": 2,
                            "type": "front-bracket"     # BRACKET; SIDE-FB: FRONT
                        }, {
                            "id": 3,
                            "type": "foot-bracket"      # BRACKET; SIDE-TB: BOTTOM
                        }, {
                            "id": 4,
                            "type": "back-bracket"      # BRACKET; SIDE-FB: BACK
                        }
                    ],
                    "faces": []
                }, {
                    "id": "storage-2",
                    "type": "STORAGE",
                    "objects": [
                        {
                            "id": 5,
                            "type": "seat"              # SEAT
                        }, {
                            "id": 6,
                            "type": "top-bracket"       # BRACKET; SIDE-TB: TOP
                        }, {
                            "id": 7,
                            "type": "back"              # BACK-OF-OBJECT
                        }
                    ],
                    "faces": []
                }
            ]
        }

        # graph = Graph("ENV")
        Frame("@ENV.EPOCH")

        bootstrap(input, Space("ENV"))

        self.assertIn("@ENV.WORKSPACE.1", graph)
        self.assertIn("@ENV.STORAGE.1", graph)
        self.assertIn("@ENV.STORAGE.2", graph)

        self.assertIn("@ENV.DOWEL.1", graph)
        self.assertIn("@ENV.BRACKET.1", graph)
        self.assertIn("@ENV.BRACKET.2", graph)
        self.assertIn("@ENV.BRACKET.3", graph)
        self.assertIn("@ENV.BRACKET.4", graph)
        self.assertIn("@ENV.SEAT.1", graph)
        self.assertIn("@ENV.BACK-OF-OBJECT.1", graph)

        self.assertIn("@ENV.HUMAN.1", graph)
        self.assertIn("@ENV.HUMAN.2", graph)

        self.assertTrue(Frame("@ENV.DOWEL.1")["visual-object-id"] == 1)
        self.assertTrue(Frame("@ENV.SEAT.1")["visual-object-id"] == 5)
        self.assertTrue(Frame("@ENV.BACK-OF-OBJECT.1")["visual-object-id"] == 7)

        for bracket in [Frame("@ENV.BRACKET.1"), Frame("@ENV.BRACKET.2"), Frame("@ENV.BRACKET.3"), Frame("@ENV.BRACKET.4")]:
            if bracket["SIDE-FB"] == "FRONT":
                self.assertTrue(bracket["visual-object-id"] == 2)
            if bracket["SIDE-TB"] == "BOTTOM":
                self.assertTrue(bracket["visual-object-id"] == 3)
            if bracket["SIDE-FB"] == "BACK":
                self.assertTrue(bracket["visual-object-id"] == 4)
            if bracket["SIDE-TB"] == "TOP":
                self.assertTrue(bracket["visual-object-id"] == 6)

        humans = list(map(lambda human: human["HAS-NAME"].singleton(), [Frame("@ENV.HUMAN.1"), Frame("@ENV.HUMAN.2")]))
        self.assertIn("jake", humans)
        self.assertIn("bob", humans)
        self.assertEqual(2, len(humans))

        from backend.models.environment import Environment
        env = Environment(Space("ENV"))

        self.assertEqual(Frame("@ENV.WORKSPACE.1"), env.location("@ENV.DOWEL.1"))
        self.assertEqual(Frame("@ENV.WORKSPACE.1"), env.location("@ENV.HUMAN.1"))
        self.assertEqual(Frame("@ENV.WORKSPACE.1"), env.location("@ENV.HUMAN.2"))
        self.assertEqual(Frame("@ENV.STORAGE.1"), env.location("@ENV.BRACKET.1"))
        self.assertEqual(Frame("@ENV.STORAGE.1"), env.location("@ENV.BRACKET.2"))
        self.assertEqual(Frame("@ENV.STORAGE.1"), env.location("@ENV.BRACKET.3"))
        self.assertEqual(Frame("@ENV.STORAGE.2"), env.location("@ENV.SEAT.1"))
        self.assertEqual(Frame("@ENV.STORAGE.2"), env.location("@ENV.BRACKET.4"))
        self.assertEqual(Frame("@ENV.STORAGE.2"), env.location("@ENV.BACK-OF-OBJECT.1"))

    def test_visual_input(self):
        Frame("@ONT.HUMAN")

        storage1 = Frame("@TEST.STORAGE.?")
        storage2 = Frame("@TEST.STORAGE.?")
        workspace = Frame("@TEST.WORKSPACE.?")

        object1 = Frame("@TEST.OBJECT.?")
        object2 = Frame("@TEST.OBJECT.?")
        object3 = Frame("@TEST.OBJECT.?")
        object4 = Frame("@TEST.OBJECT.?")

        human1 = Frame("@TEST.HUMAN.?").add_parent("@ONT.HUMAN")
        human2 = Frame("@TEST.HUMAN.?").add_parent("@ONT.HUMAN")

        object1["visual-object-id"] = 1
        object2["visual-object-id"] = 2
        object3["visual-object-id"] = 3
        object4["visual-object-id"] = 4

        human1["HAS-NAME"] = "jake"
        human2["HAS-NAME"] = "bob"

        input = {
            "storage-1": [1, 2],
            "storage-2": [3],
            "faces": ["jake"]
        }

        expected = {
            "ENVIRONMENT": {
                "_refers_to": "TEST",
                "timestamp": "...",
                "contains": {
                    "@TEST.HUMAN.1": {
                        "LOCATION": "HERE"
                    },
                    "@TEST.HUMAN.2": {
                        "LOCATION": "NOT-HERE"
                    },
                    "@TEST.OBJECT.1": {
                        "LOCATION": "@TEST.STORAGE.1"
                    },
                    "@TEST.OBJECT.2": {
                        "LOCATION": "@TEST.STORAGE.1"
                    },
                    "@TEST.OBJECT.3": {
                        "LOCATION": "@TEST.STORAGE.2"
                    },
                    "@TEST.OBJECT.4": {
                        "LOCATION": "@TEST.WORKSPACE.1"
                    }
                }
            }
        }

        results = visual_input(input, Space("TEST"))

        self.assertEqual(expected["ENVIRONMENT"]["_refers_to"], results["ENVIRONMENT"]["_refers_to"])
        self.assertEqual(expected["ENVIRONMENT"]["contains"], results["ENVIRONMENT"]["contains"])

    def test_lookup_by_visual_id(self):
        frame1 = Frame("@ENV.FRAME")
        frame1["visual-object-id"] = 123

        frame2 = Frame("@TEST.FRAME.?")
        frame2["visual-object-id"] = 456

        self.assertEqual(frame1, lookup_by_visual_id(123))
        self.assertEqual(frame2, lookup_by_visual_id(456))
        self.assertEqual(999, lookup_by_visual_id(999))

    @skip("This uses the old Agent.input method and FR stuff; should probably be removed.")
    def test_simple_format(self):

        file = os.path.abspath(__package__) + "/resources/DemoMay2018_Analyses.json"
        demo = self.resource(file)

        input = [
            demo[0],  # We will build a chair.

            demo[3],  # First, we will build a front leg of the chair.
            demo[4],  # Get a foot bracket.
            demo[5],  # Get a front bracket.
            demo[6],  # Get a dowel.
            demo[7],  # Hold the dowel.
            demo[8],  # I am using the screwdriver to affix the brackets on the dowel with screws.
            demo[9],  # Release the dowel.
            demo[10],  # We have assembled a front leg.

            # demo[68],  # We finished assembling the chair.
        ]

        from backend.utils.OntologyLoader import OntologyServiceLoader
        OntologyServiceLoader().load()

        agent = Agent()
        for i in input:
            agent.input(i)

        output = format_learned_event_yale(Frame("@WM.BUILD.1"))

        self.assertEqual(output, self.load_resource("tests.resources", "YaleFormatSimple.json", parse_json=True))

    @skip("This uses the old Agent.input method and FR stuff; should probably be removed.")
    def test_multiple_integrated(self):

        file = os.path.abspath(__package__) + "/resources/DemoMay2018_Analyses.json"
        demo = self.resource(file)

        input = [
            demo[0],  # We will build a chair.

            demo[3],  # First, we will build a front leg of the chair.
            demo[4],  # Get a foot bracket.
            demo[5],  # Get a front bracket.
            demo[6],  # Get a dowel.
            demo[7],  # Hold the dowel.
            demo[8],  # I am using the screwdriver to affix the brackets on the dowel with screws.
            demo[9],  # Release the dowel.
            demo[10],  # We have assembled a front leg.

            demo[68],  # We finished assembling the chair.
        ]

        n = Network()
        ontology = n.register(Ontology.init_default())

        agent = Agent(ontology=ontology)
        for i in input:
            agent.input(i)

        input = [
            demo[0],  # We will build a chair.

            demo[3],  # First, we will build a front leg of the chair.
            demo[6],  # Get a dowel.
            demo[5],  # Get a front bracket.
            demo[4],  # Get a foot bracket.
            demo[7],  # Hold the dowel.
            demo[8],  # I am using the screwdriver to affix the brackets on the dowel with screws.
            demo[9],  # Release the dowel.
            demo[10],  # We have assembled a front leg.

            demo[68],  # We finished assembling the chair.
        ]

        for i in input:
            agent.input(i)

        output = format_treenode_yale(model)

        with open("resources/YaleFormatIntegrated.json", "r") as file:
            expected = file.read()
            self.assertEqual(output, json.loads(expected))
