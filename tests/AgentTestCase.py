from backend.agent import Agent
from backend.models.agenda import Action, Goal, Step
from backend.models.effectors import Capability, Effector
from backend.models.graph import Literal, Network
from backend.models.ontology import Ontology
from backend.models.statement import CapabilityStatement, Statement, VariableMap
from backend.models.tmr import TMR
from backend.models.xmr import XMR

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

        self.agent.identity["PRIORITY_WEIGHT"] = 1.5
        self.agent.identity["RESOURCES_WEIGHT"] = 0.25

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
        self.assertEqual(6, len(self.agent))
        self.assertEqual(0, len(self.agent.input_memory))

        self.agent._input()
        self.assertEqual(6, len(self.agent))
        self.assertEqual(0, len(self.agent.input_memory))

        tmr = self.tmr()
        self.agent._input(input=tmr)
        self.assertEqual(7, len(self.agent))
        self.assertIn("TMR#1", self.agent)
        self.assertEqual(1, len(self.agent.pending_inputs()))
        self.assertEqual(tmr["sentence"], self.agent.pending_inputs()[0].sentence)

        tmr = self.tmr()
        source = self.agent.lt_memory.register("HUMAN")
        self.agent._input(input=tmr, source=source)
        self.assertEqual(8, len(self.agent))
        self.assertIn("TMR#2", self.agent)
        self.assertTrue(self.agent.internal["XMR.2"]["SOURCE"] == source)

        tmr = self.tmr()
        self.agent._input(input=tmr, type="LANGUAGE")
        self.assertEqual(9, len(self.agent))
        self.assertIn("TMR#3", self.agent)
        self.assertTrue(self.agent.internal["XMR.3"]["TYPE"] == XMR.Type.LANGUAGE.value)

    def test_idea_decision(self):
        graph = self.agent.internal
        definition = graph.register("GOAL")
        action = graph.register("ACTION")

        definition["PRIORITY"] = 0.5
        definition["RESOURCES"] = 0.5
        definition["PLAN"] = action
        action["SELECT"] = Literal(Action.DEFAULT)

        goal = Goal.instance_of(graph, definition, [])
        self.agent.agenda().add_goal(goal)
        self.agent._decision()

        self.assertTrue(goal.is_active())
        self.assertEqual(0.5, goal.priority(None))
        self.assertEqual(0.5, goal.resources(None))
        self.assertEqual(0.625, goal.decision(None))
        self.assertTrue(self.agent.identity["ACTION-TO-TAKE"] == action)

    def test_idea_decision_reserves_effectors(self):
        graph = self.agent.internal

        # 1) Define and assign a capability and effector
        capability = Capability.instance(graph, "CAP-A", "")
        effector = Effector.instance(graph, Effector.Type.MENTAL, [capability])
        self.agent.identity["HAS-EFFECTOR"] += effector.frame

        # 2) Define and instance a goal that needs the capability
        stmt = CapabilityStatement.instance(graph, capability, [], [])
        action = Action.build(graph, "ACTION", Action.DEFAULT, Step.build(graph, 1, stmt))
        definition = Goal.define(graph, "TEST", 0.5, 0.5, [action], [], [])
        goal = Goal.instance_of(graph, definition, [])
        self.agent.agenda().add_goal(goal)

        # 3) Decide on the next task; the effector should then be reserved
        self.assertTrue(effector.is_free())
        self.agent._decision()
        self.assertFalse(effector.is_free())

    def test_idea_decision_reserves_multiple_effectors(self):
        graph = self.agent.internal

        # 1) Define and assign two capabilities and effectors
        capability1 = Capability.instance(graph, "CAP-A", "")
        capability2 = Capability.instance(graph, "CAP-B", "")
        effector1 = Effector.instance(graph, Effector.Type.MENTAL, [capability1])
        effector2 = Effector.instance(graph, Effector.Type.MENTAL, [capability2])
        self.agent.identity["HAS-EFFECTOR"] += effector1.frame
        self.agent.identity["HAS-EFFECTOR"] += effector2.frame

        # 2) Define and instance a goal that needs both capabilities
        stmt1 = CapabilityStatement.instance(graph, capability1, [], [])
        stmt2 = CapabilityStatement.instance(graph, capability2, [], [])
        action = Action.build(graph, "ACTION", Action.DEFAULT, Step.build(graph, 1, [stmt1, stmt2]))
        definition = Goal.define(graph, "TEST", 0.5, 0.5, [action], [], [])
        goal = Goal.instance_of(graph, definition, [])
        self.agent.agenda().add_goal(goal)

        # 3) Decide on the next task; the effectors should then be reserved
        self.assertTrue(effector1.is_free())
        self.assertTrue(effector2.is_free())
        self.agent._decision()
        self.assertFalse(effector1.is_free())
        self.assertFalse(effector2.is_free())

    def test_idea_decision_reserves_effectors_in_decision_order(self):
        graph = self.agent.internal

        # 1) Define and assign a capability and effector
        capability = Capability.instance(graph, "CAP-A", "")
        effector = Effector.instance(graph, Effector.Type.MENTAL, [capability])
        self.agent.identity["HAS-EFFECTOR"] += effector.frame

        # 2) Define and instance two goals that needs the capability (with different weights)
        stmt = CapabilityStatement.instance(graph, capability, [], [])
        action1 = Action.build(graph, "ACTION", Action.DEFAULT, Step.build(graph, 1, stmt))
        action2 = Action.build(graph, "ACTION", Action.DEFAULT, Step.build(graph, 1, stmt))
        definition1 = Goal.define(graph, "TEST", 0.5, 0.5, [action1], [], [])
        definition2 = Goal.define(graph, "TEST", 1.0, 0.1, [action2], [], [])
        goal1 = Goal.instance_of(graph, definition1, [])
        goal2 = Goal.instance_of(graph, definition2, [])
        self.agent.agenda().add_goal(goal1)
        self.agent.agenda().add_goal(goal2)

        # 3) Decide on the next task; goal2 should be selected and goal1 should not be
        self.assertFalse(goal1.is_active())
        self.assertFalse(goal2.is_active())
        self.agent._decision()
        self.assertFalse(goal1.is_active())
        self.assertTrue(goal2.is_active())

    def test_idea_decision_activates_multiple_goals_if_capabilities_exist(self):
        graph = self.agent.internal

        # 1) Define and assign two capabilities and effectors
        capability1 = Capability.instance(graph, "CAP-A", "")
        capability2 = Capability.instance(graph, "CAP-B", "")
        effector1 = Effector.instance(graph, Effector.Type.MENTAL, [capability1])
        effector2 = Effector.instance(graph, Effector.Type.MENTAL, [capability2])
        self.agent.identity["HAS-EFFECTOR"] += effector1.frame
        self.agent.identity["HAS-EFFECTOR"] += effector2.frame

        # 2) Define and instance two goals that needs different capabilities
        stmt1 = CapabilityStatement.instance(graph, capability1, [], [])
        stmt2 = CapabilityStatement.instance(graph, capability2, [], [])
        action1 = Action.build(graph, "ACTION", Action.DEFAULT, Step.build(graph, 1, stmt1))
        action2 = Action.build(graph, "ACTION", Action.DEFAULT, Step.build(graph, 1, stmt2))
        definition1 = Goal.define(graph, "TEST", 0.5, 0.5, [action1], [], [])
        definition2 = Goal.define(graph, "TEST", 0.5, 0.5, [action2], [], [])
        goal1 = Goal.instance_of(graph, definition1, [])
        goal2 = Goal.instance_of(graph, definition2, [])
        self.agent.agenda().add_goal(goal1)
        self.agent.agenda().add_goal(goal2)

        # 3) Decide on the next task; both goals should be made active
        self.assertFalse(goal1.is_active())
        self.assertFalse(goal2.is_active())
        self.agent._decision()
        self.assertTrue(goal1.is_active())
        self.assertTrue(goal2.is_active())

    def test_idea_decision_activates_goals_with_no_capability_requirements(self):
        graph = self.agent.internal

        # 1) Define and instance a goal that needs no capability
        action = Action.build(graph, "ACTION", Action.DEFAULT, Step.build(graph, 1, Step.IDLE))
        definition = Goal.define(graph, "TEST", 0.5, 0.5, [action], [], [])
        goal = Goal.instance_of(graph, definition, [])
        self.agent.agenda().add_goal(goal)

        # 2) Decide on the next task; the goal should be made active
        self.assertFalse(goal.is_active())
        self.agent._decision()
        self.assertTrue(goal.is_active())

    def test_idea_execute(self):
        ran = False
        found_goal = False

        class TestStatement(Statement):
            def run(self, varmap: VariableMap, *args, **kwargs):
                nonlocal ran
                ran = True

                nonlocal found_goal
                if varmap.frame["MARKER"] == 123:
                    found_goal = True

        graph = self.agent.internal
        action = graph.register("ACTION")
        step = graph.register("STEP")
        statement = graph.register("STATEMENT", isa="EXE.STATEMENT")
        goal = graph.register("GOAL")
        goal["PLAN"] = action

        action["HAS-STEP"] = step

        step["INDEX"] = 1
        step["STATUS"] = Step.Status.PENDING
        step["PERFORM"] = statement

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
            def run(self, varmap: VariableMap, *args, **kwargs):
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

    def test_callback(self):
        from backend.agent import Callback
        from backend.models.mps import AgentMethod, MPRegistry
        from backend.models.statement import CapabilityStatement, MeaningProcedureStatement

        # First, declare a testable Meaning Procedure to run
        result = 0

        class TestMP(AgentMethod):
            def run(self, var1):
                nonlocal result
                result += 1

        MPRegistry.register(TestMP)

        # Next, minimally define a goal
        definition = self.agent.exe.register("GOAL-DEFINITION")
        definition["WITH"] += Literal("$var1")
        params = [1]
        goal = VariableMap.instance_of(self.agent.exe, definition, params)

        # Now define a capability statement with a callback
        capability = Capability.instance(self.agent.exe, "CAPABILITY", TestMP.__name__)
        callback = [MeaningProcedureStatement.instance(self.agent.exe, TestMP.__name__, ["$var1"])]
        statement = CapabilityStatement.instance(self.agent.exe, capability, callback, ["$var1"])

        # Load the callback directly into the agent (this is "after" the capability statement has been executed)
        cbi = Callback.instance(self.agent.exe, goal, [statement], capability)

        # Fire the callback
        self.agent.callback(cbi.frame._identifier)

        # Did it fire? And has the callback been removed?
        self.assertEqual(result, 1)
        self.assertNotIn(cbi.frame.name(), self.agent.exe)
