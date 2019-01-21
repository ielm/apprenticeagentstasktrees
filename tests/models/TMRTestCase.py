from backend.models.graph import Identifier, Network
from backend.models.tmr import TMR, TMRFrame

from pkgutil import get_data
import json
import unittest


class TMRTestCase(unittest.TestCase):

    def setUp(self):
        super().setUp()

        self.n = Network()
        self.n.register("INPUTS")

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
        tmr = TMR.from_contents(self.n, self.ontology)

        agent1 = tmr.graph(self.n).register("AGENT", generate_index=True)
        event1 = tmr.graph(self.n).register("EVENT", generate_index=True)
        theme1 = tmr.graph(self.n).register("THEME", generate_index=True)

        event1["AGENT"] = "AGENT.1"
        event1["THEME"] = "THEME.1"

        self.assertEqual(agent1, event1["AGENT"][0].resolve())
        self.assertEqual(theme1, event1["THEME"][0].resolve())

    def test_tmr_loaded(self):
        self.ontology.register("CHAIR", isa="OBJECT")
        self.ontology.register("RELATION", isa="PROPERTY")
        self.ontology.register("THEME", isa="RELATION")

        r = self.load_resource("tests.resources", "DemoMay2018_Analyses.json", parse_json=True)
        tmr = TMR.from_json(self.n, self.ontology, r[0])
        tmr = tmr.graph(self.n)

        self.assertEqual(tmr["BUILD.1"]["THEME"][0].resolve(), tmr["CHAIR.1"])
        self.assertTrue(tmr["BUILD.1"]["THEME"] ^ "ONT.CHAIR")
        self.assertTrue(tmr["BUILD.1"]["AGENT"] == "SET-1")
        self.assertTrue(tmr["BUILD.1"]["THEME"] ^ "ONT.OBJECT")

    def test_tmr_is_event_or_object(self):
        tmr = TMR.from_contents(self.n, self.ontology)
        tmr = tmr.graph(self.n)

        tmr.register("OBJECT", isa="ONT.OBJECT", generate_index=True)
        tmr.register("EVENT", isa="ONT.EVENT", generate_index=True)

        self.assertTrue(tmr["OBJECT.1"].isa("ONT.OBJECT"))
        self.assertFalse(tmr["OBJECT.1"].isa("ONT.EVENT"))

        self.assertTrue(tmr["EVENT.1"].isa("ONT.EVENT"))
        self.assertFalse(tmr["EVENT.1"].isa("ONT.OBJECT"))

        self.assertTrue(tmr["OBJECT.1"] ^ "ONT.OBJECT")
        self.assertFalse(tmr["OBJECT.1"] ^ "ONT.EVENT")

        self.assertTrue(tmr["EVENT.1"] ^ "ONT.EVENT")
        self.assertFalse(tmr["EVENT.1"] ^ "ONT.OBJECT")

        self.assertTrue(tmr["OBJECT.1"].is_object())
        self.assertFalse(tmr["OBJECT.1"].is_event())

        self.assertTrue(tmr["EVENT.1"].is_event())
        self.assertFalse(tmr["EVENT.1"].is_object())

    def test_tmr_find_main_event(self):
        tmr = TMR.from_contents(self.n, self.ontology)

        object1 = tmr.graph(self.n).register("OBJECT-1", isa="ONT.OBJECT")
        event1 = tmr.graph(self.n).register("EVENT-1", isa="ONT.EVENT")

        self.assertEqual(event1, tmr.find_main_event())

    def test_tmr_find_main_event_with_purpose_of(self):
        tmr = TMR.from_contents(self.n, self.ontology)

        object1 = tmr.graph(self.n).register("OBJECT-1", isa="ONT.OBJECT")
        event1 = tmr.graph(self.n).register("EVENT-1", isa="ONT.EVENT")
        event2 = tmr.graph(self.n).register("EVENT-2", isa="ONT.EVENT")
        event3 = tmr.graph(self.n).register("EVENT-3", isa="ONT.EVENT")

        event1["PURPOSE-OF"] = event2
        event2["PURPOSE-OF"] = event3

        self.assertEqual(event3, tmr.find_main_event())

    def test_tmr_is_prefix(self):
        tmr = TMR.from_contents(self.n, self.ontology)

        event1 = tmr.graph(self.n).register("EVENT-1", isa="ONT.EVENT")

        self.assertFalse(tmr.is_prefix())

        event1["TIME"] = [[">", "FIND-ANCHOR-TIME"]]

        self.assertTrue(tmr.is_prefix())

    def test_tmr_is_postfix(self):
        tmr = TMR.from_contents(self.n, self.ontology)

        event1 = tmr.graph(self.n).register("EVENT-1", isa="ONT.EVENT")

        self.assertFalse(tmr.is_postfix())

        event1["TIME"] = [["<", "FIND-ANCHOR-TIME"]]

        self.assertTrue(tmr.is_postfix())

    def test_tmr_is_postfix_generic_event(self):
        self.ontology.register("ASPECT", isa="ALL")

        tmr = TMR.from_contents(self.n, self.ontology)

        aspect1 = tmr.graph(self.n).register("ASPECT", isa="ONT.ASPECT", generate_index=True)
        event1 = tmr.graph(self.n).register("EVENT", isa="ONT.EVENT", generate_index=True)

        self.assertFalse(tmr.is_postfix())

        aspect1["PHASE"] = "END"
        aspect1["SCOPE"] = "EVENT.1"

        self.assertTrue(tmr.is_postfix())

    def test_tmr_find_by_concept(self):
        self.ontology.register("PHYSICAL-OBJECT", isa="OBJECT")

        tmr = TMR.from_contents(self.n, self.ontology)

        self.assertEqual([], tmr.find_by_concept("ONT.OBJECT"))

        event = tmr.graph(self.n).register("EVENT.1", isa="ONT.EVENT")
        o1 = tmr.graph(self.n).register("O.1", isa="ONT.OBJECT")
        o2 = tmr.graph(self.n).register("O.2", isa="ONT.OBJECT")
        o3 = tmr.graph(self.n).register("O.3", isa="ONT.PHYSICAL-OBJECT")

        self.assertEqual([o1, o2, o3], tmr.find_by_concept("ONT.OBJECT"))

    def test_render(self):
        from backend.models.graph import Literal
        
        g = self.n.register("TEST")
        tmr = g.register("TMR")

        self.assertEqual("TEST.TMR", TMR(tmr).render())

        tmr["SENTENCE"] = Literal("Test sentence.")

        self.assertEqual("Test sentence.", TMR(tmr).render())


