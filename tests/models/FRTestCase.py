import unittest

from backend.models.fr import FR
from backend.models.instance import Instance
from backend.models.frinstance import FRInstance
from backend.models.tmr import TMR
from tests.ApprenticeAgentsTestCase import ApprenticeAgentsTestCase


class FRInstanceTestCase(ApprenticeAgentsTestCase):

    def test_register(self):
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
        fr = FR()

        fr_id = fr.register("CONCEPT").name

        instance = Instance({
            "concept": "CONCEPT",
            "PROPERTY": "VALUE-123"
        })

        resolves = {
            "VALUE-123": "CONCEPT-FR2"
        }

        fr.populate(fr_id, instance, resolves)

        fr_instance = fr[fr_id]
        self.assertEqual(fr_instance["PROPERTY"], [FRInstance.FRFiller(0, "CONCEPT-FR2")])

    def test_populate_ambiguity(self):
        fr = FR()

        fr_id = fr.register("CONCEPT").name

        instance = Instance({
            "concept": "CONCEPT",
            "PROPERTY": "VALUE-123"
        })

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
        fr = FR()

        fr_id = fr.register("CONCEPT").name

        instance = Instance({
            "concept": "CONCEPT",
            "PROPERTY": "VALUE-123"
        })

        resolves = {}

        fr.populate(fr_id, instance, resolves)

        fr_instance = fr[fr_id]
        self.assertEqual(0, len(fr_instance["PROPERTY"]))

    def test_resolve_instance_simple(self):
        fr = FR()

        instance = Instance({
            "concept": "CONCEPT"
        })

        resolves = {}

        iresolves = fr.resolve_instance(instance, resolves, tmr=None)

        self.assertEqual(iresolves, {
            instance.name: None
        })

    def test_resolve_instance_with_relations(self):
        fr = FR()

        instance = Instance({
            "concept": "CONCEPT",
            "OBJECT-RELATION": ["CONCEPT-123", "CONCEPT-456"],
            "TEMPORAL-RELATION": ["CONCEPT-123"]
        })

        resolves = {}

        iresolves = fr.resolve_instance(instance, resolves, tmr=None)

        self.assertEqual(iresolves, {
            instance.name: None,
            "CONCEPT-123": None,
            "CONCEPT-456": None
        })

    def test_resolve_instance_with_existing_resolves(self):
        fr = FR()

        instance = Instance({
            "concept": "CONCEPT",
            "OBJECT-RELATION": ["CONCEPT-123", "CONCEPT-456"],
            "TEMPORAL-RELATION": ["CONCEPT-123"]
        })

        resolves = {
            instance.name: ["CONCEPT-FR1"],
            "CONCEPT-123": ["CONCEPT-FR2"],
        }

        iresolves = fr.resolve_instance(instance, resolves, tmr=None)

        self.assertEqual(iresolves, {
            instance.name: ["CONCEPT-FR1"],
            "CONCEPT-123": ["CONCEPT-FR2"],
            "CONCEPT-456": None
        })

    def test_learn_tmr(self):
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