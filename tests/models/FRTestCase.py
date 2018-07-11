from backend.heuristics.fr_heuristics import FRResolutionHeuristic, FRImportHeuristic
from backend.models.fr import FR
from backend.models.graph import Frame, Network
from backend.models.tmr import TMR

import unittest


class FRTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass  # Do not load the usual ontology

    def setUp(self):
        self.n = Network()
        self.ontology = self.n.register("ONT")
        self.fr = self.n.register(FR("FR", self.ontology))

    def test_register(self):
        instance1 = self.fr.register("CONCEPT-1")
        instance2 = self.fr.register("CONCEPT-2")
        instance3 = self.fr.register("CONCEPT-1.2", generate_index=False)

        self.assertEqual(instance1.name(), "FR.CONCEPT-1.1")
        self.assertEqual(instance2.name(), "FR.CONCEPT-2.1")
        self.assertEqual(instance3.name(), "FR.CONCEPT-1.2")

        self.assertTrue(instance1.name() in self.fr)
        self.assertTrue(instance2.name() in self.fr)
        self.assertTrue(instance3.name() in self.fr)

    def test_populate_simple(self):
        fr_id = self.fr.register("CONCEPT").name()

        input = Frame("CONCEPT-1", isa="CONCEPT")
        input["PROPERTY"] = "VALUE-123"

        resolves = {
            "VALUE-123": "CONCEPT-FR2"
        }

        self.fr.populate(fr_id, input, resolves)

        fr_instance = self.fr[fr_id]

        self.assertEqual(fr_instance["PROPERTY"], "CONCEPT-FR2")

    def test_populate_ambiguity(self):
        fr_id = self.fr.register("CONCEPT").name()

        frame = Frame("CONCEPT.1", isa="CONCEPT")
        frame["PROPERTY"] = "VALUE.123"

        resolves = {
            "VALUE.123": {"FR.CONCEPT.2", "FR.CONCEPT.3"}
        }

        self.fr.populate(fr_id, frame, resolves)

        fr_instance = self.fr[fr_id]

        self.assertTrue(fr_instance["PROPERTY"] == "FR.CONCEPT.2")
        self.assertTrue(fr_instance["PROPERTY"] == "FR.CONCEPT.3")

        self.assertEqual(2, len(fr_instance["PROPERTY"]))
        for filler in fr_instance["PROPERTY"]:
            self.assertEqual(filler._metadata, {"ambiguities": {fr_instance["PROPERTY"][0]._uuid, fr_instance["PROPERTY"][1]._uuid}})

    def test_populate_unresolved(self):
        fr_id = self.fr.register("CONCEPT").name()

        frame = Frame("CONCEPT.1", isa="CONCEPT")
        frame["PROPERTY"] = "VALUE-123"

        resolves = {}

        self.fr.populate(fr_id, frame, resolves)

        fr_instance = self.fr[fr_id]
        self.assertEqual(0, len(fr_instance["PROPERTY"]))

    def test_resolve_instance_simple(self):
        self.ontology.register("ALL")
        self.ontology.register("OBJECT", isa="ALL")
        self.ontology.register("HUMAN", isa="ALL")
        self.ontology.register("ROBOT", isa="ALL")
        self.ontology.register("CONCEPT", isa="ALL")
        self.ontology.register("SET", isa="ALL")

        frame = Frame("CONCEPT-1", isa="CONCEPT")

        resolves = {}

        iresolves = self.fr.resolve_instance(frame, resolves, tmr=None)

        self.assertEqual(iresolves, {
            frame.name(): None
        })

    def test_resolve_instance_with_relations(self):
        self.ontology.register("ALL")
        self.ontology.register("PROPERTY", isa="ALL")
        self.ontology.register("RELATION", isa="PROPERTY")
        self.ontology.register("OBJECT-RELATION", isa="RELATION")
        self.ontology.register("TEMPORAL-RELATION", isa="RELATION")
        self.ontology.register("OBJECT", isa="ALL")
        self.ontology.register("HUMAN", isa="ALL")
        self.ontology.register("ROBOT", isa="ALL")
        self.ontology.register("CONCEPT", isa="ALL")
        self.ontology.register("SET", isa="ALL")

        frame = Frame("CONCEPT-1", isa="CONCEPT")
        frame["OBJECT-RELATION"] = ["CONCEPT-123", "CONCEPT-456"]
        frame["TEMPORAL-RELATION"] = "CONCEPT-123"

        resolves = {}

        iresolves = self.fr.resolve_instance(frame, resolves, tmr=None)

        self.assertEqual(iresolves, {
            frame.name(): None,
            "CONCEPT-123": None,
            "CONCEPT-456": None
        })

    def test_resolve_instance_with_existing_resolves(self):
        self.ontology.register("ALL")
        self.ontology.register("PROPERTY", isa="ALL")
        self.ontology.register("RELATION", isa="PROPERTY")
        self.ontology.register("OBJECT-RELATION", isa="RELATION")
        self.ontology.register("TEMPORAL-RELATION", isa="RELATION")

        frame = Frame("CONCEPT-1", isa="CONCEPT")
        frame["OBJECT-RELATION"] = ["CONCEPT-123", "CONCEPT-456"]
        frame["TEMPORAL-RELATION"] = "CONCEPT-123"

        resolves = {
            frame.name(): {"CONCEPT-FR1"},
            "CONCEPT-123": {"CONCEPT-FR2"},
        }

        iresolves = self.fr.resolve_instance(frame, resolves, tmr=None)

        self.assertEqual(iresolves, {
            frame.name(): {"CONCEPT-FR1"},
            "CONCEPT-123": {"CONCEPT-FR2"},
            "CONCEPT-456": None
        })

    # This tests that the resolution of a TMR will repeat until it can resolve no further.  Typically, this would be
    # useful if the first pass of resolution found something that would help in a later pass.  In this test, we just
    # force the "resolve_b" heuristic to skip its first invocation, but because "resolve_a" finds something, the
    # resolution system should repeat, allowing "resolve_b" to work the second time.
    def test_merged_iterative_resolves(self):

        class TestHeuristicA(FRResolutionHeuristic):
            def resolve(self, instance, resolves, tmr=None):
                if instance.name() == "TMR.CONCEPT-A.1":
                    resolves["CONCEPT-A.1"] = {"FR.CONCEPT-A.1"}

        called = 0

        class TestHeuristicB(FRResolutionHeuristic):
            def resolve(self, instance, resolves, tmr=None):
                nonlocal called
                if called == 0:
                    called = 1
                elif instance.name() == "TMR.CONCEPT-B.1":
                    resolves["CONCEPT-B.1"] = {"FR.CONCEPT-B.1"}

        self.fr.heuristics = [
            TestHeuristicA,
            TestHeuristicB,
        ]

        self.fr.register("CONCEPT-A", isa="CONCEPT-A")
        self.fr.register("CONCEPT-B", isa="CONCEPT-B")

        tmr = self.n.register(TMR({
            "sentence": "Test.",
            "tmr": [{
                "results": [{
                    "TMR": {
                        "CONCEPT-A.1": {
                            "concept": "CONCEPT-A",
                            "sent-word-ind": [1, [0]]
                        },
                        "CONCEPT-B.1": {
                            "concept": "CONCEPT-B",
                            "sent-word-ind": [1, [1]]
                        },
                    }
                }]
            }],
            "syntax": [{
                "0": {},
                "1": {},
                "basicDeps": []
            }]
        }, self.ontology, namespace="TMR"))

        iresolves = self.fr.resolve_tmr(tmr)

        self.assertEqual(1, called)
        self.assertEqual(iresolves, {
            "CONCEPT-A.1": {"FR.CONCEPT-A.1"},
            "CONCEPT-B.1": {"FR.CONCEPT-B.1"},
        })

    def test_learn_tmr(self):
        self.ontology.register("ALL")
        self.ontology.register("CONCEPT", isa="ALL")
        self.ontology.register("THING", isa="ALL")
        self.ontology.register("OBJECT", isa="ALL")
        self.ontology.register("HUMAN", isa="ALL")
        self.ontology.register("ROBOT", isa="ALL")
        self.ontology.register("SET", isa="ALL")
        self.ontology.register("PROPERTY", isa="ALL")
        self.ontology.register("RELATION", isa="PROPERTY")
        self.ontology.register("AGENT", isa="RELATION")
        self.ontology.register("AGENT-OF", isa="RELATION")

        tmr = self.n.register(TMR({
            "sentence": "Test.",
            "tmr": [{
                "results": [{
                    "TMR": {
                        "CONCEPT-1": {
                            "concept": "CONCEPT",
                            "AGENT": "THING-2",
                            "sent-word-ind": [1, [0]]
                        },
                        "THING-2": {
                            "concept": "THING",
                            "AGENT-OF": "CONCEPT-1",
                            "sent-word-ind": [1, [1]]
                        },
                    }
                }]
            }],
            "syntax": [{
                "0": {},
                "1": {},
                "basicDeps": []
            }]
        }, self.ontology))

        self.fr.learn_tmr(tmr)

        self.assertEqual(2, len(self.fr))

        concept = self.fr["FR.CONCEPT.1"]
        thing = self.fr["FR.THING.1"]

        self.assertEqual(concept["AGENT"], "FR.THING.1")
        self.assertEqual(thing["AGENT-OF"], "FR.CONCEPT.1")

    def test_import_fr(self):
        to_import = FR("FR1", self.ontology._namespace)
        to_import.register("CONCEPT", isa="CONCEPT")

        destination = FR("FR2", self.ontology._namespace)
        destination.import_fr(to_import)

        self.assertTrue("FR2.CONCEPT.1" in destination)

        destination.import_fr(to_import)

        self.assertTrue("FR2.CONCEPT.1" in destination)
        self.assertTrue("FR2.CONCEPT.2" in destination)

    def test_import_fr_with_relations(self):
        to_import = FR("FR", self.ontology._namespace)
        c1 = to_import.register("CONCEPT", isa="CONCEPT")
        c2 = to_import.register("CONCEPT", isa="CONCEPT")
        c2["RELATION"] = c1

        destination = FR("DEST", self.ontology._namespace)
        destination.import_fr(to_import)

        self.assertTrue("DEST.CONCEPT.1" in destination)
        self.assertTrue("DEST.CONCEPT.2" in destination)

        self.assertTrue(destination["CONCEPT.2"]["RELATION"] == "CONCEPT.1")

    def test_import_fr_with_import_heuristics(self):
        self.ontology.register("ALL")
        self.ontology.register("CONCEPT1", isa="ALL")
        self.ontology.register("CONCEPT2", isa="ALL")

        to_import = FR("FR", self.ontology._namespace)
        to_import.register("CONCEPT1", isa="CONCEPT1")
        to_import.register("CONCEPT2", isa="CONCEPT2")

        class TestHeuristic(FRImportHeuristic):
            def filter(self, import_fr, status):
                status["FR.CONCEPT2.1"] = False

        destination = FR("DEST", self.ontology._namespace)
        destination.import_fr(to_import, import_heuristics=[TestHeuristic])

        self.assertTrue("DEST.CONCEPT1.1" in destination)
        self.assertTrue("DEST.CONCEPT2.1" not in destination)

    def test_import_fr_with_resolution_heuristics(self):
        to_import = FR("FR", self.ontology._namespace)
        to_import.register("CONCEPT", isa="CONCEPT")
        to_import.register("CONCEPT", isa="CONCEPT")

        class TestHeuristic(FRResolutionHeuristic):
            def resolve(self, instance, resolves, tmr=None):
                if instance.name() == "FR.CONCEPT.1":
                    resolves["CONCEPT.1"] = {"DEST.CONCEPT.1"}

        destination = FR("DEST", self.ontology._namespace)
        destination.register("CONCEPT", isa="CONCEPT")
        destination.import_fr(to_import, resolve_heuristics=[TestHeuristic])

        self.assertEqual(2, len(destination))
        self.assertTrue("DEST.CONCEPT.1" in destination)
        self.assertTrue("DEST.CONCEPT.2" in destination)

    def test_fr_uses_instance_of(self):
        self.ontology.register("ALL")
        self.ontology.register("OBJECT", isa="ALL")

        instance = self.fr.register("TEST", isa="ONT.OBJECT")

        self.assertIn("INSTANCE-OF", instance)
        self.assertNotIn("IS-A", instance)
        self.assertTrue(instance ^ "ONT.OBJECT")