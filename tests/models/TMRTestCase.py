from backend.models.graph import Identifier, Network
from backend.models.tmr import TMR, TMRInstance

from pkgutil import get_data
import json
import unittest


class TMRTestCase(unittest.TestCase):

    def setUp(self):
        super().setUp()

        self.n = Network()

        self.ontology = self.n.register("ONT")
        self.ontology.register("ALL")
        self.ontology.register("OBJECT", isa="ALL")
        self.ontology.register("EVENT", isa="ALL")
        self.ontology.register("PROPERTY", isa="ALL")

    def load_resource(self, module: str, file: str, parse_json: bool=False):
        binary = get_data(module, file)

        if not parse_json:
            return str(binary)

        return json.loads(binary)

    def test_tmr_as_graph(self):
        tmr = TMR.new(self.ontology)

        agent1 = tmr.register("AGENT.1")
        event1 = tmr.register("EVENT.1")
        theme1 = tmr.register("THEME.1")

        event1["AGENT"] = "AGENT.1"
        event1["THEME"] = "THEME.1"

        self.assertEqual(agent1, event1["AGENT"][0].resolve())
        self.assertEqual(theme1, event1["THEME"][0].resolve())

    def test_tmr_loaded(self):
        self.ontology.register("CHAIR", isa="OBJECT")
        self.ontology.register("RELATION", isa="PROPERTY")
        self.ontology.register("THEME", isa="RELATION")

        r = self.load_resource("tests.resources", "DemoMay2018_Analyses.json", parse_json=True)
        tmr = self.n.register(TMR(r[0], self.ontology))

        self.assertEqual(tmr["BUILD-1"]["THEME"][0].resolve(), tmr["CHAIR-1"])
        self.assertTrue(tmr["BUILD-1"]["THEME"] ^ "ONT.CHAIR")
        self.assertTrue(tmr["BUILD-1"]["AGENT"] == "SET-1")
        self.assertTrue(tmr["BUILD-1"]["THEME"] ^ "ONT.OBJECT")

    def test_tmr_is_event_or_object(self):
        tmr = self.n.register(TMR.new(self.ontology))

        tmr.register("OBJECT-1", isa="ONT.OBJECT")
        tmr.register("EVENT-1", isa="ONT.EVENT")

        self.assertTrue(tmr["OBJECT-1"].isa("ONT.OBJECT"))
        self.assertFalse(tmr["OBJECT-1"].isa("ONT.EVENT"))

        self.assertTrue(tmr["EVENT-1"].isa("ONT.EVENT"))
        self.assertFalse(tmr["EVENT-1"].isa("ONT.OBJECT"))

        self.assertTrue(tmr["OBJECT-1"] ^ "ONT.OBJECT")
        self.assertFalse(tmr["OBJECT-1"] ^ "ONT.EVENT")

        self.assertTrue(tmr["EVENT-1"] ^ "ONT.EVENT")
        self.assertFalse(tmr["EVENT-1"] ^ "ONT.OBJECT")

        self.assertTrue(tmr["OBJECT-1"].is_object())
        self.assertFalse(tmr["OBJECT-1"].is_event())

        self.assertTrue(tmr["EVENT-1"].is_event())
        self.assertFalse(tmr["EVENT-1"].is_object())

    def test_tmr_find_main_event(self):
        tmr = self.n.register(TMR.new(self.ontology))

        object1 = tmr.register("OBJECT-1", isa="ONT.OBJECT")
        event1 = tmr.register("EVENT-1", isa="ONT.EVENT")

        self.assertEqual(event1, tmr.find_main_event())

    def test_tmr_find_main_event_with_purpose_of(self):
        tmr = self.n.register(TMR.new(self.ontology))

        object1 = tmr.register("OBJECT-1", isa="ONT.OBJECT")
        event1 = tmr.register("EVENT-1", isa="ONT.EVENT")
        event2 = tmr.register("EVENT-2", isa="ONT.EVENT")
        event3 = tmr.register("EVENT-3", isa="ONT.EVENT")

        event1["PURPOSE-OF"] = event2
        event2["PURPOSE-OF"] = event3

        self.assertEqual(event3, tmr.find_main_event())

    def test_tmr_is_prefix(self):
        tmr = self.n.register(TMR.new(self.ontology))

        event1 = tmr.register("EVENT-1", isa="ONT.EVENT")

        self.assertFalse(tmr.is_prefix())

        event1["TIME"] = [[">", "FIND-ANCHOR-TIME"]]

        self.assertTrue(tmr.is_prefix())

    def test_tmr_is_postfix(self):
        tmr = self.n.register(TMR.new(self.ontology))

        event1 = tmr.register("EVENT-1", isa="ONT.EVENT")

        self.assertFalse(tmr.is_postfix())

        event1["TIME"] = [["<", "FIND-ANCHOR-TIME"]]

        self.assertTrue(tmr.is_postfix())

    def test_tmr_is_postfix_generic_event(self):
        self.ontology.register("ASPECT", isa="ALL")

        tmr = self.n.register(TMR.new(self.ontology))

        aspect1 = tmr.register("ASPECT-1", isa="ONT.ASPECT")
        event1 = tmr.register("EVENT-1", isa="ONT.EVENT")

        self.assertFalse(tmr.is_postfix())

        aspect1["PHASE"] = "END"
        aspect1["SCOPE"] = "EVENT-1"

        self.assertTrue(tmr.is_postfix())

    def test_tmr_find_by_concept(self):
        self.ontology.register("PHYSICAL-OBJECT", isa="OBJECT")

        tmr = self.n.register(TMR.new(self.ontology))

        self.assertEqual([], tmr.find_by_concept("ONT.OBJECT"))

        event = tmr.register("EVENT.1", isa="ONT.EVENT")
        o1 = tmr.register("O.1", isa="ONT.OBJECT")
        o2 = tmr.register("O.2", isa="ONT.OBJECT")
        o3 = tmr.register("O.3", isa="ONT.PHYSICAL-OBJECT")

        self.assertEqual([o1, o2, o3], tmr.find_by_concept("ONT.OBJECT"))