class TMRFrameTestCase(unittest.TestCase):

    def setUp(self):
        super().setUp()

        self.n = Network()
        self.n.register("INPUTS")

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

        instance = TMRFrame.parse("NAME", properties=properties, ontology=self.ontology)

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
        tmr = TMR.from_json(self.n, self.ontology, r[8])
        tmr = tmr.graph(self.n)

        self.assertTrue(tmr["BRACKET.1"]["MADE-OF"][0]._value.graph == "ONT")

    def test_tmr_imported_collapses_numbered_properties(self):
        r = self.load_resource("tests.resources", "DemoMay2018_Analyses.json", parse_json=True)
        analysis: dict = r[8]
        _tmr = analysis["tmr"][0]["results"][0]["TMR"]

        self.assertTrue("INSTRUMENT" in _tmr["FASTEN-1"])
        self.assertEqual("SCREW-1", _tmr["FASTEN-1"]["INSTRUMENT"])
        self.assertTrue("INSTRUMENT-1" in _tmr["FASTEN-1"])
        self.assertEqual("SCREWDRIVER-1", _tmr["FASTEN-1"]["INSTRUMENT-1"])

        tmr = TMR.from_json(self.n, self.ontology, r[8])
        tmr = tmr.graph(self.n)
        self.assertTrue("INSTRUMENT" in tmr["FASTEN.1"])
        self.assertFalse("INSTRUMENT.1" in tmr["FASTEN.1"])
        self.assertEqual(2, len(tmr["FASTEN.1"]["INSTRUMENT"]))
        self.assertTrue(tmr["FASTEN.1"]["INSTRUMENT"] == _tmr["FASTEN-1"]["INSTRUMENT"])
        self.assertTrue(tmr["FASTEN.1"]["INSTRUMENT"] == _tmr["FASTEN-1"]["INSTRUMENT-1"])

    def test_tmr_imported_assigns_ontology_to_unspecified_identifiers(self):
        self.ontology.register("RELATION", isa="PROPERTY")
        self.ontology.register("AGENT", isa="RELATION")

        r = self.load_resource("tests.resources", "DemoMay2018_Analyses.json", parse_json=True)
        analysis: dict = r[8]
        _tmr = analysis["tmr"][0]["results"][0]["TMR"]

        self.assertTrue("HUMAN" in _tmr["FASTEN-1"]["AGENT"])

        tmr = TMR.from_json(self.n, self.ontology, r[8])
        tmr = tmr.graph(self.n)
        self.assertTrue(isinstance(tmr["FASTEN.1"]["AGENT"][0]._value, Identifier))
        self.assertEqual(tmr["FASTEN.1"]["AGENT"][0]._value.graph, self.ontology._namespace)

    def test_tmr_instance_uses_instance_of(self):
        tmr = TMR.from_contents(self.n, self.ontology)
        tmr = tmr.graph(self.n)
        instance: TMRFrame = tmr.register("NAME", isa="ONT.OBJECT")

        self.assertIn("INSTANCE-OF", instance)
        self.assertNotIn("IS-A", instance)
        self.assertTrue(instance ^ "ONT.OBJECT")
        self.assertTrue(instance.is_object())
        self.assertFalse(instance.is_event())
