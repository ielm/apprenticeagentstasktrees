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

        self.assertTrue(tmr["OBJECT-1"] ^ "ONT.OBJECT")
        self.assertFalse(tmr["OBJECT-1"] ^ "ONT.EVENT")

        self.assertTrue(tmr["EVENT-1"] ^ "ONT.EVENT")
        self.assertFalse(tmr["EVENT-1"] ^ "ONT.OBJECT")

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

    def test_tmr_is_action_from_request(self):
        self.ontology.register("REQUEST-ACTION", isa="EVENT")

        tmr = self.n.register(TMR.new("ONT"))

        self.assertFalse(tmr.is_action())

        request = tmr.register("REQUEST-ACTION.1", isa="ONT.REQUEST-ACTION")
        human = tmr.register("HUMAN.1", isa="ONT.HUMAN")
        robot = tmr.register("ROBOT.1", isa="ONT.ROBOT")

        self.assertFalse(tmr.is_action())

        request["AGENT"] = human
        request["BENEFICIARY"] = robot

        self.assertTrue(tmr.is_action())

    def test_tmr_is_action_from_present_physical_event(self):
        self.ontology.register("PHYSICAL-EVENT", isa="EVENT")

        tmr = self.n.register(TMR.new("ONT"))

        self.assertFalse(tmr.is_action())

        event = tmr.register("PHYSICAL-EVENT.1", isa="ONT.PHYSICAL-EVENT")
        human = tmr.register("HUMAN.1", isa="ONT.HUMAN")

        self.assertFalse(tmr.is_action())

        event["AGENT"] = human
        event["TIME"] = ["FIND-ANCHOR-TIME"]

        self.assertTrue(tmr.is_action())

    def test_tmr_find_recursive_themes_of_main_event(self):
        self.ontology.register("OTHER", isa="ALL")

        tmr = self.n.register(TMR.new("ONT"))

        self.assertEquals([], tmr.find_themes())

        event = tmr.register("EVENT.1", isa="ONT.EVENT")
        t1 = tmr.register("T.1", isa="ONT.OBJECT")
        t2 = tmr.register("T.2", isa="ONT.EVENT")
        t3 = tmr.register("T.3", isa="ONT.OTHER")

        self.assertEquals([], tmr.find_themes())

        event["THEME"] = [t1, t2]
        t1["THEME"] = t3

        self.assertEquals({"ONT.OBJECT", "ONT.EVENT", "ONT.OTHER"}, tmr.find_themes())

    def test_tmr_find_by_concept(self):
        self.ontology.register("PHYSICAL-OBJECT", isa="OBJECT")

        tmr = self.n.register(TMR.new("ONT"))

        self.assertEquals([], tmr.find_by_concept("ONT.OBJECT"))

        event = tmr.register("EVENT.1", isa="ONT.EVENT")
        o1 = tmr.register("O.1", isa="ONT.OBJECT")
        o2 = tmr.register("O.2", isa="ONT.OBJECT")
        o3 = tmr.register("O.3", isa="ONT.PHYSICAL-OBJECT")

        self.assertEquals([o1, o2, o3], tmr.find_by_concept("ONT.OBJECT"))

    def test_tmr_has_same_main_event_compares_concepts(self):
        self.ontology.register("PHYSICAL-EVENT", isa="EVENT")

        tmr1 = self.n.register(TMR.new("ONT"))
        tmr2 = self.n.register(TMR.new("ONT"))

        self.assertFalse(tmr1.has_same_main_event(tmr2))

        event1 = tmr1.register("EVENT.1", isa="ONT.EVENT")
        event2 = tmr2.register("EVENT.2", isa="ONT.OTHER")

        self.assertFalse(tmr1.has_same_main_event(tmr2))

        event2["IS-A"] = "ONT.EVENT"

        self.assertTrue(tmr1.has_same_main_event(tmr2))

        event2["IS-A"] = "ONT.PHYSICAL-EVENT"

        self.assertFalse(tmr1.has_same_main_event(tmr2))

    def test_tmr_has_same_main_event_compares_agents(self):
        tmr1 = self.n.register(TMR.new("ONT"))
        tmr2 = self.n.register(TMR.new("ONT"))

        self.assertFalse(tmr1.has_same_main_event(tmr2))

        event1 = tmr1.register("EVENT.1", isa="ONT.EVENT")
        event2 = tmr2.register("EVENT.2", isa="ONT.EVENT")

        agent1 = tmr1.register("HUMAN.1", isa="ONT.OBJECT")
        agent2 = tmr2.register("HUMAN.2", isa="ONT.OBJECT")
        agent3 = tmr2.register("HUMAN.3", isa="ONT.OBJECT")

        self.assertTrue(tmr1.has_same_main_event(tmr2))

        event1["AGENT"] = agent1
        event2["AGENT"] = agent2
        self.assertTrue(tmr1.has_same_main_event(tmr2))

        event2["AGENT"] = agent3
        self.assertTrue(tmr1.has_same_main_event(tmr2))

    def test_tmr_has_same_main_event_compares_themes(self):
        tmr1 = self.n.register(TMR.new("ONT"))
        tmr2 = self.n.register(TMR.new("ONT"))

        self.assertFalse(tmr1.has_same_main_event(tmr2))

        event1 = tmr1.register("EVENT.1", isa="ONT.EVENT")
        event2 = tmr2.register("EVENT.2", isa="ONT.EVENT")

        theme1 = tmr1.register("HUMAN.1", isa="ONT.OBJECT")
        theme2 = tmr2.register("HUMAN.2", isa="ONT.OBJECT")
        theme3 = tmr2.register("HUMAN.3", isa="ONT.OBJECT")

        self.assertTrue(tmr1.has_same_main_event(tmr2))

        event1["THEME"] = theme1
        event2["THEME"] = theme2
        self.assertTrue(tmr1.has_same_main_event(tmr2))

        event2["THEME"] = theme3
        self.assertTrue(tmr1.has_same_main_event(tmr2))

    def test_tmr_has_same_main_event_compares_instruments(self):
        tmr1 = self.n.register(TMR.new("ONT"))
        tmr2 = self.n.register(TMR.new("ONT"))

        self.assertFalse(tmr1.has_same_main_event(tmr2))

        event1 = tmr1.register("EVENT.1", isa="ONT.EVENT")
        event2 = tmr2.register("EVENT.2", isa="ONT.EVENT")

        instrument1 = tmr1.register("HUMAN.1", isa="ONT.OBJECT")
        instrument2 = tmr2.register("HUMAN.2", isa="ONT.OBJECT")
        instrument3 = tmr2.register("HUMAN.3", isa="ONT.OBJECT")

        self.assertTrue(tmr1.has_same_main_event(tmr2))

        event1["INSTRUMENT"] = instrument1
        event2["INSTRUMENT"] = instrument2
        self.assertTrue(tmr1.has_same_main_event(tmr2))

        event2["INSTRUMENT"] = instrument3
        self.assertTrue(tmr1.has_same_main_event(tmr2))
