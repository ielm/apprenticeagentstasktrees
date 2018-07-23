from backend.agent import Agent
from backend.contexts.LCTContext import LCTContext
from backend.heuristics.lctcontex.lct_pre_heuristics import *
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

    def test_IdentifyClosingOfKnownTaskAgendaProcessor(self):
        agent = Agent(ontology=self.ontology)
        context = LCTContext(agent)

        event = agent.wo_memory.register("EVENT", isa="ONT.EVENT")
        event[LCTContext.LEARNING] = True
        event[LCTContext.CURRENT] = True

        tmr = self.n.register(TMR.new(self.ontology))
        event1 = tmr.register("EVENT.1", isa="ONT.EVENT")
        event1["TIME"] = [["<", "FIND-ANCHOR-TIME"]]

        IdentifyClosingOfKnownTaskAgendaProcessor(context).process(agent, tmr)

        self.assertTrue(LCTContext.LEARNING not in event)
        self.assertTrue(LCTContext.CURRENT not in event)
        self.assertEqual(event[LCTContext.LEARNED], True)

    def test_IdentifyCompletedTaskAgendaProcessor(self):

        def setup():
            agent = Agent(ontology=self.ontology)
            context = LCTContext(agent)

            tmr = self.n.register(TMR.new(self.ontology))
            event1 = tmr.register("EVENT", isa="ONT.EVENT")
            event1["TIME"] = [["<", "FIND-ANCHOR-TIME"]]

            event = agent.wo_memory.register("EVENT", isa="ONT.EVENT")
            event[LCTContext.LEARNED] = True

            return agent, context, tmr

        # If matched, the heuristic affects LT and WO memory.
        agent, context, tmr = setup()
        IdentifyCompletedTaskAgendaProcessor(context).process(agent, tmr)
        self.assertEqual(0, len(agent.wo_memory))
        self.assertTrue(len(agent.lt_memory) > 0)

        # Fail if the TMR is not in postfix.
        agent, context, tmr = setup()
        tmr["EVENT.1"]["TIME"] = [[">", "FIND-ANCHOR-TIME"]]
        with self.assertRaises(HeuristicException):
            IdentifyCompletedTaskAgendaProcessor(context)._logic(agent, tmr)

        # Fail if there is no LEARNED event.
        agent, context, tmr = setup()
        agent.wo_memory["EVENT.1"][LCTContext.LEARNED] = False
        with self.assertRaises(HeuristicException):
            IdentifyCompletedTaskAgendaProcessor(context)._logic(agent, tmr)

        # Fail if there is any LEARNING event.
        agent, context, tmr = setup()
        learning = agent.wo_memory.register("EVENT", isa="ONT.EVENT")
        learning[LCTContext.LEARNING] = True
        with self.assertRaises(HeuristicException):
            IdentifyCompletedTaskAgendaProcessor(context)._logic(agent, tmr)