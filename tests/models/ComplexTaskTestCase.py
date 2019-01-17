from backend.models.graph import Frame, Graph, Literal, Network
from backend.agent import Agent
from backend.models.ontology import Ontology
from backend.models.agenda import Agenda, Goal, Plan
from backend.models.output import OutputXMR, OutputXMRTemplate
from backend.models.bootstrap import Bootstrap
from backend.models.task import ComplexTask, ActionableTask

import unittest


class ComplexTaskTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("TEST")
        # self.capability = self.g.register("CAPABILITY")
        self.ontology = self.n.register(Ontology("ONT"))

        self.agent = Agent(ontology=Ontology.init_default())

        Bootstrap.bootstrap_resource(self.agent, "backend.resources.experiments", "chair.knowledge")
        # Bootstrap.bootstrap_resource(self.agent, "backend.resources", "goals.aa")
        Bootstrap.bootstrap_resource(self.agent, "backend.resources", "Templates.knowledge")
        Bootstrap.bootstrap_resource(self.agent, "backend.resources.example", "example.knowledge")

    def action(self):
        return self.agent.lt_memory["LT.BUILD.1"]

    def test_Actionable_Task(self):
        print("\nActionableTask\n" + "=" * 50)

        action = self.action()

        print(action, "\n")

        test_action = action["HAS-EVENT-AS-PART"][0].resolve()
        test_action = ActionableTask(test_action, test_action.name(), test_action["INSTANCE-OF"])

        expected = "LT.TAKE.1 = {'IS-A': INSTANCE-OF=[ONT.TAKE], 'INSTANCE-OF': INSTANCE-OF=[ONT.TAKE], 'AGENT': AGENT=[SELF.ROBOT.1], 'THEME': THEME=[LT.SCREWDRIVER.1]}"

        self.assertEqual(test_action.__str__(), expected)

    def test_Complex_Task(self):
        print("\nComplexTask\n" + "=" * 50)

        action = self.action()

        complex_task = ComplexTask(self.agent, action, action.name())

        for subtask in complex_task.subtasks():
            print(subtask)

        expected = "LT.BUILD.1.TAKE.1 = {'IS-A': INSTANCE-OF=[ONT.TAKE], 'INSTANCE-OF': INSTANCE-OF=[ONT.TAKE], 'AGENT': AGENT=[SELF.ROBOT.1], 'THEME': THEME=[LT.SCREWDRIVER.1]}"
        self.assertEqual(complex_task.subtasks()[0].__str__(), expected)

        expected = "LT.BUILD.1.BUILD.2.TAKE.2 = {'IS-A': INSTANCE-OF=[ONT.TAKE], 'INSTANCE-OF': INSTANCE-OF=[ONT.TAKE], 'AGENT': AGENT=[SELF.ROBOT.1], 'THEME': THEME=[LT.BRACKET.1]}"
        self.assertEqual(complex_task.subtasks()[1].__str__(), expected)

        expected = "LT.BUILD.1.BUILD.2.TAKE.3 = {'IS-A': INSTANCE-OF=[ONT.TAKE], 'INSTANCE-OF': INSTANCE-OF=[ONT.TAKE], 'AGENT': AGENT=[SELF.ROBOT.1], 'THEME': THEME=[LT.BRACKET.2]}"
        self.assertEqual(complex_task.subtasks()[2].__str__(), expected)

        expected = "LT.BUILD.1.BUILD.2.TAKE.4 = {'IS-A': INSTANCE-OF=[ONT.TAKE], 'INSTANCE-OF': INSTANCE-OF=[ONT.TAKE], 'AGENT': AGENT=[SELF.ROBOT.1], 'THEME': THEME=[LT.DOWEL.1]}"
        self.assertEqual(complex_task.subtasks()[3].__str__(), expected)

        expected = "LT.BUILD.1.BUILD.2.HOLD.1 = {'IS-A': INSTANCE-OF=[ONT.HOLD], 'INSTANCE-OF': INSTANCE-OF=[ONT.HOLD], 'AGENT': AGENT=[SELF.ROBOT.1], 'THEME': THEME=[LT.DOWEL.1]}"
        self.assertEqual(complex_task.subtasks()[4].__str__(), expected)

        expected = "LT.BUILD.1.BUILD.2.FASTEN.1 = {'IS-A': INSTANCE-OF=[ONT.FASTEN], 'INSTANCE-OF': INSTANCE-OF=[ONT.FASTEN], 'AGENT': AGENT=[LT.HUMAN.1], 'THEME': THEME=[LT.BRACKET.2], 'DESTINATION': DESTINATION=[LT.DOWEL.1], 'INSTRUMENT': INSTRUMENT=[LT.SCREW.1, LT.SCREWDRIVER.1], 'TIME': TIME=[FIND-ANCHOR-TIME]}"
        self.assertEqual(complex_task.subtasks()[5].__str__(), expected)

        expected = "LT.BUILD.1.BUILD.2.RESTRAIN.1 = {'IS-A': INSTANCE-OF=[ONT.RESTRAIN], 'INSTANCE-OF': INSTANCE-OF=[ONT.RESTRAIN], 'AGENT': AGENT=[SELF.ROBOT.1], 'THEME': THEME=[LT.DOWEL.1]}"
        self.assertEqual(complex_task.subtasks()[6].__str__(), expected)

    def test_Steps(self):
        print("\nStep\n" + "=" * 50)

        action = self.action()

        complex_task = ComplexTask(self.agent, action, action.name())

        # print(complex_task.plan())
        # for step in complex_task.steps():
        #     print(step.index())

        # for s in complex_task.steps():
            # print(s.__str__())
        # print("debug")
        print(complex_task.plan().steps())
