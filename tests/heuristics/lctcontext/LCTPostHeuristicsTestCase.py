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

    def test_IdentifyPreconditionsAgendaProcessor(self):

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
        class MockedHeuristic(IdentifyPreconditionsAgendaProcessor):
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