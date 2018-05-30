from backend.agent import Agent
from backend.contexts.LCTContext import LCTContext
from backend.heuristics.lctcontex.lct_pre_heuristics import *
from backend.models.tmr import TMR
from backend.models.tmrinstance import TMRInstance
from backend.ontology import Ontology
from tests.ApprenticeAgentsTestCase import ApprenticeAgentsTestCase


class LCTPreHeuristicsTestCase(ApprenticeAgentsTestCase):

    @classmethod
    def setUpClass(cls):
        pass  # Do not load the usual ontology

    def setUp(self):
        Ontology.ontology = ApprenticeAgentsTestCase.TestOntology(include_t1=True)
        Ontology.ontology["FASTEN"] = {}
        Ontology.ontology["ASSEMBLE"] = {}
        Ontology.ontology["BUILD"] = {}

    def test_IdentifyClosingOfKnownTaskAgendaProcessor(self):
        agent = Agent()
        context = LCTContext(agent)

        event = agent.wo_memory.register("EVENT")
        event.context()[LCTContext.LEARNING] = True
        event.context()[LCTContext.CURRENT] = True

        tmr = TMR.new()
        tmr["EVENT-1"] = TMRInstance(name="EVENT-1", concept="EVENT")
        tmr["EVENT-1"]["TIME"] = ["<", "FIND-ANCHOR-TIME"]

        IdentifyClosingOfKnownTaskAgendaProcessor(context).process(agent, tmr)

        self.assertTrue(LCTContext.LEARNING not in event.context())
        self.assertTrue(LCTContext.CURRENT not in event.context())
        self.assertEqual(event.context()[LCTContext.LEARNED], True)