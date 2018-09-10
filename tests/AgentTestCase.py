from backend.agent import Agent
from backend.models.agenda import Action, Goal
from backend.models.graph import Literal, Network
from backend.models.ontology import Ontology
from backend.models.statement import Statement, VariableMap
from backend.models.tmr import TMR

import unittest


class AgentTestCase(unittest.TestCase):

    def setUp(self):

        class TestableAgent(Agent):
            def _bootstrap(self):
                pass

        self.n = Network()
        self.ontology = self.n.register(Ontology("ONT"))

        self.ontology.register("ALL")
        self.ontology.register("OBJECT", isa="ONT.ALL")
        self.ontology.register("EVENT", isa="ONT.ALL")
        self.ontology.register("PROPERTY", isa="ONT.ALL")
        self.ontology.register("FASTEN", isa="ONT.EVENT")
        self.ontology.register("ASSEMBLE", isa="ONT.EVENT")

        self.agent = TestableAgent(ontology=self.ontology)

        from backend.utils.AtomicCounter import AtomicCounter
        TMR.counter = AtomicCounter()

    def tmr(self):
        return {
            "sentence": "Test.",
            "tmr": [{
                "sentence": "Test.",
                "sent-num": 1,
                "results": [{
                    "TMR": {}
                }],

            }],
            "syntax": [{
                "basicDeps": {}
            }]
        }

    def test_idea_input(self):
        self.assertEqual(5, len(self.agent))
        self.assertEqual(0, len(self.agent.input_memory))

        self.agent._input()
        self.assertEqual(5, len(self.agent))
        self.assertEqual(0, len(self.agent.input_memory))

        tmr = self.tmr()
        self.agent._input(input=tmr)
        self.assertEqual(6, len(self.agent))
        self.assertIn("TMR#1", self.agent)
        self.assertEqual(1, len(self.agent.pending_inputs()))
        self.assertEqual(tmr["sentence"], self.agent.pending_inputs()[0].sentence)

    def test_idea_decision(self):
        graph = self.agent.internal
        definition = graph.register("GOAL")
        action = graph.register("ACTION")

        definition["PRIORITY"] = 0.5
        definition["PLAN"] = action
        action["SELECT"] = Literal(Action.DEFAULT)

        goal = Goal.instance_of(graph, definition, [])
        self.agent.agenda().add_goal(goal)
        self.agent._decision()

        self.assertTrue(goal.is_active())
        self.assertEqual(0.5, goal.priority())
        self.assertTrue(self.agent.identity["ACTION-TO-TAKE"] == action)

    def test_idea_decision_deactivates_other_goals(self):
        graph = self.agent.internal
        definition1 = graph.register("GOAL")
        definition2 = graph.register("GOAL")
        action = graph.register("ACTION")

        definition1["PRIORITY"] = 0.1
        definition2["PRIORITY"] = 0.2

        definition1["PLAN"] = action
        definition2["PLAN"] = action

        action["SELECT"] = Literal(Action.DEFAULT)

        goal1 = Goal.instance_of(graph, definition1, [])
        goal2 = Goal.instance_of(graph, definition2, [])

        goal1.status(Goal.Status.ACTIVE)
        goal2.status(Goal.Status.PENDING)

        self.agent.agenda().add_goal(goal1)
        self.agent.agenda().add_goal(goal2)
        self.agent._decision()

        self.assertTrue(goal1.is_pending())
        self.assertTrue(goal2.is_active())

    def test_idea_execute(self):
        ran = False
        found_goal = False

        class TestStatement(Statement):
            def run(self, varmap: VariableMap):
                nonlocal ran
                ran = True

                nonlocal found_goal
                if varmap.frame["MARKER"] == 123:
                    found_goal = True

        graph = self.agent.internal
        action = graph.register("ACTION")
        statement = graph.register("STATEMENT", isa="EXE.STATEMENT")
        goal = graph.register("GOAL")

        action["PERFORM"] = statement
        Goal(goal).status(Goal.Status.ACTIVE)
        self.agent.lookup("EXE.STATEMENT")["CLASSMAP"] = Literal(TestStatement)
        self.agent.identity["ACTION-TO-TAKE"] = action
        self.agent.agenda().add_goal(goal)
        goal["MARKER"] = 123

        self.agent._execute()
        self.assertTrue(ran)
        self.assertTrue(found_goal)
        self.assertNotIn("ACTION-TO-TAKE", self.agent.identity)

    def test_idea_assess(self):

        class TestStatement(Statement):
            def run(self, varmap: VariableMap):
                return True

        graph = self.agent.internal
        definition = graph.register("GOAL")
        condition = graph.register("CONDITION")
        statement = graph.register("STATEMENT", isa="EXE.BOOLEAN-STATEMENT")

        definition["PRIORITY"] = 0.5
        definition["WHEN"] = condition
        condition["IF"] = statement
        condition["STATUS"] = Goal.Status.SATISFIED

        self.agent.lookup("EXE.BOOLEAN-STATEMENT")["CLASSMAP"] = Literal(TestStatement)

        goal = Goal.instance_of(graph, definition, [])
        goal.status(Goal.Status.ACTIVE)
        self.agent.agenda().add_goal(goal)

        self.agent._assess()
        self.assertTrue(goal.is_satisfied())

    def test_idea(self):
        agent = Agent(ontology=Ontology.init_default("ONT"))
        agent.logger().enable()

        import json
        import os

        def resource(fp):
            r = None
            with open(fp) as f:
                r = json.load(f)
            return r

        file = os.path.abspath(__package__) + "/resources/DemoMay2018_Analyses.json"
        demo = resource(file)
        tmr = demo[0]  # We will build a chair.

        agent.idea(None)
        agent.idea(tmr)
        agent.idea(None)

    def test_iidea(self):
        agent = Agent(ontology=Ontology.init_default("ONT"))
        agent.logger().enable()

        import json
        import os

<<<<<<< HEAD
        self.assertEqual(agent.action_queue, ["ROBOT.GET(ONT.SCREWDRIVER)"])




=======
        def resource(fp):
            r = None
            with open(fp) as f:
                r = json.load(f)
            return r

        file = os.path.abspath(__package__) + "/resources/DemoMay2018_Analyses.json"
        demo = resource(file)
        tmr = demo[0]  # We will build a chair.

        agent.iidea()
        agent.iidea()
        agent.iidea()
        agent.iidea(input=tmr)
        agent.iidea()
        agent.iidea()
        agent.iidea()
        agent.iidea()
        agent.iidea()
        agent.iidea()
        agent.iidea()
        agent.iidea()
        agent.iidea()
        agent.iidea()
        agent.iidea()
        agent.iidea()
        agent.iidea()
        agent.iidea()
        agent.iidea()
        agent.iidea()
        agent.iidea(input=tmr)
        agent.iidea()
        agent.iidea()
        agent.iidea()
        agent.iidea()
        agent.iidea()
        agent.iidea()
        agent.iidea()
>>>>>>> upstream/master
