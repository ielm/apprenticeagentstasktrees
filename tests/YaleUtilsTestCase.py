import json
import os

from backend.agent import Agent
from backend.models.graph import Graph, Literal, Network
from backend.models.ontology import Ontology
from backend.utils.YaleUtils import bootstrap, format_learned_event_yale, lookup_by_visual_id, visual_input
from tests.ApprenticeAgentsTestCase import ApprenticeAgentsTestCase

from unittest import skip


class YaleUtilsTestCase(ApprenticeAgentsTestCase):

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

        graph = Graph("ENV")
        graph.register("EPOCH")

        bootstrap(input, graph)

        self.assertIn("ENV.WORKSPACE.1", graph)
        self.assertIn("ENV.STORAGE.1", graph)
        self.assertIn("ENV.STORAGE.2", graph)

        self.assertIn("ENV.DOWEL.1", graph)
        self.assertIn("ENV.BRACKET.1", graph)
        self.assertIn("ENV.BRACKET.2", graph)
        self.assertIn("ENV.BRACKET.3", graph)
        self.assertIn("ENV.BRACKET.4", graph)
        self.assertIn("ENV.SEAT.1", graph)
        self.assertIn("ENV.BACK-OF-OBJECT.1", graph)

        self.assertIn("ENV.HUMAN.1", graph)
        self.assertIn("ENV.HUMAN.2", graph)

        self.assertTrue(graph["ENV.DOWEL.1"]["visual-object-id"] == 1)
        self.assertTrue(graph["ENV.SEAT.1"]["visual-object-id"] == 5)
        self.assertTrue(graph["ENV.BACK-OF-OBJECT.1"]["visual-object-id"] == 7)

        for bracket in [graph["ENV.BRACKET.1"], graph["ENV.BRACKET.2"], graph["ENV.BRACKET.3"], graph["ENV.BRACKET.4"]]:
            if bracket["SIDE-FB"] == "FRONT":
                self.assertTrue(bracket["visual-object-id"] == 2)
            if bracket["SIDE-TB"] == "BOTTOM":
                self.assertTrue(bracket["visual-object-id"] == 3)
            if bracket["SIDE-FB"] == "BACK":
                self.assertTrue(bracket["visual-object-id"] == 4)
            if bracket["SIDE-TB"] == "TOP":
                self.assertTrue(bracket["visual-object-id"] == 6)

        humans = list(map(lambda human: human["HAS-NAME"].singleton(), [graph["ENV.HUMAN.1"], graph["ENV.HUMAN.2"]]))
        self.assertIn("jake", humans)
        self.assertIn("bob", humans)
        self.assertEqual(2, len(humans))

        from backend.models.environment import Environment
        env = Environment(graph)

        self.assertEqual(graph["ENV.WORKSPACE.1"], env.location("ENV.DOWEL.1"))
        self.assertEqual(graph["ENV.WORKSPACE.1"], env.location("ENV.HUMAN.1"))
        self.assertEqual(graph["ENV.WORKSPACE.1"], env.location("ENV.HUMAN.2"))
        self.assertEqual(graph["ENV.STORAGE.1"], env.location("ENV.BRACKET.1"))
        self.assertEqual(graph["ENV.STORAGE.1"], env.location("ENV.BRACKET.2"))
        self.assertEqual(graph["ENV.STORAGE.1"], env.location("ENV.BRACKET.3"))
        self.assertEqual(graph["ENV.STORAGE.2"], env.location("ENV.SEAT.1"))
        self.assertEqual(graph["ENV.STORAGE.2"], env.location("ENV.BRACKET.4"))
        self.assertEqual(graph["ENV.STORAGE.2"], env.location("ENV.BACK-OF-OBJECT.1"))

    def test_visual_input(self):
        network = Network()
        ont = network.register(Graph("ONT"))
        graph = network.register(Graph("TEST"))

        ont.register("HUMAN", generate_index=False)

        storage1 = graph.register("STORAGE", generate_index=True)
        storage2 = graph.register("STORAGE", generate_index=True)
        workspace = graph.register("WORKSPACE", generate_index=True)

        object1 = graph.register("OBJECT", generate_index=True)
        object2 = graph.register("OBJECT", generate_index=True)
        object3 = graph.register("OBJECT", generate_index=True)
        object4 = graph.register("OBJECT", generate_index=True)

        human1 = graph.register("HUMAN", isa="ONT.HUMAN", generate_index=True)
        human2 = graph.register("HUMAN", isa="ONT.HUMAN", generate_index=True)

        object1["visual-object-id"] = 1
        object2["visual-object-id"] = 2
        object3["visual-object-id"] = 3
        object4["visual-object-id"] = 4

        human1["HAS-NAME"] = Literal("jake")
        human2["HAS-NAME"] = Literal("bob")

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
                    "TEST.HUMAN.1": {
                        "LOCATION": "HERE"
                    },
                    "TEST.HUMAN.2": {
                        "LOCATION": "NOT-HERE"
                    },
                    "TEST.OBJECT.1": {
                        "LOCATION": "TEST.STORAGE.1"
                    },
                    "TEST.OBJECT.2": {
                        "LOCATION": "TEST.STORAGE.1"
                    },
                    "TEST.OBJECT.3": {
                        "LOCATION": "TEST.STORAGE.2"
                    },
                    "TEST.OBJECT.4": {
                        "LOCATION": "TEST.WORKSPACE.1"
                    }
                }
            }
        }

        results = visual_input(input, graph)

        self.assertEqual(expected["ENVIRONMENT"]["_refers_to"], results["ENVIRONMENT"]["_refers_to"])
        self.assertEqual(expected["ENVIRONMENT"]["contains"], results["ENVIRONMENT"]["contains"])

    def test_lookup_by_visual_id(self):
        network = Network()
        env = network.register(Graph("ENV"))
        test = network.register(Graph("TEST"))

        frame1 = env.register("FRAME")
        frame1["visual-object-id"] = 123

        frame2 = test.register("FRAME")
        frame2["visual-object-id"] = 123

        frame3 = test.register("FRAME")
        frame3["visual-object-id"] = 456

        self.assertEqual(frame1, lookup_by_visual_id(network, 123))
        self.assertEqual(456, lookup_by_visual_id(network, 456))
        self.assertEqual(frame1, lookup_by_visual_id(network, frame1))
        self.assertEqual("ENV.FRAME", lookup_by_visual_id(network, "ENV.FRAME"))

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

        n = Network()
        ontology = n.register(Ontology.init_default())

        agent = Agent(ontology=ontology)
        for i in input:
            agent.input(i)

        output = format_learned_event_yale(agent.wo_memory["WM.BUILD.1"], ontology)

        self.assertEqual(output, self.load_resource("tests.resources", "YaleFormatSimple.json", parse_json=True))

    @skip
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
