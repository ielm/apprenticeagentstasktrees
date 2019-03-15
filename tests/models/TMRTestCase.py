from backend.models.tmr import TMR, TMRFrame
from backend.utils.AtomicCounter import AtomicCounter
from ontograph import graph
from ontograph.Frame import Frame
from ontograph.Space import Space

from pkgutil import get_data
import json
import unittest


class TMRTestCase(unittest.TestCase):

    def setUp(self):
        super().setUp()
        graph.reset()
        TMR.counter = AtomicCounter()

        Frame("@ONT.ALL")
        Frame("@ONT.OBJECT").add_parent("@ONT.ALL")
        Frame("@ONT.EVENT").add_parent("@ONT.ALL")
        Frame("@ONT.PROPERTY").add_parent("@ONT.ALL")

    def load_resource(self, module: str, file: str, parse_json: bool=False):
        binary = get_data(module, file)

        if not parse_json:
            return str(binary)

        return json.loads(binary)

    def test_tmr_as_graph(self):
        tmr = TMR.from_contents()

        agent1 = Frame("@" + tmr.graph().name + ".AGENT.?")
        event1 = Frame("@" + tmr.graph().name + ".EVENT.?")
        theme1 = Frame("@" + tmr.graph().name + ".THEME.?")

        event1["AGENT"] = agent1
        event1["THEME"] = theme1

        self.assertEqual(agent1, event1["AGENT"][0])
        self.assertEqual(theme1, event1["THEME"][0])

    def test_tmr_loaded(self):
        Frame("@ONT.CHAIR").add_parent("@ONT.OBJECT")
        Frame("@ONT.RELATION").add_parent("@ONT.PROPERTY")
        Frame("@ONT.THEME").add_parent("@ONT.RELATION")
        Frame("@ONT.AGENT").add_parent("@ONT.RELATION")

        r = self.load_resource("tests.resources", "DemoMay2018_Analyses.json", parse_json=True)
        tmr = TMR.from_json(r[0])
        tmr = tmr.graph()

        self.assertEqual(Frame("@TMR#1.BUILD.1")["THEME"][0], Frame("@TMR#1.CHAIR.1"))
        self.assertTrue(Frame("@TMR#1.BUILD.1")["THEME"][0] ^ "@ONT.CHAIR")
        self.assertTrue(Frame("@TMR#1.BUILD.1")["AGENT"] == Frame("@TMR#1.SET.1"))
        self.assertTrue(Frame("@TMR#1.BUILD.1")["THEME"][0] ^ "@ONT.OBJECT")

    def test_tmr_is_event_or_object(self):
        tmr = TMR.from_contents()
        tmr = tmr.graph()

        o = Frame("@" + tmr.name + ".OBJECT.?").add_parent("@ONT.OBJECT")
        e = Frame("@" + tmr.name + ".EVENT.?").add_parent("@ONT.EVENT")

        self.assertTrue(o.isa("@ONT.OBJECT"))
        self.assertFalse(o.isa("@ONT.EVENT"))

        self.assertTrue(e.isa("@ONT.EVENT"))
        self.assertFalse(e.isa("@ONT.OBJECT"))

        self.assertTrue(o ^ "@ONT.OBJECT")
        self.assertFalse(o ^ "@ONT.EVENT")

        self.assertTrue(e ^ "@ONT.EVENT")
        self.assertFalse(e ^ "@ONT.OBJECT")

        self.assertTrue(TMRFrame("@" + tmr.name + ".OBJECT.1").is_object())
        self.assertFalse(TMRFrame("@" + tmr.name + ".OBJECT.1").is_event())

        self.assertTrue(TMRFrame("@" + tmr.name + ".EVENT.1").is_event())
        self.assertFalse(TMRFrame("@" + tmr.name + ".EVENT.1").is_object())

    def test_tmr_find_main_event(self):
        tmr = TMR.from_contents()

        object1 = Frame("@" + tmr.graph().name + ".OBJECT.1").add_parent("@ONT.OBJECT")
        event1 = Frame("@" + tmr.graph().name + ".EVENT.1").add_parent("@ONT.EVENT")

        self.assertEqual(event1, tmr.find_main_event())

    def test_tmr_find_main_event_with_purpose_of(self):
        tmr = TMR.from_contents()

        object1 = Frame("@" + tmr.graph().name + ".OBJECT.1").add_parent("@ONT.OBJECT")
        event1 = Frame("@" + tmr.graph().name + ".EVENT.1").add_parent("@ONT.EVENT")
        event2 = Frame("@" + tmr.graph().name + ".EVENT.2").add_parent("@ONT.EVENT")
        event3 = Frame("@" + tmr.graph().name + ".EVENT.3").add_parent("@ONT.EVENT")

        event1["PURPOSE-OF"] = event2
        event2["PURPOSE-OF"] = event3

        self.assertEqual(event3, tmr.find_main_event())

    def test_tmr_is_prefix(self):
        tmr = TMR.from_contents()

        event1 = Frame("@" + tmr.graph().name + ".EVENT.1").add_parent("@ONT.EVENT")

        self.assertFalse(tmr.is_prefix())

        event1["TIME"] = [[">", "FIND-ANCHOR-TIME"]]

        self.assertTrue(tmr.is_prefix())

    def test_tmr_is_postfix(self):
        tmr = TMR.from_contents()

        event1 = Frame("@" + tmr.graph().name + ".EVENT.1").add_parent("@ONT.EVENT")

        self.assertFalse(tmr.is_postfix())

        event1["TIME"] = [["<", "FIND-ANCHOR-TIME"]]

        self.assertTrue(tmr.is_postfix())

    def test_tmr_is_postfix_generic_event(self):
        Frame("@ONT.ASPECT").add_parent("@ONT.ALL")

        tmr = TMR.from_contents()

        aspect1 = Frame("@" + tmr.graph().name + ".ASPECT.1").add_parent("@ONT.ASPECT")
        event1 = Frame("@" + tmr.graph().name + ".EVENT.?").add_parent("@ONT.EVENT")

        self.assertFalse(tmr.is_postfix())

        aspect1["PHASE"] = "END"
        aspect1["SCOPE"] = event1

        self.assertTrue(tmr.is_postfix())

    def test_tmr_find_by_concept(self):
        Frame("@ONT.PHYSICAL-OBJECT").add_parent("@ONT.OBJECT")

        tmr = TMR.from_contents()

        self.assertEqual([], tmr.find_by_concept("@ONT.OBJECT"))

        event1 = Frame("@" + tmr.graph().name + ".EVENT.1").add_parent("@ONT.EVENT")
        o1 = Frame("@" + tmr.graph().name + ".O.1").add_parent("@ONT.OBJECT")
        o2 = Frame("@" + tmr.graph().name + ".O.2").add_parent("@ONT.OBJECT")
        o3 = Frame("@" + tmr.graph().name + ".O.3").add_parent("@ONT.PHYSICAL-OBJECT")

        results = tmr.find_by_concept("@ONT.OBJECT")
        self.assertEqual(3, len(results))
        self.assertIn(o1, results)
        self.assertIn(o2, results)
        self.assertIn(o3, results)

    def test_render(self):
        tmr = Frame("@TEST.TMR")

        self.assertEqual("@TEST.TMR", TMR(tmr).render())

        tmr["SENTENCE"] = "Test sentence."

        self.assertEqual("Test sentence.", TMR(tmr).render())


