from backend.models.graph import Graph, Network
from backend.models.tmr import TMR

import json
import os
import unittest


class TMRTestCase(unittest.TestCase):

    def setUp(self):
        super().setUp()

        self.n = Network()

        self.ontology = self.n.register("ONT")
        self.ontology.register("ALL")
        self.ontology.register("OBJECT", isa="ALL")
        self.ontology.register("EVENT", isa="ALL")

    def test_tmr_as_graph(self):
        tmr = TMR.new("ONT")

        agent1 = tmr.register("AGENT.1")
        event1 = tmr.register("EVENT.1")
        theme1 = tmr.register("THEME.1")

        event1["AGENT"] = "AGENT.1"
        event1["THEME"] = "THEME.1"

        self.assertEqual(agent1, event1["AGENT"][0].resolve())
        self.assertEqual(theme1, event1["THEME"][0].resolve())

    def test_tmr_loaded(self):
        self.ontology.register("CHAIR", isa="OBJECT")

        file = os.path.abspath(__package__) + "/../resources/DemoMay2018_Analyses.json"

        r = None
        with open(file) as f:
            r = json.load(f)

        tmr = self.n.register(TMR(r[0], "ONT"))

        self.assertEqual(tmr["BUILD-1"]["THEME"][0].resolve(), tmr["CHAIR-1"])
        self.assertTrue(tmr["BUILD-1"]["THEME"] ^ "ONT.CHAIR")
        self.assertTrue(tmr["BUILD-1"]["AGENT"] == "SET-1")
        self.assertTrue(tmr["BUILD-1"]["THEME"] ^ "ONT.OBJECT")

    def test_tmr_is_event_or_object(self):
        tmr = self.n.register(TMR.new("ONT"))

        tmr.register("OBJECT-1", isa="ONT.OBJECT")
        tmr.register("EVENT-1", isa="ONT.EVENT")

        self.assertTrue(tmr["OBJECT-1"].isa("ONT.OBJECT"))
        self.assertFalse(tmr["OBJECT-1"].isa("ONT.EVENT"))

        self.assertTrue(tmr["EVENT-1"].isa("ONT.EVENT"))
        self.assertFalse(tmr["EVENT-1"].isa("ONT.OBJECT"))

        self.assertTrue(tmr["OBJECT-1"].is_object())
        self.assertFalse(tmr["OBJECT-1"].is_event())

        self.assertTrue(tmr["EVENT-1"].is_event())
        self.assertFalse(tmr["EVENT-1"].is_object())

    def test_tmr_find_main_event(self):
        tmr = self.n.register(TMR.new("ONT"))

        object1 = tmr.register("OBJECT-1", isa="ONT.OBJECT")
        event1 = tmr.register("EVENT-1", isa="ONT.EVENT")

        self.assertEqual(event1, tmr.find_main_event())

    def test_tmr_find_main_event_with_purpose_of(self):
        tmr = self.n.register(TMR.new("ONT"))

        object1 = tmr.register("OBJECT-1", isa="ONT.OBJECT")
        event1 = tmr.register("EVENT-1", isa="ONT.EVENT")
        event2 = tmr.register("EVENT-2", isa="ONT.EVENT")
        event3 = tmr.register("EVENT-3", isa="ONT.EVENT")

        event1["PURPOSE-OF"] = event2
        event2["PURPOSE-OF"] = event3

        self.assertEqual(event3, tmr.find_main_event())

    def test_tmr_is_prefix(self):
        tmr = self.n.register(TMR.new("ONT"))

        event1 = tmr.register("EVENT-1", isa="ONT.EVENT")

        self.assertFalse(tmr.is_prefix())

        event1["TIME"] = [">", "FIND-ANCHOR-TIME"]

        self.assertTrue(tmr.is_prefix())

    def test_tmr_is_postfix(self):
        tmr = self.n.register(TMR.new("ONT"))

        event1 = tmr.register("EVENT-1", isa="ONT.EVENT")

        self.assertFalse(tmr.is_postfix())

        event1["TIME"] = ["<", "FIND-ANCHOR-TIME"]

        self.assertTrue(tmr.is_postfix())

    def test_tmr_is_postfix_generic_event(self):
        self.ontology.register("ASPECT", isa="ALL")

        tmr = self.n.register(TMR.new("ONT"))

        aspect1 = tmr.register("ASPECT-1", isa="ONT.ASPECT")
        event1 = tmr.register("EVENT-1", isa="ONT.EVENT")

        self.assertFalse(tmr.is_postfix())

        aspect1["PHASE"] = "END"
        aspect1["SCOPE"] = "EVENT-1"

        self.assertTrue(tmr.is_postfix())
