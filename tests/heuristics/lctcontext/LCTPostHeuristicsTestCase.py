from backend.agent import Agent
from backend.contexts.LCTContext import LCTContext
from backend.heuristics.fr_heuristics import FRResolveHumanAndRobotAsSingletonsHeuristic
from backend.heuristics.lctcontex.lct_post_heuristics import *
from backend.models.graph import Graph, Network
from backend.models.tmr import TMR
from tests.ApprenticeAgentsTestCase import ApprenticeAgentsTestCase


class LCTPostHeuristicsTestCase(ApprenticeAgentsTestCase):

    @classmethod
    def setUpClass(cls):
        pass  # Do not load the usual ontology

    def setUp(self):
        self.n = Network()

        self.ontology = self.n.register(Graph("ONT"))

        self.ontology.register("ALL")
        self.ontology.register("SET", isa="ONT.ALL")
        self.ontology.register("OBJECT", isa="ONT.ALL")
        self.ontology.register("EVENT", isa="ONT.ALL")
        self.ontology.register("PROPERTY", isa="ONT.ALL")

        self.ontology.register("HUMAN", isa="ONT.OBJECT")
        self.ontology.register("ROBOT", isa="ONT.OBJECT")

        self.ontology.register("ASSEMBLE", isa="ONT.EVENT")
        self.ontology.register("BUILD", isa="ONT.EVENT")
        self.ontology.register("FASTEN", isa="ONT.EVENT")

    def test_IdentifyPreconditionsUnderstandingProcessor(self):

        self.ontology.register("RELATION", isa="ONT.PROPERTY")
        self.ontology.register("AGENT", isa="ONT.RELATION")

        def setup():
            agent = Agent(ontology=self.ontology)
            context = LCTContext(agent)

            agent.wo_memory.heuristics = [FRResolveHumanAndRobotAsSingletonsHeuristic]

            frevent = agent.wo_memory.register("EVENT", isa="ONT.EVENT")
            fragent = agent.wo_memory.register("HUMAN", isa="ONT.HUMAN")
            frevent[LCTContext.LEARNING] = True
            frevent["AGENT"] = fragent

            tmr = agent.register(TMR.new(self.ontology))
            event = tmr.register("EVENT", isa="ONT.EVENT")
            purpose = tmr.register("EVENT", isa="ONT.EVENT")
            event["PURPOSE"] = purpose
            purpose["AGENT"] = "HUMAN"

            agent.wo_memory.learn_tmr(tmr)

            return agent, context, tmr

        effect = False
        class MockedHeuristic(IdentifyPreconditionsUnderstandingProcessor):
            def halt_siblings(self):
                nonlocal effect
                effect = True

        # If matched, the heuristic adds the input event as a PRECONDITION.
        agent, context, tmr = setup()
        MockedHeuristic(context).process(agent, tmr)
        self.assertTrue(agent.wo_memory["EVENT.1"]["PRECONDITION"] == agent.wo_memory["EVENT.2"])
        self.assertTrue(effect)

        # Fails if tmr is prefix.
        agent, context, tmr = setup()
        tmr["EVENT.1"]["TIME"] = [[">", "FIND-ANCHOR-TIME"]]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

        # Fails if tmr is postfix.
        agent, context, tmr = setup()
        tmr["EVENT.1"]["TIME"] = [["<", "FIND-ANCHOR-TIME"]]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

        # Fails if the event has no PURPOSE.
        agent, context, tmr = setup()
        del tmr["EVENT.1"]["PURPOSE"]
        del agent.wo_memory["EVENT.2"]["PURPOSE"]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

        # Fails if there is no LEARNING event.
        agent, context, tmr = setup()
        del agent.wo_memory["EVENT.1"][LCTContext.LEARNING]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

        # Fails if case roles do not match between PURPOSE and LEARNING events.
        agent, context, tmr = setup()
        agent.wo_memory["EVENT.3"]["AGENT"] = ["ONT.ROBOT"]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

    def test_HandleRequestedActionsUnderstandingProcessor(self):

        self.ontology.register("REQUEST-ACTION", isa="ONT.EVENT")

        def setup():
            agent = Agent(ontology=self.ontology)
            context = LCTContext(agent)

            agent.wo_memory.heuristics = [FRResolveHumanAndRobotAsSingletonsHeuristic]

            frevent = agent.wo_memory.register("EVENT", isa="ONT.EVENT")
            frevent[LCTContext.LEARNING] = True
            frevent[LCTContext.CURRENT] = True

            tmr = agent.register(TMR.new(self.ontology))
            event = tmr.register("EVENT", isa="ONT.REQUEST-ACTION")
            theme = tmr.register("EVENT", isa="ONT.EVENT")
            event["BENEFICIARY"] = "ROBOT"
            event["THEME"] = theme

            agent.wo_memory.learn_tmr(tmr)

            return agent, context, tmr

        effect = False
        class MockedHeuristic(HandleRequestedActionsUnderstandingProcessor):
            def halt_siblings(self):
                nonlocal effect
                effect = True

        # If matched, the heuristic adds the input event's THEME as a HAS-EVENT-AS-PART.
        agent, context, tmr = setup()
        MockedHeuristic(context).process(agent, tmr)
        self.assertTrue(agent.wo_memory["EVENT.1"]["HAS-EVENT-AS-PART"] == agent.wo_memory["EVENT.2"])
        self.assertTrue(effect)

        # Fails if tmr is prefix.
        agent, context, tmr = setup()
        tmr["EVENT.1"]["TIME"] = [[">", "FIND-ANCHOR-TIME"]]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

        # Fails if tmr is postfix.
        agent, context, tmr = setup()
        tmr["EVENT.1"]["TIME"] = [["<", "FIND-ANCHOR-TIME"]]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

        # Fails if the main event is not a REQUEST-ACTION.
        agent, context, tmr = setup()
        tmr["EVENT.1"]["INSTANCE-OF"] = "ONT.EVENT"
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

        # Fails if the robot is not the BENEFICIARY.
        agent, context, tmr = setup()
        del tmr["EVENT.1"]["BENEFICIARY"]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

    def test_HandleCurrentActionUnderstandingProcessor(self):

        def setup():
            agent = Agent(ontology=self.ontology)
            context = LCTContext(agent)

            agent.wo_memory.heuristics = [FRResolveHumanAndRobotAsSingletonsHeuristic]

            frevent = agent.wo_memory.register("EVENT", isa="ONT.EVENT")
            frevent[LCTContext.LEARNING] = True
            frevent[LCTContext.CURRENT] = True

            tmr = agent.register(TMR.new(self.ontology))
            event = tmr.register("EVENT", isa="ONT.EVENT")

            agent.wo_memory.learn_tmr(tmr)

            return agent, context, tmr

        effect = False

        class MockedHeuristic(HandleCurrentActionUnderstandingProcessor):
            def halt_siblings(self):
                nonlocal effect
                effect = True

        # If matched, the heuristic adds the input event as a HAS-EVENT-AS-PART.
        agent, context, tmr = setup()
        MockedHeuristic(context).process(agent, tmr)
        self.assertTrue(agent.wo_memory["EVENT.1"]["HAS-EVENT-AS-PART"] == agent.wo_memory["EVENT.2"])
        self.assertTrue(effect)

        # Fails if tmr is prefix.
        agent, context, tmr = setup()
        tmr["EVENT.1"]["TIME"] = [[">", "FIND-ANCHOR-TIME"]]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

        # Fails if tmr is postfix.
        agent, context, tmr = setup()
        tmr["EVENT.1"]["TIME"] = [["<", "FIND-ANCHOR-TIME"]]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

    def test_RecognizeSubEventsUnderstandingProcessor(self):

        def setup():
            agent = Agent(ontology=self.ontology)
            context = LCTContext(agent)

            agent.wo_memory.heuristics = [FRResolveHumanAndRobotAsSingletonsHeuristic]

            frevent = agent.wo_memory.register("EVENT", isa="ONT.EVENT")
            frevent[LCTContext.LEARNING] = True
            frevent[LCTContext.CURRENT] = True

            tmr = agent.register(TMR.new(self.ontology))
            event = tmr.register("EVENT", isa="ONT.EVENT")
            event["TIME"] = [[">", "FIND-ANCHOR-TIME"]]

            agent.wo_memory.learn_tmr(tmr)

            return agent, context, tmr

        effect = False

        class MockedHeuristic(RecognizeSubEventsUnderstandingProcessor):
            def halt_siblings(self):
                nonlocal effect
                effect = True

        # If matched, the heuristic adds the input event as a HAS-EVENT-AS-PART, and it is marked as LEARNING / CURRENT.
        agent, context, tmr = setup()
        MockedHeuristic(context).process(agent, tmr)
        self.assertTrue(agent.wo_memory["EVENT.1"]["HAS-EVENT-AS-PART"] == agent.wo_memory["EVENT.2"])
        self.assertTrue(agent.wo_memory["EVENT.1"][LCTContext.LEARNING] == True)
        self.assertTrue(agent.wo_memory["EVENT.1"][LCTContext.CURRENT] == False)
        self.assertTrue(agent.wo_memory["EVENT.2"][LCTContext.LEARNING] == True)
        self.assertTrue(agent.wo_memory["EVENT.2"][LCTContext.CURRENT] == True)
        self.assertTrue(effect)

        # Fails if tmr is not prefix.
        agent, context, tmr = setup()
        del tmr["EVENT.1"]["TIME"]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

        # Fails if tmr is postfix.
        agent, context, tmr = setup()
        tmr["EVENT.1"]["TIME"] = [["<", "FIND-ANCHOR-TIME"]]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

    def test_IdentifyClosingOfUnknownTaskUnderstandingProcessor(self):

        self.ontology.register("EVENT-A", isa="ONT.EVENT")
        self.ontology.register("EVENT-B", isa="ONT.EVENT")

        def setup():
            agent = Agent(ontology=self.ontology)
            context = LCTContext(agent)

            agent.wo_memory.heuristics = [FRResolveHumanAndRobotAsSingletonsHeuristic]

            frevent = agent.wo_memory.register("EVENT", isa="ONT.EVENT-A")
            child1 = agent.wo_memory.register("EVENT", isa="ONT.EVENT")
            child2 = agent.wo_memory.register("EVENT", isa="ONT.EVENT")
            child3 = agent.wo_memory.register("EVENT", isa="ONT.EVENT")
            frtheme = agent.wo_memory.register("EVENT", isa="ONT.EVENT-A")

            frevent[LCTContext.LEARNING] = True
            frevent[LCTContext.CURRENT] = True
            frevent["HAS-EVENT-AS-PART"] = [child1, child2]
            child2["HAS-EVENT-AS-PART"] = [child3]
            frevent["THEME"] = frtheme

            tmr = agent.register(TMR.new(self.ontology))
            event = tmr.register("EVENT", isa="ONT.EVENT-B")
            theme = tmr.register("EVENT", isa="ONT.EVENT-B")
            event["TIME"] = [["<", "FIND-ANCHOR-TIME"]]
            event["THEME"] = theme

            agent.wo_memory.learn_tmr(tmr)

            return agent, context, tmr

        class MockedHeuristic(IdentifyClosingOfUnknownTaskUnderstandingProcessor):
            pass

        # If matched, the heuristic adds the input event as a HAS-EVENT-AS-PART, and moves existing non-complex events
        # underneath itself.
        agent, context, tmr = setup()
        MockedHeuristic(context).process(agent, tmr)
        self.assertTrue(agent.wo_memory["EVENT.1"]["HAS-EVENT-AS-PART"] == agent.wo_memory["EVENT.3"])
        self.assertTrue(agent.wo_memory["EVENT.1"]["HAS-EVENT-AS-PART"] == agent.wo_memory["EVENT-B.1"])
        self.assertTrue(agent.wo_memory["EVENT.3"]["HAS-EVENT-AS-PART"] == agent.wo_memory["EVENT.4"])
        self.assertTrue(agent.wo_memory["EVENT-B.1"]["HAS-EVENT-AS-PART"] == agent.wo_memory["EVENT.2"])
        self.assertTrue(agent.wo_memory["EVENT-B.1"][LCTContext.LEARNED] == True)

        # Fails if tmr is prefix.
        agent, context, tmr = setup()
        tmr["EVENT.1"]["TIME"] = [[">", "FIND-ANCHOR-TIME"]]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

        # Fails if tmr is not postfix.
        agent, context, tmr = setup()
        del tmr["EVENT.1"]["TIME"]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

        # Fails if there is no LEARNING event.
        agent, context, tmr = setup()
        agent.wo_memory["EVENT.1"][LCTContext.LEARNING] = False
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

        # Fails if there is the LEARNING event is the same as the input event and they share THEME concepts.
        agent, context, tmr = setup()
        agent.wo_memory["EVENT.1"]["INSTANCE-OF"] = ["ONT.EVENT-B"]
        agent.wo_memory["EVENT.5"]["INSTANCE-OF"] = ["ONT.EVENT-B"]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

    def test_RecognizePartsOfObjectUnderstandingProcessor(self):

        def setup():
            agent = Agent(ontology=self.ontology)
            context = LCTContext(agent)

            agent.wo_memory.heuristics = [FRResolveHumanAndRobotAsSingletonsHeuristic]

            frevent = agent.wo_memory.register("EVENT", isa="ONT.BUILD")
            frtheme = agent.wo_memory.register("OBJECT", isa="ONT.OBJECT")
            frevent[LCTContext.LEARNING] = True
            frevent["THEME"] = frtheme

            tmr = agent.register(TMR.new(self.ontology))
            event = tmr.register("EVENT", isa="ONT.BUILD")
            theme = tmr.register("EVENT", isa="ONT.OBJECT")
            event[LCTContext.LEARNING] = True
            event["THEME"] = theme

            agent.wo_memory.learn_tmr(tmr)

            frevent[LCTContext.WAITING_ON] = agent.wo_memory["BUILD.1"]

            return agent, context, tmr

        class MockedHeuristic(RecognizePartsOfObjectUnderstandingProcessor):
            pass

        # If matched, the heuristic adds the input event's THEMEs (objects) as a HAS-OBJECT-AS-PART to the currently
        # LEARNING frame's theme (also an object)
        agent, context, tmr = setup()
        MockedHeuristic(context).process(agent, tmr)
        self.assertTrue(agent.wo_memory["OBJECT.1"]["HAS-OBJECT-AS-PART"] == agent.wo_memory["OBJECT.2"])

        # Fails if there are no "parts" (THEMEs or DESTINATIONs) to the input event.
        agent, context, tmr = setup()
        del tmr["EVENT.1"]["THEME"]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

        # Fails if the event is not flagged as LEARNING.
        agent, context, tmr = setup()
        agent.wo_memory["BUILD.1"][LCTContext.LEARNING] = False
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

        # Fails if the event is not an instance of BUILD.
        agent, context, tmr = setup()
        agent.wo_memory["BUILD.1"]["INSTANCE-OF"] = ["ONT.EVENT"]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

        # Fails if the event is not being WAITING-ON by another LEARNING event.
        agent, context, tmr = setup()
        del agent.wo_memory["EVENT.1"][LCTContext.WAITING_ON]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

        # Fails if the event WAITING-ON this event is not a BUILD.
        agent, context, tmr = setup()
        agent.wo_memory["EVENT.1"]["INSTANCE-OF"] = ["ONT.EVENT"]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

        # Fails if the event WAITING-ON this event has no THEME.
        agent, context, tmr = setup()
        del agent.wo_memory["EVENT.1"]["THEME"]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)