class TMRFrameTestCase(unittest.TestCase):

    def setUp(self):
        super().setUp()
        graph.reset()

        # self.n = Network()
        # self.n.register("INPUTS")

        # self.ontology = self.n.register("ONT")
        # self.ontology.register("ALL")
        # self.ontology.register("OBJECT", isa="ALL")
        # self.ontology.register("EVENT", isa="ALL")
        # self.ontology.register("PROPERTY", isa="ALL")

        Frame("@ONT.ALL")
        Frame("@ONT.OBJECT").add_parent("@ONT.ALL")
        Frame("@ONT.EVENT").add_parent("@ONT.ALL")
        Frame("@ONT.PROPERTY").add_parent("@ONT.ALL")

    def load_resource(self, module: str, file: str, parse_json: bool=False):
        binary = get_data(module, file)

        if not parse_json:
            return str(binary)

        return json.loads(binary)

    def test_tmr_instance_maps_relations_to_identifiers(self):
        Frame("@ONT.RELATION").add_parent("@ONT.PROPERTY")
        Frame("@ONT.ATTRIBUTE").add_parent("@ONT.PROPERTY")
        Frame("@ONT.ONTOLOGY-SLOT").add_parent("@ONT.PROPERTY")
        Frame("@ONT.EXTRA-ONTOLOGICAL").add_parent("@ONT.PROPERTY")
        Frame("@ONT.SECOND-ORDER-PROPERTY").add_parent("@ONT.PROPERTY")

        Frame("@ONT.RELATION-CHILD").add_parent("@ONT.RELATION")

        properties = {
            "RELATION": "TMR.THING.1",
            "RELATION-CHILD": "TMR.THING.1",
            "ATTRIBUTE": "TMR.THING.1",
            "ONTOLOGY-SLOT": "TMR.THING.1",
            "EXTRA-ONTOLOGICAL": "TMR.THING.1",
            "SECOND-ORDER-PROPERTY": "TMR.THING.1",
        }

        instance = TMRFrame.parse("NAME", Space("TMR"), {}, properties=properties)

        self.assertTrue(isinstance(instance["RELATION"][0], Frame))
        self.assertTrue(isinstance(instance["RELATION-CHILD"][0], Frame))
        self.assertFalse(isinstance(instance["ATTRIBUTE"][0], Frame))
        self.assertTrue(isinstance(instance["ONTOLOGY-SLOT"][0], Frame))
        self.assertFalse(isinstance(instance["EXTRA-ONTOLOGICAL"][0], Frame))
        self.assertFalse(isinstance(instance["SECOND-ORDER-PROPERTY"][0], Frame))

    def test_tmr_imported_maps_unknown_identifiers_to_ontology(self):
        Frame("@ONT.RELATION").add_parent("@ONT.PROPERTY")
        Frame("@ONT.MADE-OF").add_parent("@ONT.RELATION")

        r = self.load_resource("tests.resources", "DemoMay2018_Analyses.json", parse_json=True)
        tmr = TMR.from_json(r[8])
        tmr = tmr.graph()

        self.assertTrue(Frame("@" + tmr.name + ".BRACKET.1")["MADE-OF"][0].space() == "ONT")

    def test_tmr_imported_collapses_numbered_properties(self):
        r = self.load_resource("tests.resources", "DemoMay2018_Analyses.json", parse_json=True)
        analysis: dict = r[8]
        _tmr = analysis["tmr"][0]["results"][0]["TMR"]

        self.assertTrue("INSTRUMENT" in _tmr["FASTEN-1"])
        self.assertEqual("SCREW-1", _tmr["FASTEN-1"]["INSTRUMENT"])
        self.assertTrue("INSTRUMENT-1" in _tmr["FASTEN-1"])
        self.assertEqual("SCREWDRIVER-1", _tmr["FASTEN-1"]["INSTRUMENT-1"])

        tmr = TMR.from_json(r[8])
        tmr = tmr.graph()
        self.assertTrue("INSTRUMENT" in Frame("@" + tmr.name + ".FASTEN.1"))
        self.assertFalse("INSTRUMENT.1" in Frame("@" + tmr.name + ".FASTEN.1"))
        self.assertEqual(2, len(Frame("@" + tmr.name + ".FASTEN.1")["INSTRUMENT"]))
        self.assertTrue(Frame("@" + tmr.name + ".FASTEN.1")["INSTRUMENT"] == _tmr["FASTEN-1"]["INSTRUMENT"])
        self.assertTrue(Frame("@" + tmr.name + ".FASTEN.1")["INSTRUMENT"] == _tmr["FASTEN-1"]["INSTRUMENT-1"])

    def test_tmr_imported_assigns_ontology_to_unspecified_identifiers(self):
        Frame("@ONT.RELATION").add_parent("@ONT.PROPERTY")
        Frame("@ONT.AGENT").add_parent("@ONT.RELATION")

        r = self.load_resource("tests.resources", "DemoMay2018_Analyses.json", parse_json=True)
        analysis: dict = r[8]
        _tmr = analysis["tmr"][0]["results"][0]["TMR"]

        self.assertTrue("HUMAN" in _tmr["FASTEN-1"]["AGENT"])

        tmr = TMR.from_json(r[8])
        tmr = tmr.graph()
        self.assertTrue(isinstance(Frame("@" + tmr.name + ".FASTEN.1")["AGENT"][0], Frame))
        self.assertEqual(Frame("@" + tmr.name + ".FASTEN.1")["AGENT"][0].space(), Space("ONT"))

    def test_tmr_instance_uses_instance_of(self):
        tmr = TMR.from_contents()
        tmr = tmr.graph()
        instance = TMRFrame("@" + tmr.name + ".NAME").add_parent("@ONT.OBJECT")

        self.assertIn("INSTANCE-OF", instance)
        self.assertNotIn("IS-A", instance)
        self.assertTrue(instance ^ "@ONT.OBJECT")
        self.assertTrue(instance.is_object())
        self.assertFalse(instance.is_event())
