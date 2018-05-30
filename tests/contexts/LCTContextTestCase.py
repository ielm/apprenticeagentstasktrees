from backend.agent import Agent
from backend.contexts.LCTContext import LCTContext
from backend.models.tmr import TMR
from backend.models.tmrinstance import TMRInstance
from backend.ontology import Ontology
from tests.ApprenticeAgentsTestCase import ApprenticeAgentsTestCase


class LCTContextTestCase(ApprenticeAgentsTestCase):

    @classmethod
    def setUpClass(cls):
        pass  # Do not load the usual ontology

    def setUp(self):
        Ontology.ontology = ApprenticeAgentsTestCase.TestOntology(include_t1=True)
        Ontology.ontology["FASTEN"] = {}
        Ontology.ontology["ASSEMBLE"] = {}
        Ontology.ontology["BUILD"] = {}

    def test_learning_hierarchy(self):
        agent = Agent()
        context = LCTContext(agent)

        event1 = agent.wo_memory.register("EVENT")
        event2 = agent.wo_memory.register("EVENT")
        event3 = agent.wo_memory.register("EVENT")
        event4 = agent.wo_memory.register("EVENT")

        event1.context()[LCTContext.LEARNING] = True
        event1.context()[LCTContext.CURRENT] = False
        event1.context()[LCTContext.WAITING_ON] = event2.name

        event2.context()[LCTContext.LEARNING] = True
        event2.context()[LCTContext.CURRENT] = False
        event2.context()[LCTContext.WAITING_ON] = event3.name

        event3.context()[LCTContext.LEARNING] = True
        event3.context()[LCTContext.CURRENT] = True

        self.assertEqual(context.learning_hierarchy(), [event3.name, event2.name, event1.name])

    def test_learning_hierarchy_no_current(self):
        agent = Agent()
        context = LCTContext(agent)

        event1 = agent.wo_memory.register("EVENT")

        event1.context()[LCTContext.LEARNED] = True

        self.assertEqual(context.learning_hierarchy(), [])

    def test_finish_learning(self):
        agent = Agent()
        context = LCTContext(agent)

        event1 = agent.wo_memory.register("EVENT")
        event2 = agent.wo_memory.register("EVENT")

        event1.context()[LCTContext.LEARNING] = True
        event1.context()[LCTContext.CURRENT] = False
        event1.context()[LCTContext.WAITING_ON] = event2.name

        event2.context()[LCTContext.LEARNING] = True
        event2.context()[LCTContext.CURRENT] = True

        context.finish_learning(event2.name)

        self.assertEqual(event1.context()[LCTContext.LEARNING], True)
        self.assertEqual(event1.context()[LCTContext.CURRENT], True)
        self.assertTrue(LCTContext.WAITING_ON not in event1.context())

        self.assertEqual(event2.context()[LCTContext.LEARNED], True)
        self.assertTrue(LCTContext.LEARNING not in event2.context())
        self.assertTrue(LCTContext.CURRENT not in event2.context())
        self.assertTrue(LCTContext.WAITING_ON not in event2.context())

    def test_IdentifyClosingOfKnownTaskAgendaProcessor(self):
        agent = Agent()
        context = LCTContext(agent)

        event = agent.wo_memory.register("EVENT")
        event.context()[LCTContext.LEARNING] = True
        event.context()[LCTContext.CURRENT] = True

        tmr = TMR.new()
        tmr["EVENT-1"] = TMRInstance(name="EVENT-1", concept="EVENT")
        tmr["EVENT-1"]["TIME"] = ["<", "FIND-ANCHOR-TIME"]

        LCTContext.IdentifyClosingOfKnownTaskAgendaProcessor(context).process(agent, tmr)

        self.assertTrue(LCTContext.LEARNING not in event.context())
        self.assertTrue(LCTContext.CURRENT not in event.context())
        self.assertEqual(event.context()[LCTContext.LEARNED], True)