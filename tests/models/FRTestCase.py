from backend.models.fr import FR
from backend.models.instance import Instance
from backend.models.frinstance import FRInstance
from backend.models.tmr import TMR
from backend.ontology import Ontology
from tests.ApprenticeAgentsTestCase import ApprenticeAgentsTestCase


class FRInstanceTestCase(ApprenticeAgentsTestCase):

    @classmethod
    def setUpClass(cls):
        pass  # Do not load the usual ontology

    def setUp(self):
        Ontology.ontology = ApprenticeAgentsTestCase.TestOntology(include_t1=True)

    def test_register(self):
        Ontology.ontology.subclass("ALL", "CONCEPT-1")
        Ontology.ontology.subclass("ALL", "CONCEPT-2")

        fr = FR()

        instance1 = fr.register("CONCEPT-1")
        instance2 = fr.register("CONCEPT-2")
        instance3 = fr.register("CONCEPT-1")

        self.assertEqual(instance1.name, "CONCEPT-1-FR1")
        self.assertEqual(instance2.name, "CONCEPT-2-FR1")
        self.assertEqual(instance3.name, "CONCEPT-1-FR2")

        self.assertTrue(instance1.name in fr)
        self.assertTrue(instance2.name in fr)
        self.assertTrue(instance3.name in fr)

    def test_populate_simple(self):
        Ontology.ontology.subclass("ALL", "CONCEPT")

        fr = FR()

        fr_id = fr.register("CONCEPT").name

        instance = Instance("CONCEPT-1", "CONCEPT", properties={"PROPERTY": ["VALUE-123"]})

        resolves = {
            "VALUE-123": "CONCEPT-FR2"
        }

        fr.populate(fr_id, instance, resolves)

        fr_instance = fr[fr_id]
        self.assertEqual(fr_instance["PROPERTY"], [FRInstance.FRFiller(0, "CONCEPT-FR2")])

    def test_populate_ambiguity(self):
        Ontology.ontology.subclass("ALL", "CONCEPT")

        fr = FR()

        fr_id = fr.register("CONCEPT").name

        instance = Instance("CONCEPT-1", "CONCEPT", properties={"PROPERTY": ["VALUE-123"]})

        resolves = {
            "VALUE-123": {"CONCEPT-FR2", "CONCEPT-FR3"}
        }

        fr.populate(fr_id, instance, resolves)

        fr_instance = fr[fr_id]

        fr2 = fr_instance["PROPERTY"][0]
        fr3 = fr_instance["PROPERTY"][1]
        if fr2.value == "CONCEPT-FR3":
            fr2 = fr_instance["PROPERTY"][1]
            fr3 = fr_instance["PROPERTY"][0]

        self.assertTrue(FRInstance.FRFiller(0, "CONCEPT-FR2", ambiguities={fr3.id}) in fr_instance["PROPERTY"])
        self.assertTrue(FRInstance.FRFiller(0, "CONCEPT-FR3", ambiguities={fr2.id}) in fr_instance["PROPERTY"])

    def test_populate_unresolved(self):
        Ontology.ontology.subclass("ALL", "CONCEPT")

        fr = FR()

        fr_id = fr.register("CONCEPT").name

        instance = Instance("CONCEPT-1", "CONCEPT", properties={"PROPERTY": ["VALUE-123"]})

        resolves = {}

        fr.populate(fr_id, instance, resolves)

        fr_instance = fr[fr_id]
        self.assertEqual(0, len(fr_instance["PROPERTY"]))

    def test_resolve_instance_simple(self):
        Ontology.ontology.subclass("ALL", "CONCEPT")

        fr = FR()

        instance = Instance("CONCEPT-1", "CONCEPT")

        resolves = {}

        iresolves = fr.resolve_instance(instance, resolves, tmr=None)

        self.assertEqual(iresolves, {
            instance.name: None
        })

    def test_resolve_instance_with_relations(self):
        Ontology.ontology.subclass("ALL", "CONCEPT")
        Ontology.ontology.subclass("PROPERTY", "RELATION")
        Ontology.ontology.subclass("RELATION", "OBJECT-RELATION")
        Ontology.ontology.subclass("RELATION", "TEMPORAL-RELATION")

        fr = FR()

        instance = Instance("CONCEPT-1", "CONCEPT", properties={"OBJECT-RELATION": ["CONCEPT-123", "CONCEPT-456"], "TEMPORAL-RELATION": ["CONCEPT-123"]})

        resolves = {}

        iresolves = fr.resolve_instance(instance, resolves, tmr=None)

        self.assertEqual(iresolves, {
            instance.name: None,
            "CONCEPT-123": None,
            "CONCEPT-456": None
        })

    def test_resolve_instance_with_existing_resolves(self):
        Ontology.ontology.subclass("ALL", "CONCEPT")
        Ontology.ontology.subclass("PROPERTY", "RELATION")
        Ontology.ontology.subclass("RELATION", "OBJECT-RELATION")
        Ontology.ontology.subclass("RELATION", "TEMPORAL-RELATION")

        fr = FR()

        instance = Instance("CONCEPT-1", "CONCEPT", properties={"OBJECT-RELATION": ["CONCEPT-123", "CONCEPT-456"], "TEMPORAL-RELATION": ["CONCEPT-123"]})

        resolves = {
            instance.name: {"CONCEPT-FR1"},
            "CONCEPT-123": {"CONCEPT-FR2"},
        }

        iresolves = fr.resolve_instance(instance, resolves, tmr=None)

        self.assertEqual(iresolves, {
            instance.name: {"CONCEPT-FR1"},
            "CONCEPT-123": {"CONCEPT-FR2"},
            "CONCEPT-456": None
        })

    # This tests that the resolution of a TMR will repeat until it can resolve no further.  Typically, this would be
    # useful if the first pass of resolution found something that would help in a later pass.  In this test, we just
    # force the "resolve_b" heuristic to skip its first invocation, but because "resolve_a" finds something, the
    # resolution system should repeat, allowing "resolve_b" to work the second time.
    def test_merged_iterative_resolves(self):
        Ontology.ontology.subclass("ALL", "CONCEPT-A")
        Ontology.ontology.subclass("ALL", "CONCEPT-B")

        fr = FR()

        def resolve_a(fr, instance, resolves, tmr=None):
            if instance.name == "CONCEPT-A-1":
                resolves["CONCEPT-A-1"] = {"CONCEPT-A-FR1"}

        called = 0

        def resolve_b(fr, instance, resolves, tmr=None):
            nonlocal called
            if called == 0:
                called = 1
            elif instance.name == "CONCEPT-B-1":
                resolves["CONCEPT-B-1"] = {"CONCEPT-B-FR1"}

        fr.heuristics = [
            resolve_a,
            resolve_b,
        ]

        fr.register("CONCEPT-A")
        fr.register("CONCEPT-B")

        tmr = TMR({
            "sentence": "Test.",
            "tmr": [{
                "results": [{
                    "TMR": {
                        "CONCEPT-A-1": {
                            "concept": "CONCEPT-A",
                            "sent-word-ind": [1, [0]]
                        },
                        "CONCEPT-B-1": {
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
        })

        iresolves = fr.resolve_tmr(tmr)

        self.assertEqual(1, called)
        self.assertEqual(iresolves, {
            "CONCEPT-A-1": {"CONCEPT-A-FR1"},
            "CONCEPT-B-1": {"CONCEPT-B-FR1"},
        })

    def test_learn_tmr(self):
        Ontology.ontology.subclass("ALL", "CONCEPT")
        Ontology.ontology.subclass("ALL", "THING")

        fr = FR()

        tmr = TMR({
            "sentence": "Test.",
            "tmr": [{
                "results": [{
                    "TMR": {
                        "CONCEPT-1": {
                            "concept": "CONCEPT",
                            "AGENT": ["THING-2"],
                            "sent-word-ind": [1, [0]]
                        },
                        "THING-2": {
                            "concept": "THING",
                            "AGENT-OF": ["CONCEPT-1"],
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
        })

        fr.learn_tmr(tmr)

        self.assertEqual(2, len(fr))

        concept = fr["CONCEPT-FR1"]
        thing = fr["THING-FR1"]

        self.assertEqual(concept["AGENT"], [FRInstance.FRFiller(0, "THING-FR1")])
        self.assertEqual(thing["AGENT-OF"], [FRInstance.FRFiller(0, "CONCEPT-FR1")])

    def test_import_fr(self):
        Ontology.ontology.subclass("ALL", "CONCEPT")

        to_import = FR()
        to_import.register("CONCEPT")

        destination = FR()
        destination.import_fr(to_import)

        self.assertTrue("CONCEPT-FR1" in destination)

        destination.import_fr(to_import)

        self.assertTrue("CONCEPT-FR1" in destination)
        self.assertTrue("CONCEPT-FR2" in destination)

    def test_import_fr_with_relations(self):
        Ontology.ontology.subclass("ALL", "CONCEPT")

        to_import = FR()
        to_import.register("CONCEPT")
        to_import.register("CONCEPT").remember("RELATION", "CONCEPT-FR1")

        destination = FR(namespace="DEST")
        destination.import_fr(to_import)

        self.assertTrue("CONCEPT-DEST1" in destination)
        self.assertTrue("CONCEPT-DEST2" in destination)

        self.assertTrue(destination["CONCEPT-DEST2"]["RELATION"][0].value == "CONCEPT-DEST1")

    def test_import_fr_with_import_heuristics(self):
        Ontology.ontology.subclass("ALL", "CONCEPT1")
        Ontology.ontology.subclass("ALL", "CONCEPT2")

        to_import = FR()
        to_import.register("CONCEPT1")
        to_import.register("CONCEPT2")

        def heuristic(fr, status):
            status["CONCEPT2-FR1"] = False

        destination = FR()
        destination.import_fr(to_import, import_heuristics=[heuristic])

        self.assertTrue("CONCEPT1-FR1" in destination)
        self.assertTrue("CONCEPT2-FR1" not in destination)

    def test_import_fr_with_resolution_heuristics(self):
        Ontology.ontology.subclass("ALL", "CONCEPT")

        to_import = FR()
        to_import.register("CONCEPT")
        to_import.register("CONCEPT")

        def heuristic(fr, instance, resolves, tmr=None):
            if instance.name == "CONCEPT-FR1":
                resolves["CONCEPT-FR1"] = {"CONCEPT-DEST1"}

        destination = FR(namespace="DEST")
        to_import.register("CONCEPT")
        destination.import_fr(to_import, resolve_heuristics=[heuristic])

        self.assertEqual(2, len(destination))
        self.assertTrue("CONCEPT-DEST1" in destination)
        self.assertTrue("CONCEPT-DEST2" in destination)