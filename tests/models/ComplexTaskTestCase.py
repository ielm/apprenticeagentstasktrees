from backend.models.graph import Frame, Graph, Literal, Network
from backend.agent import Agent
from backend.models.ontology import Ontology
from backend.models.agenda import Agenda, Goal, Action
from backend.models.output import OutputXMR, OutputXMRTemplate
from backend.models.bootstrap import Bootstrap
from backend.models.task import ComplexTask

import unittest


class ComplexTaskTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("TEST")
        # self.capability = self.g.register("CAPABILITY")
        self.ontology = self.n.register(Ontology("ONT"))

    @staticmethod
    def action():
        agent = Agent(ontology=Ontology.init_default())

        Bootstrap.bootstrap_resource(agent, "backend.resources", "chair.knowledge")

        return agent.lt_memory["LT.BUILD.1"]

    def test_create(self):
        action = self.action()

        complextask = ComplexTask(action, action.name())

        # print(complextask.actions())
        # print(action)

        for item in complextask.actions():
            print(item)