class TMRInstanceTestCase(unittest.TestCase):

    def setUp(self):
        super().setUp()

        self.n = Network()

        self.ontology = self.n.register("ONT")
        self.ontology.register("ALL")
        self.ontology.register("OBJECT", isa="ALL")
        self.ontology.register("EVENT", isa="ALL")
        self.ontology.register("PROPERTY", isa="ALL")

    def load_resource(self, module: str, file: str, parse_json: bool=False):
        binary = get_data(module, file)

        if not parse_json:
            return str(binary)

        return json.loads(binary)

    def test_tmr_instance_maps_relations_to_identifiers(self):
        self.ontology.register("RELATION", isa="PROPERTY")
        self.ontology.register("ATTRIBUTE", isa="PROPERTY")
        self.ontology.register("ONTOLOGY-SLOT", isa="PROPERTY")
        self.ontology.register("EXTRA-ONTOLOGICAL", isa="PROPERTY")
        self.ontology.register("SECOND-ORDER-PROPERTY", isa="PROPERTY")

        self.ontology.register("RELATION-CHILD", isa="RELATION")

        properties = {
            "RELATION": "TMR.THING.1",
            "RELATION-CHILD": "TMR.THING.1",
            "ATTRIBUTE": "TMR.THING.1",
            "ONTOLOGY-SLOT": "TMR.THING.1",
            "EXTRA-ONTOLOGICAL": "TMR.THING.1",
            "SECOND-ORDER-PROPERTY": "TMR.THING.1",
        }

        instance = TMRInstance("NAME", properties=properties, ontology=self.ontology)

        self.assertTrue(isinstance(instance["RELATION"][0]._value, Identifier))
        self.assertTrue(isinstance(instance["RELATION-CHILD"][0]._value, Identifier))
        self.assertFalse(isinstance(instance["ATTRIBUTE"][0]._value, Identifier))
        self.assertTrue(isinstance(instance["ONTOLOGY-SLOT"][0]._value, Identifier))
        self.assertFalse(isinstance(instance["EXTRA-ONTOLOGICAL"][0]._value, Identifier))
        self.assertFalse(isinstance(instance["SECOND-ORDER-PROPERTY"][0]._value, Identifier))

    def test_tmr_imported_maps_unknown_identifiers_to_ontology(self):
        self.ontology.register("RELATION", isa="PROPERTY")
        self.ontology.register("MADE-OF", isa="RELATION")

        r = self.load_resource("tests.resources", "DemoMay2018_Analyses.json", parse_json=True)
        tmr = self.n.register(TMR(r[8], self.ontology))

        self.assertTrue(tmr["BRACKET-1"]["MADE-OF"][0]._value.graph == "ONT")

    def test_tmr_imported_collapses_numbered_properties(self):
        r = self.load_resource("tests.resources", "DemoMay2018_Analyses.json", parse_json=True)
        analysis = r[8]
        _tmr = analysis["tmr"][0]["results"][0]["TMR"]

        self.assertTrue("INSTRUMENT" in _tmr["FASTEN-1"])
        self.assertEqual("SCREW-1", _tmr["FASTEN-1"]["INSTRUMENT"])
        self.assertTrue("INSTRUMENT-1" in _tmr["FASTEN-1"])
        self.assertEqual("SCREWDRIVER-1", _tmr["FASTEN-1"]["INSTRUMENT-1"])

        tmr = self.n.register(TMR(analysis, self.ontology))
        self.assertTrue("INSTRUMENT" in tmr["FASTEN-1"])
        self.assertFalse("INSTRUMENT-1" in tmr["FASTEN-1"])
        self.assertEqual(2, len(tmr["FASTEN-1"]["INSTRUMENT"]))
        self.assertTrue(tmr["FASTEN-1"]["INSTRUMENT"] == _tmr["FASTEN-1"]["INSTRUMENT"])
        self.assertTrue(tmr["FASTEN-1"]["INSTRUMENT"] == _tmr["FASTEN-1"]["INSTRUMENT-1"])
