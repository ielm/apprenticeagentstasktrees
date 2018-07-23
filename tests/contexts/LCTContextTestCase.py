from backend.agent import Agent
from backend.contexts.LCTContext import LCTContext
from backend.models.graph import Network
from backend.models.ontology import Ontology
from tests.ApprenticeAgentsTestCase import ApprenticeAgentsTestCase


class LCTContextTestCase(ApprenticeAgentsTestCase):

    @classmethod
    def setUpClass(cls):
        pass  # Do not load the usual ontology

    def setUp(self):
        self.n = Network()
        self.ontology = self.n.register(Ontology("ONT"))

        self.ontology.register("ALL")
        self.ontology.register("OBJECT", isa="ONT.ALL")
        self.ontology.register("EVENT", isa="ONT.ALL")

        self.ontology.register("ASSEMBLE", isa="ONT.EVENT")
        self.ontology.register("BUILD", isa="ONT.EVENT")
        self.ontology.register("FASTEN", isa="ONT.EVENT")

    def test_learning_hierarchy(self):
        agent = Agent(self.n, ontology=self.ontology)
        context = LCTContext(agent)

        event1 = agent.wo_memory.register("EVENT", isa="ONT.EVENT")
        event2 = agent.wo_memory.register("EVENT", isa="ONT.EVENT")
        event3 = agent.wo_memory.register("EVENT", isa="ONT.EVENT")
        event4 = agent.wo_memory.register("EVENT", isa="ONT.EVENT")

        event1[LCTContext.LEARNING] = True
        event1[LCTContext.CURRENT] = False
        event1[LCTContext.WAITING_ON] = event2.name()

        event2[LCTContext.LEARNING] = True
        event2[LCTContext.CURRENT] = False
        event2[LCTContext.WAITING_ON] = event3.name()

        event3[LCTContext.LEARNING] = True
        event3[LCTContext.CURRENT] = True

        self.assertEqual(context.learning_hierarchy(), [event3.name(), event2.name(), event1.name()])

    def test_learning_hierarchy_no_current(self):
        agent = Agent(self.n, ontology=self.ontology)
        context = LCTContext(agent)

        event1 = agent.wo_memory.register("EVENT", isa="ONT.EVENT")

        event1[LCTContext.LEARNED] = True

        self.assertEqual(context.learning_hierarchy(), [])

    def test_finish_learning(self):
        agent = Agent(self.n, ontology=self.ontology)
        context = LCTContext(agent)

        event1 = agent.wo_memory.register("EVENT", isa="ONT.EVENT")
        event2 = agent.wo_memory.register("EVENT", isa="ONT.EVENT")

        event1[LCTContext.LEARNING] = True
        event1[LCTContext.CURRENT] = False
        event1[LCTContext.WAITING_ON] = event2.name()

        event2[LCTContext.LEARNING] = True
        event2[LCTContext.CURRENT] = True

        context.finish_learning(event2.name())

        self.assertEqual(event1[LCTContext.LEARNING], True)
        self.assertEqual(event1[LCTContext.CURRENT], True)
        self.assertTrue(LCTContext.WAITING_ON not in event1)

        self.assertEqual(event2[LCTContext.LEARNED], True)
        self.assertTrue(LCTContext.LEARNING not in event2)
        self.assertTrue(LCTContext.CURRENT not in event2)
        self.assertTrue(LCTContext.WAITING_ON not in event2)