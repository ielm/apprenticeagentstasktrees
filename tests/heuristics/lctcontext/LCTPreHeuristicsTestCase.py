from backend.agent import Agent
from backend.contexts.LCTContext import LCTContext
from backend.heuristics.lctcontext.lct_pre_heuristics import *
from backend.models.graph import Graph, Network
from backend.models.tmr import TMR
from tests.ApprenticeAgentsTestCase import ApprenticeAgentsTestCase


class LCTPreHeuristicsTestCase(ApprenticeAgentsTestCase):

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

        self.ontology.register("HUMAN", isa="ONT.OBJECT")
        self.ontology.register("ROBOT", isa="ONT.OBJECT")

        self.ontology.register("ASSEMBLE", isa="ONT.EVENT")
        self.ontology.register("BUILD", isa="ONT.EVENT")
        self.ontology.register("FASTEN", isa="ONT.EVENT")

    def test_IdentifyClosingOfKnownTaskUnderstandingProcessor(self):
        agent = Agent(ontology=self.ontology)
        context = LCTContext(agent)

        event = agent.wo_memory.register("EVENT", isa="ONT.EVENT")
        event[LCTContext.LEARNING] = True
        event[LCTContext.CURRENT] = True

        tmr = self.n.register(TMR.new(self.ontology))
        event1 = tmr.register("EVENT.1", isa="ONT.EVENT")
        event1["TIME"] = [["<", "FIND-ANCHOR-TIME"]]

        IdentifyClosingOfKnownTaskUnderstandingProcessor(context).process(agent, tmr)

        self.assertTrue(LCTContext.LEARNING not in event)
        self.assertTrue(LCTContext.CURRENT not in event)
        self.assertEqual(event[LCTContext.LEARNED], True)

    def test_IdentifyCompletedTaskUnderstandingProcessor(self):

        def setup():
            agent = Agent(ontology=self.ontology)
            context = LCTContext(agent)

            tmr = agent.register(TMR.new(self.ontology))
            event1 = tmr.register("EVENT", isa="ONT.EVENT")
            event1["TIME"] = [["<", "FIND-ANCHOR-TIME"]]

            event = agent.wo_memory.register("EVENT", isa="ONT.EVENT")
            event[LCTContext.LEARNED] = True

            return agent, context, tmr

        # If matched, the heuristic affects LT and WO memory.
        agent, context, tmr = setup()
        IdentifyCompletedTaskUnderstandingProcessor(context).process(agent, tmr)
        self.assertEqual(0, len(agent.wo_memory))
        self.assertTrue(len(agent.lt_memory) > 0)

        # Fail if the TMR is not in postfix.
        agent, context, tmr = setup()
        tmr["EVENT.1"]["TIME"] = [[">", "FIND-ANCHOR-TIME"]]
        with self.assertRaises(HeuristicException):
            IdentifyCompletedTaskUnderstandingProcessor(context)._logic(agent, tmr)

        # Fail if there is no LEARNED event.
        agent, context, tmr = setup()
        agent.wo_memory["EVENT.1"][LCTContext.LEARNED] = False
        with self.assertRaises(HeuristicException):
            IdentifyCompletedTaskUnderstandingProcessor(context)._logic(agent, tmr)

        # Fail if there is any LEARNING event.
        agent, context, tmr = setup()
        learning = agent.wo_memory.register("EVENT", isa="ONT.EVENT")
        learning[LCTContext.LEARNING] = True
        with self.assertRaises(HeuristicException):
            IdentifyCompletedTaskUnderstandingProcessor(context)._logic(agent, tmr)

    def test_IdentifyPreconditionSatisfyingActionsUnderstandingProcessor(self):
        self.ontology.register("REQUEST-ACTION", isa="ONT.EVENT")
        self.ontology.register("BIRD", isa="ONT.OBJECT")
        self.ontology.register("HUMAN", isa="ONT.OBJECT")

        def setup():
            agent = Agent(ontology=self.ontology)
            context = LCTContext(agent)

            previous = agent.register(TMR.new(self.ontology))
            prevevent = previous.register("EVENT", isa="ONT.EVENT")
            prevtheme = previous.register("OBJECT", isa="ONT.BIRD")
            prevevent["PURPOSE"] = 123  # Any purpose is sufficient
            prevevent["THEME"] = prevtheme

            tmr = agent.register(TMR.new(self.ontology))
            event1 = tmr.register("EVENT", isa="ONT.REQUEST-ACTION")
            theme1 = tmr.register("EVENT", isa="ONT.EVENT")
            object1 = tmr.register("OBJECT", isa="ONT.BIRD")

            event1["BENEFICIARY"] += "ROBOT"
            event1["THEME"] = theme1
            theme1["THEME"] = object1

            event = agent.wo_memory.register("EVENT", isa="ONT.EVENT")
            event[LCTContext.LEARNED] = True

            agent.input_memory = [previous, tmr]

            return agent, context, tmr, previous

        effect = False
        class MockedHeuristic(IdentifyPreconditionSatisfyingActionsUnderstandingProcessor):
            def reassign_siblings(self, siblings):
                if len(siblings) == 1 and isinstance(siblings[0], FRResolutionUnderstandingProcessor):
                    nonlocal effect
                    effect = True

        # If matched, the heuristic affects LT and WO memory.
        agent, context, tmr, previous = setup()
        MockedHeuristic(context).process(agent, tmr)
        self.assertTrue(effect)

        # Fail if the TMR is prefix.
        agent, context, tmr, previous = setup()
        tmr["EVENT.1"]["TIME"] = [[">", "FIND-ANCHOR-TIME"]]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

        # Fail if the TMR is postfix.
        agent, context, tmr, previous = setup()
        tmr["EVENT.1"]["TIME"] = [["<", "FIND-ANCHOR-TIME"]]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

        # Fail if there is no previous input (this is the first TMR).
        agent, context, tmr, previous = setup()
        agent.input_memory.remove(previous)
        del agent[previous._namespace]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

        # Fail if the main event is not a REQUEST-ACTION
        agent, context, tmr, previous = setup()
        tmr["EVENT.1"]["INSTANCE-OF"] = ["ONT.EVENT"]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

        # Fail if the main event does not have the ROBOT as the BENEFICIARY.
        agent, context, tmr, previous = setup()
        tmr["EVENT.1"]["BENEFICIARY"] = ["OTHER"]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

        # Fail if the previous TMR's event is prefix.
        agent, context, tmr, previous = setup()
        previous["EVENT.1"]["TIME"] = [[">", "FIND-ANCHOR-TIME"]]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

        # Fail if the previous TMR's event is postfix.
        agent, context, tmr, previous = setup()
        previous["EVENT.1"]["TIME"] = [["<", "FIND-ANCHOR-TIME"]]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

        # Fail if the previous TMR has no purpose.
        agent, context, tmr, previous = setup()
        del previous["EVENT.1"]["PURPOSE"]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)

        # Fail if this TMR's REQUEST-ACTION.THEME is not ontologically similar to the previous TMR's THEME.
        agent, context, tmr, previous = setup()
        tmr["OBJECT.1"]["INSTANCE-OF"] = ["ONT.HUMAN"]
        with self.assertRaises(HeuristicException):
            MockedHeuristic(context)._logic(agent, tmr)