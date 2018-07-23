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