from backend.Agent import Agent
from backend.models.agenda import Decision, Expectation, Goal, Plan, Step, Trigger
from backend.models.effectors import Capability, Effector
from backend.models.output import OutputXMRTemplate
from backend.models.statement import OutputXMRStatement, VariableMap
from backend.models.tmr import TMR
from backend.models.xmr import XMR
from backend.utils.AgentOntoLang import AgentOntoLang
from ontograph import graph
from ontograph.Frame import Frame
from ontograph.Query import ExistsComparator, IdComparator, Query
from ontograph.Space import Space

import unittest
from unittest.mock import patch


class AgentTestCase(unittest.TestCase):

    def setUp(self):

        graph.reset()

        class TestableAgent(Agent):
            def _bootstrap(self):
                pass

        Frame("@ONT.ALL")
        Frame("@ONT.OBJECT").add_parent("@ONT.ALL")
        Frame("@ONT.EVENT").add_parent("@ONT.ALL")
        Frame("@ONT.PROPERTY").add_parent("@ONT.ALL")
        Frame("@ONT.FASTEN").add_parent("@ONT.EVENT")
        Frame("@ONT.ASSEMBLE").add_parent("@ONT.EVENT")

        self.agent = TestableAgent()

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
                    "TMR": {"EVENT-1": {"AGENT": "HUMAN", "concept": "EVENT", "sent-word-ind": [1,[0]]}}
                }],

            }],
            "syntax": [{
                "basicDeps": {}
            }]
        }

    def test_decisions(self):
        f1 = Frame("@EXE.DECISION.?")
        f2 = Frame("@EXE.DECISION.?")

        self.agent.identity["HAS-DECISION"] += f1
        self.agent.identity["HAS-DECISION"] += f2

        self.assertTrue(f1 in self.agent.decisions())
        self.assertTrue(f2 in self.agent.decisions())

    def test_idea_input(self):
        self.assertEqual(8, len(self.agent))
        self.assertEqual(0, len(self.agent.input_memory))

        self.agent._input()
        self.assertEqual(8, len(self.agent))
        self.assertEqual(0, len(self.agent.input_memory))

        tmr = self.tmr()
        self.agent._input(input=tmr)
        self.assertEqual(9, len(self.agent))
        self.assertIn("TMR#1", self.agent)
        self.assertEqual(1, len(self.agent.pending_inputs()))
        self.assertEqual(tmr["sentence"], Frame("@INPUTS.XMR.1")["SENTENCE"].singleton())

        tmr = self.tmr()
        source = Frame("@LT.HUMAN.?")
        self.agent._input(input=tmr, source=source)
        self.assertEqual(10, len(self.agent))
        self.assertIn("TMR#2", self.agent)
        self.assertTrue(Frame("@INPUTS.XMR.2")["SOURCE"] == source)

        tmr = self.tmr()
        self.agent._input(input=tmr, type="LANGUAGE")
        self.assertEqual(11, len(self.agent))
        self.assertIn("TMR#3", self.agent)
        self.assertTrue(Frame("@INPUTS.XMR.3")["TYPE"] == XMR.Type.LANGUAGE)

    def test_iidea(self):
        agent = Agent()
        # agent.logger().enable()

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
        from backend.models.effectors import Callback

        # First, minimally define a goal
        definition = Frame("@EXE.GOAL-DEFINITION")
        definition["WITH"] += "$var1"
        params = [1]
        goal = VariableMap.instance_of(self.agent.exe, definition, params)

        # Now define a capability statement with a callback
        capability = Capability.instance(self.agent.exe, "CAPABILITY", "TestMP", ["@ONT.EVENT"])
        effector = Effector.instance(self.agent.exe, Effector.Type.PHYSICAL, [capability])

        decision = Decision.build(self.agent.exe, goal.frame, "PLAN", "STEP")
        callback = Callback.build(self.agent.exe, decision, effector)

        # Load the callback directly into the agent (this is "after" the capability statement has been executed)
        effector.reserve(decision, "OUTPUT", capability)
        decision.frame["HAS-CALLBACK"] += callback.frame

        # Fire the callback
        self.agent.callback(callback.frame.id)

        # Is the callback marked as received?
        self.assertEqual(Callback.Status.RECEIVED, callback.status())

    def test_preferences(self):
        self.assertEqual(0.5, self.agent.preference("TEST-PREFERENCE", 0.5))
        self.agent.identity["TEST-PREFERENCE"] = 0.6
        self.assertEqual(0.6, self.agent.preference("TEST-PREFERENCE", 0.5))


class AgentDecideTestCase(unittest.TestCase):

    def setUp(self):

        graph.reset()

        class TestableAgent(Agent):
            pass

        Frame("@ONT.ALL")
        Frame("@ONT.OBJECT").add_parent("@ONT.ALL")
        Frame("@ONT.EVENT").add_parent("@ONT.ALL")
        Frame("@ONT.PROPERTY").add_parent("@ONT.ALL")
        Frame("@ONT.FASTEN").add_parent("@ONT.EVENT")
        Frame("@ONT.ASSEMBLE").add_parent("@ONT.EVENT")

        self.agent = TestableAgent()

        self.agent.identity["PRIORITY_WEIGHT"] = 1.5
        self.agent.identity["RESOURCES_WEIGHT"] = 0.25

        Frame("@EXE.TEST-CAPABILITY").add_parent("@EXE.CAPABILITY")

        self.g = self.agent.exe

    def test_decide_creates_decisions(self):
        step = Step.build(self.g, 1, [])
        plan1 = Plan.build(self.g, "plan-1", Plan.DEFAULT, [step])
        plan2 = Plan.build(self.g, "plan-2", Plan.DEFAULT, [step])
        definition = Goal.define(self.g, "goal-1", 0.5, 0.5, [plan1, plan2], [], [], [])

        goal1 = Goal.instance_of(self.g, definition, [])
        goal2 = Goal.instance_of(self.g, definition, [])

        self.agent.agenda().add_goal(goal1)
        self.agent.agenda().add_goal(goal2)

        self.assertEqual(0, len(self.agent.decisions()))

        self.agent._decide()

        self.assertEqual(4, len(self.agent.decisions()))

        decisions = list(map(lambda decision: (decision.goal().name(), str(decision.goal().frame.id), decision.plan().name(), decision.step().index()), self.agent.decisions()))

        self.assertIn(("goal-1", "@EXE.GOAL.1", "plan-1", 1), decisions)
        self.assertIn(("goal-1", "@EXE.GOAL.1", "plan-2", 1), decisions)
        self.assertIn(("goal-1", "@EXE.GOAL.2", "plan-1", 1), decisions)
        self.assertIn(("goal-1", "@EXE.GOAL.2", "plan-2", 1), decisions)

    def test_decide_only_creates_decisions_for_selectable_plans(self):
        from backend.models.statement import ExistsStatement
        stmt = ExistsStatement.instance(self.g, Query(ExistsComparator(slot="DNE", filler=123)))

        step = Step.build(self.g, 1, [])
        plan1 = Plan.build(self.g, "plan-1", Plan.DEFAULT, [step])
        plan2 = Plan.build(self.g, "plan-2", stmt, [step])
        definition = Goal.define(self.g, "goal", 0.5, 0.5, [plan1, plan2], [], [], [])

        goal = Goal.instance_of(self.g, definition, [])

        self.agent.agenda().add_goal(goal)

        self.assertEqual(0, len(self.agent.decisions()))

        self.agent._decide()

        self.assertEqual(1, len(self.agent.decisions()))

        decisions = list(map(lambda decision: (decision.goal().name(), str(decision.goal().frame.id), decision.plan().name(), decision.step().index()), self.agent.decisions()))
        self.assertIn(("goal", "@EXE.GOAL.1", "plan-1", 1), decisions)
        self.assertNotIn(("goal", "@EXE.GOAL.1", "plan-2", 1), decisions)

    def test_decide_only_creates_decisions_that_do_not_yet_exist(self):
        step = Step.build(self.g, 1, [])
        plan1 = Plan.build(self.g, "plan-1", Plan.DEFAULT, [step])
        plan2 = Plan.build(self.g, "plan-2", Plan.DEFAULT, [step])
        definition = Goal.define(self.g, "goal", 0.5, 0.5, [plan1, plan2], [], [], [])

        goal = Goal.instance_of(self.g, definition, [])

        self.agent.agenda().add_goal(goal)

        self.assertEqual(0, len(self.agent.decisions()))

        decision = Decision.build(self.agent.internal, goal, plan1, step)
        self.agent.identity["HAS-DECISION"] += decision.frame

        self.assertEqual(1, len(self.agent.decisions()))

        self.agent._decide()

        self.assertEqual(2, len(self.agent.decisions()))

        decisions = list(map(lambda decision: (decision.goal().name(), str(decision.goal().frame.id), decision.plan().name(), decision.step().index()), self.agent.decisions()))
        self.assertIn(("goal", "@EXE.GOAL.1", "plan-1", 1), decisions)
        self.assertIn(("goal", "@EXE.GOAL.1", "plan-2", 1), decisions)

    def test_decide_inspects_decisions(self):
        step = Step.build(self.g, 1, [])
        plan = Plan.build(self.g, "plan-1", Plan.DEFAULT, [step])
        definition = Goal.define(self.g, "goal-1", 0.5, 0.5, [plan], [], [], [])

        goal = Goal.instance_of(self.g, definition, [])
        self.agent.agenda().add_goal(goal)

        self.agent._decide()

        decision = self.agent.decisions()[0]
        self.assertEqual(0.5, decision.priority())
        self.assertEqual(0.5, decision.cost())
        self.assertEqual(0, len(decision.outputs()))

    def test_decide_selects_decisions(self):
        step = Step.build(self.g, 1, [])
        plan = Plan.build(self.g, "plan-1", Plan.DEFAULT, [step])
        definition = Goal.define(self.g, "goal-1", 0.5, 0.5, [plan], [], [], [])

        goal = Goal.instance_of(self.g, definition, [])
        self.agent.agenda().add_goal(goal)

        self.agent._decide()

        decision = self.agent.decisions()[0]
        self.assertEqual(Decision.Status.SELECTED, decision.status())

    def test_decide_declines_decisions(self):
        template = OutputXMRTemplate.build("template", XMR.Type.ACTION, "@EXE.TEST-CAPABILITY", [])
        statement = OutputXMRStatement.instance(self.g, template, [], self.agent.identity)

        step = Step.build(self.g, 1, [statement])
        plan = Plan.build(self.g, "plan-1", Plan.DEFAULT, [step])
        definition = Goal.define(self.g, "goal-1", 0.5, 0.5, [plan], [], [], [])

        goal = Goal.instance_of(self.g, definition, [])
        self.agent.agenda().add_goal(goal)

        self.agent._decide()

        decision = self.agent.decisions()[0]
        self.assertEqual(Decision.Status.DECLINED, decision.status())

    def test_decide_reserves_effectors(self):
        capability = Capability.instance(self.g, "TEST-CAPABILITY", "", ["@ONT.EVENT"])
        effector = Effector.instance(self.g, Effector.Type.PHYSICAL, [capability])
        self.agent.identity["HAS-EFFECTOR"] += effector.frame

        template = OutputXMRTemplate.build("template", XMR.Type.ACTION, capability, [])
        statement = OutputXMRStatement.instance(self.g, template, [], self.agent.identity)

        step = Step.build(self.g, 1, [statement])
        plan = Plan.build(self.g, "plan-1", Plan.DEFAULT, [step])
        definition = Goal.define(self.g, "goal-1", 0.5, 0.5, [plan], [], [], [])

        goal = Goal.instance_of(self.g, definition, [])
        self.agent.agenda().add_goal(goal)

        self.agent._decide()

        self.assertFalse(effector.is_free())
        self.assertEqual(self.agent.decisions()[0], effector.on_decision())
        self.assertEqual(capability, effector.on_capability())
        self.assertEqual(self.agent.decisions()[0].outputs()[0], effector.on_output())

    def test_decide_reserves_multiple_effectors_for_separate_decisions(self):
        capability = Capability.instance(self.g, "TEST-CAPABILITY", "", ["@ONT.EVENT"])
        effector1 = Effector.instance(self.g, Effector.Type.PHYSICAL, [capability])
        effector2 = Effector.instance(self.g, Effector.Type.PHYSICAL, [capability])
        self.agent.identity["HAS-EFFECTOR"] += effector1.frame
        self.agent.identity["HAS-EFFECTOR"] += effector2.frame

        template = OutputXMRTemplate.build("template", XMR.Type.ACTION, capability, [])
        statement = OutputXMRStatement.instance(self.g, template, [], self.agent.identity)

        step = Step.build(self.g, 1, [statement])
        plan = Plan.build(self.g, "plan-1", Plan.DEFAULT, [step])
        definition = Goal.define(self.g, "goal-1", 0.5, 0.5, [plan], [], [], [])

        goal1 = Goal.instance_of(self.g, definition, [])
        goal2 = Goal.instance_of(self.g, definition, [])
        self.agent.agenda().add_goal(goal1)
        self.agent.agenda().add_goal(goal2)

        self.agent._decide()

        self.assertFalse(effector1.is_free())
        self.assertFalse(effector2.is_free())

        self.assertIn(effector1.on_decision(), self.agent.decisions())
        self.assertIn(effector2.on_decision(), self.agent.decisions())
        self.assertNotEqual(effector1.on_decision(), effector2.on_decision())

        self.assertEqual(capability, effector1.on_capability())
        self.assertEqual(capability, effector2.on_capability())

        self.assertIn(effector1.on_output(), [self.agent.decisions()[0].outputs()[0], self.agent.decisions()[1].outputs()[0]])
        self.assertIn(effector2.on_output(), [self.agent.decisions()[0].outputs()[0], self.agent.decisions()[1].outputs()[0]])
        self.assertNotEqual(effector1.on_output(), effector2.on_output())

    def test_decide_reserves_multiple_effectors_for_single_decision(self):
        capability = Capability.instance(self.g, "TEST-CAPABILITY", "", ["@ONT.EVENT"])
        effector1 = Effector.instance(self.g, Effector.Type.PHYSICAL, [capability])
        effector2 = Effector.instance(self.g, Effector.Type.PHYSICAL, [capability])
        self.agent.identity["HAS-EFFECTOR"] += effector1.frame
        self.agent.identity["HAS-EFFECTOR"] += effector2.frame

        template = OutputXMRTemplate.build("template", XMR.Type.ACTION, capability, [])
        statement1 = OutputXMRStatement.instance(self.g, template, [], self.agent.identity)
        statement2 = OutputXMRStatement.instance(self.g, template, [], self.agent.identity)

        step = Step.build(self.g, 1, [statement1, statement2])
        plan = Plan.build(self.g, "plan-1", Plan.DEFAULT, [step])
        definition = Goal.define(self.g, "goal-1", 0.5, 0.5, [plan], [], [], [])

        goal = Goal.instance_of(self.g, definition, [])
        self.agent.agenda().add_goal(goal)

        self.agent._decide()

        self.assertEqual(1, len(self.agent.decisions()))

        self.assertFalse(effector1.is_free())
        self.assertFalse(effector2.is_free())

        self.assertEqual(effector1.on_decision(), self.agent.decisions()[0])
        self.assertEqual(effector2.on_decision(), self.agent.decisions()[0])

        self.assertEqual(capability, effector1.on_capability())
        self.assertEqual(capability, effector2.on_capability())

        self.assertIn(effector1.on_output(), self.agent.decisions()[0].outputs())
        self.assertIn(effector2.on_output(), self.agent.decisions()[0].outputs())
        self.assertNotEqual(effector1.on_output(), effector2.on_output())

    def test_decide_selects_multiple_decisions_if_possible(self):
        capability = Capability.instance(self.g, "TEST-CAPABILITY", "", ["@ONT.EVENT"])
        effector1 = Effector.instance(self.g, Effector.Type.PHYSICAL, [capability])
        effector2 = Effector.instance(self.g, Effector.Type.PHYSICAL, [capability])
        self.agent.identity["HAS-EFFECTOR"] += effector1.frame
        self.agent.identity["HAS-EFFECTOR"] += effector2.frame

        template = OutputXMRTemplate.build("template", XMR.Type.ACTION, capability, [])
        statement = OutputXMRStatement.instance(self.g, template, [], self.agent.identity)

        step = Step.build(self.g, 1, [statement])
        plan = Plan.build(self.g, "plan-1", Plan.DEFAULT, [step])
        definition = Goal.define(self.g, "goal-1", 0.5, 0.5, [plan], [], [], [])

        goal1 = Goal.instance_of(self.g, definition, [])
        goal2 = Goal.instance_of(self.g, definition, [])
        self.agent.agenda().add_goal(goal1)
        self.agent.agenda().add_goal(goal2)

        self.agent._decide()

        self.assertEqual(2, len(self.agent.decisions()))
        self.assertEqual(Decision.Status.SELECTED, self.agent.decisions()[0].status())
        self.assertEqual(Decision.Status.SELECTED, self.agent.decisions()[1].status())

    def test_decide_selects_decisions_in_decision_order(self):
        capability = Capability.instance(self.g, "TEST-CAPABILITY", "", ["@ONT.EVENT"])
        effector = Effector.instance(self.g, Effector.Type.PHYSICAL, [capability])
        self.agent.identity["HAS-EFFECTOR"] += effector.frame

        template = OutputXMRTemplate.build("template", XMR.Type.ACTION, capability, [])
        statement = OutputXMRStatement.instance(self.g, template, [], self.agent.identity)

        step = Step.build(self.g, 1, [statement])
        plan = Plan.build(self.g, "plan-1", Plan.DEFAULT, [step])
        definition1 = Goal.define(self.g, "goal-1", 1.0, 0.5, [plan], [], [], [])
        definition2 = Goal.define(self.g, "goal-2", 0.0, 0.5, [plan], [], [], [])

        goal1 = Goal.instance_of(self.g, definition1, [])
        goal2 = Goal.instance_of(self.g, definition2, [])

        self.agent.agenda().add_goal(goal2)
        self.agent.agenda().add_goal(goal1)

        self.agent._decide()

        if self.agent.decisions()[0].goal() == goal1:
            self.assertEqual(Decision.Status.SELECTED, self.agent.decisions()[0].status())
            self.assertEqual(Decision.Status.DECLINED, self.agent.decisions()[1].status())
        else:
            self.assertEqual(Decision.Status.SELECTED, self.agent.decisions()[1].status())
            self.assertEqual(Decision.Status.DECLINED, self.agent.decisions()[0].status())

    def test_decide_only_pursues_one_plan_per_goal(self):
        capability = Capability.instance(self.g, "TEST-CAPABILITY", "", ["@ONT.EVENT"])
        effector = Effector.instance(self.g, Effector.Type.PHYSICAL, [capability])
        self.agent.identity["HAS-EFFECTOR"] += effector.frame

        template = OutputXMRTemplate.build("template", XMR.Type.ACTION, capability, [])
        statement = OutputXMRStatement.instance(self.g, template, [], self.agent.identity)

        step = Step.build(self.g, 1, [statement])
        plan1 = Plan.build(self.g, "plan-1", Plan.DEFAULT, [step])
        plan2 = Plan.build(self.g, "plan-2", Plan.DEFAULT, [step])
        definition = Goal.define(self.g, "goal-1", 1.0, 0.5, [plan1, plan2], [], [], [])

        goal = Goal.instance_of(self.g, definition, [])

        self.agent.agenda().add_goal(goal)

        self.agent._decide()

        self.assertEqual(2, len(self.agent.decisions()))
        self.assertEqual(1, len(list(filter(lambda decision: decision.status() == Decision.Status.SELECTED, self.agent.decisions()))))
        self.assertEqual(1, len(list(filter(lambda decision: decision.status() == Decision.Status.DECLINED, self.agent.decisions()))))

    def test_decide_blocked_decisions_cannot_be_selected(self):

        capability = Capability.instance(self.g, "TEST-CAPABILITY", "", ["@ONT.EVENT"])
        effector = Effector.instance(self.g, Effector.Type.PHYSICAL, [capability])
        self.agent.identity["HAS-EFFECTOR"] += effector.frame

        template = OutputXMRTemplate.build("template", XMR.Type.ACTION, capability, [])
        statement = OutputXMRStatement.instance(self.g, template, [], self.agent.identity)

        step = Step.build(self.g, 1, [statement])
        plan = Plan.build(self.g, "plan", Plan.DEFAULT, [step])
        definition = Goal.define(self.g, "goal", 1.0, 0.5, [plan], [], [], [])
        goal = Goal.instance_of(self.g, definition, [])

        decision = Decision.build(self.g, goal, plan, step)
        decision.frame["STATUS"] = Decision.Status.BLOCKED

        self.agent.agenda().add_goal(goal.frame)
        self.agent.identity["HAS-DECISION"] += decision.frame

        self.agent._decide()
        self.assertEqual(Decision.Status.BLOCKED, decision.status())

    def test_decide_goals_whose_decisions_are_blocked_are_still_marked_as_active(self):
        from backend.models.statement import AssertStatement, ExistsStatement, MakeInstanceStatement

        assertion = ExistsStatement.instance(self.g, Query(IdComparator("@SELF.DNE")))
        resolutions = [MakeInstanceStatement.instance(self.g, self.g.name, Goal.define(self.g, "resolution", 1.0, 0.5, [], [], [], []).frame, [])]
        statement = AssertStatement.instance(self.g, assertion, resolutions)

        step = Step.build(self.g, 1, [statement])
        plan = Plan.build(self.g, "plan", Plan.DEFAULT, [step])
        definition = Goal.define(self.g, "goal", 1.0, 0.5, [plan], [], [], [])
        goal = Goal.instance_of(self.g, definition, [])

        self.agent.agenda().add_goal(goal.frame)

        self.agent._decide()
        self.assertEqual(1, len(self.agent.decisions()))
        self.assertEqual(Decision.Status.BLOCKED, self.agent.decisions()[0].status())
        self.assertTrue(goal.is_active())

    @patch.object(Trigger, 'fire')
    def test_decide_runs_triggers(self, mocked):
        trigger1 = Trigger.build(self.g, None, None)
        trigger2 = Trigger.build(self.g, None, None)

        self.agent.agenda().add_trigger(trigger1)
        self.agent.agenda().add_trigger(trigger2)

        self.agent._decide()

        self.assertEqual(2, mocked.call_count)


class AgentExecuteTestCase(unittest.TestCase):

    def setUp(self):

        graph.reset()

        class TestableAgent(Agent):
            def _bootstrap(self):
                pass

        Frame("@ONT.ALL")
        Frame("@ONT.OBJECT").add_parent("@ONT.ALL")
        Frame("@ONT.EVENT").add_parent("@ONT.ALL")
        Frame("@ONT.PROPERTY").add_parent("@ONT.ALL")
        Frame("@ONT.FASTEN").add_parent("@ONT.EVENT")
        Frame("@ONT.ASSEMBLE").add_parent("@ONT.EVENT")

        self.agent = TestableAgent()

        self.agent.identity["PRIORITY_WEIGHT"] = 1.5
        self.agent.identity["RESOURCES_WEIGHT"] = 0.25

        Frame("@EXE.TEST-CAPABILITY").add_parent("@EXE.CAPABILITY")

        self.g = self.agent.exe

    @patch.object(Decision, 'execute')
    def test_execute_provides_correct_effectors(self, mocked):
        capability = Capability.instance(self.g, "TEST-CAPABILITY", "", ["@ONT.EVENT"])
        effector1 = Effector.instance(self.g, Effector.Type.PHYSICAL, [capability])
        effector2 = Effector.instance(self.g, Effector.Type.PHYSICAL, [capability])
        self.agent.identity["HAS-EFFECTOR"] += effector1.frame
        self.agent.identity["HAS-EFFECTOR"] += effector2.frame

        template = OutputXMRTemplate.build("template", XMR.Type.ACTION, capability, [])
        statement = OutputXMRStatement.instance(self.g, template, [], self.agent.identity)

        step = Step.build(self.g, 1, [statement])
        plan = Plan.build(self.g, "plan-1", Plan.DEFAULT, [step])
        definition = Goal.define(self.g, "goal-1", 1.0, 0.5, [plan], [], [], [])
        goal = Goal.instance_of(self.g, definition, [])

        decision = Decision.build(self.g, goal, plan, step)
        decision.select()
        self.agent.identity["HAS-DECISION"] += decision.frame

        output = template.create(self.agent.exe, [])
        self.agent.identity["HAS-OUTPUT"] += output.frame

        effector1.reserve(decision, output, capability)

        self.agent._execute()

        mocked.assert_called_once_with(self.agent, [effector1])

    @patch.object(Decision, 'execute')
    def test_execute_only_runs_selected_decisions(self, mocked):
        capability = Capability.instance(self.g, "TEST-CAPABILITY", "", ["@ONT.EVENT"])
        effector1 = Effector.instance(self.g, Effector.Type.PHYSICAL, [capability])
        effector2 = Effector.instance(self.g, Effector.Type.PHYSICAL, [capability])
        self.agent.identity["HAS-EFFECTOR"] += effector1.frame
        self.agent.identity["HAS-EFFECTOR"] += effector2.frame

        template = OutputXMRTemplate.build("template", XMR.Type.ACTION, capability, [])
        statement = OutputXMRStatement.instance(self.g, template, [], self.agent.identity)

        step = Step.build(self.g, 1, [statement])
        plan = Plan.build(self.g, "plan-1", Plan.DEFAULT, [step])
        definition = Goal.define(self.g, "goal-1", 1.0, 0.5, [plan], [], [], [])
        goal = Goal.instance_of(self.g, definition, [])

        decision1 = Decision.build(self.g, goal, plan, step)
        decision2 = Decision.build(self.g, goal, plan, step)
        decision1.select()
        self.agent.identity["HAS-DECISION"] += decision1.frame
        self.agent.identity["HAS-DECISION"] += decision2.frame

        output = template.create(self.agent.exe, [])
        self.agent.identity["HAS-OUTPUT"] += output.frame

        effector1.reserve(decision1, output, capability)
        effector2.reserve(decision2, output, capability)

        self.agent._execute()

        mocked.assert_called_once_with(self.agent, [effector1])

    def test_execute_runs_multiple_decisions(self):
        from backend.models.mps import MPRegistry, OutputMethod

        out = []
        class TestMP(OutputMethod):
            def run(self):
                nonlocal out
                out.append(self.output)

        MPRegistry.register(TestMP)

        capability = Capability.instance(self.g, "TEST-CAPABILITY", TestMP, ["@ONT.EVENT"])
        effector1 = Effector.instance(self.g, Effector.Type.PHYSICAL, [capability])
        effector2 = Effector.instance(self.g, Effector.Type.PHYSICAL, [capability])
        self.agent.identity["HAS-EFFECTOR"] += effector1.frame
        self.agent.identity["HAS-EFFECTOR"] += effector2.frame

        template = OutputXMRTemplate.build("template", XMR.Type.ACTION, capability, [])
        statement = OutputXMRStatement.instance(self.g, template, [], self.agent.identity)

        step = Step.build(self.g, 1, [statement])
        plan = Plan.build(self.g, "plan-1", Plan.DEFAULT, [step])
        definition = Goal.define(self.g, "goal-1", 1.0, 0.5, [plan], [], [], [])
        goal = Goal.instance_of(self.g, definition, [])

        decision1 = Decision.build(self.g, goal, plan, step)
        decision2 = Decision.build(self.g, goal, plan, step)
        decision1.select()
        decision2.select()
        self.agent.identity["HAS-DECISION"] += decision1.frame
        self.agent.identity["HAS-DECISION"] += decision2.frame

        output1 = template.create(self.agent.exe, [])
        output2 = template.create(self.agent.exe, [])
        self.agent.identity["HAS-OUTPUT"] += output1.frame
        self.agent.identity["HAS-OUTPUT"] += output2.frame

        effector1.reserve(decision1, output1, capability)
        effector2.reserve(decision2, output2, capability)

        self.agent._execute()

        self.assertEqual([output1, output2], out)


class AgentAssessTestCase(unittest.TestCase):

    def setUp(self):

        graph.reset()

        class TestableAgent(Agent):
            pass

        Frame("@ONT.ALL")
        Frame("@ONT.OBJECT").add_parent("@ONT.ALL")
        Frame("@ONT.EVENT").add_parent("@ONT.ALL")
        Frame("@ONT.PROPERTY").add_parent("@ONT.ALL")
        Frame("@ONT.FASTEN").add_parent("@ONT.EVENT")
        Frame("@ONT.ASSEMBLE").add_parent("@ONT.EVENT")

        self.agent = TestableAgent()

        self.agent.identity["PRIORITY_WEIGHT"] = 1.5
        self.agent.identity["RESOURCES_WEIGHT"] = 0.25

        Frame("@EXE.TEST-CAPABILITY").add_parent("@EXE.CAPABILITY")

        self.g = self.agent.exe

    def test_assess_processes_all_received_callbacks(self):
        from backend.models.effectors import Callback

        # First, minimally define a goal
        definition = Frame("@EXE.GOAL-DEFINITION")
        definition["WITH"] += "$var1"
        params = [1]
        goal = VariableMap.instance_of(self.agent.exe, definition, params)

        # Now define a capability statement with two callbacks
        capability = Capability.instance(self.agent.exe, "TEST-CAPABILITY", "TestMP", ["@ONT.EVENT"])
        effector1 = Effector.instance(self.agent.exe, Effector.Type.PHYSICAL, [capability])
        effector2 = Effector.instance(self.agent.exe, Effector.Type.PHYSICAL, [capability])

        decision1 = Decision.build(self.agent.exe, goal.frame, "PLAN", "STEP")
        decision2 = Decision.build(self.agent.exe, goal.frame, "PLAN", "STEP")

        decision1.frame["HAS-EFFECTOR"] = effector1.frame
        decision2.frame["HAS-EFFECTOR"] = effector2.frame

        callback1 = Callback.build(self.agent.exe, decision1, effector1)
        callback2 = Callback.build(self.agent.exe, decision2, effector2)

        self.agent.identity["HAS-DECISION"] += decision1.frame
        self.agent.identity["HAS-DECISION"] += decision2.frame

        # Load the callbacks directly into the agent (this is "after" the capability statement has been executed)
        effector1.reserve(decision1, "OUTPUT", capability)
        effector2.reserve(decision2, "OUTPUT", capability)
        decision1.frame["HAS-CALLBACK"] += callback1.frame
        decision2.frame["HAS-CALLBACK"] += callback2.frame
        decision2.frame["STATUS"] = Decision.Status.EXECUTING

        # Set one of the callbacks to be received
        callback1.received()

        # Assess, and check that only one of the callbacks has been processed
        self.agent._assess()

        self.assertTrue(effector1.is_free())
        self.assertNotIn(callback1, decision1.callbacks())
        self.assertNotIn(effector1, decision1.effectors())
        self.assertNotIn(callback1.frame.id, self.agent.exe)

        self.assertFalse(effector2.is_free())
        self.assertIn(callback2, decision2.callbacks())
        self.assertIn(effector2, decision2.effectors())
        self.assertIn(callback2.frame.id, self.agent.exe)

    def test_assess_marks_executing_decisions_as_finished_if_no_callbacks_remain(self):
        step = Step.build(self.g, 1, [])

        decision1 = Decision.build(self.g, "GOAL", "PLAN", step)
        decision2 = Decision.build(self.g, "GOAL", "PLAN", step)

        decision2.frame["HAS-CALLBACK"] = Frame("@EXE.CALLBACK")

        decision1.frame["STATUS"] = Decision.Status.EXECUTING
        decision2.frame["STATUS"] = Decision.Status.EXECUTING

        self.agent.identity["HAS-DECISION"] += decision1.frame
        self.agent.identity["HAS-DECISION"] += decision2.frame

        self.agent._assess()

        self.assertEqual(Decision.Status.FINISHED, decision1.status())
        self.assertEqual(Decision.Status.EXECUTING, decision2.status())

    def test_assess_marks_executing_decisions_as_finished_if_no_pending_expectations_remain(self):
        # from backend.models.bootstrap import Bootstrap
        from backend.models.statement import IsStatement

        AgentOntoLang().load_knowledge("backend.resources", "exe.knowledge")

        target = Frame("@EXE.TARGET")
        target["SLOT"] = 123

        step = Step.build(self.g, 1, [])

        decision1 = Decision.build(self.g, VariableMap(Frame("@EXE.VARMAP.?")).frame, "PLAN", step)
        decision2 = Decision.build(self.g, VariableMap(Frame("@EXE.VARMAP.?")).frame, "PLAN", step)

        decision1.frame["HAS-EXPECTATION"] = Expectation.build(self.g, Expectation.Status.PENDING, IsStatement.instance(self.g, target, "SLOT", 123)).frame
        decision2.frame["HAS-EXPECTATION"] = Expectation.build(self.g, Expectation.Status.PENDING, IsStatement.instance(self.g, target, "SLOT", 456)).frame

        decision1.frame["STATUS"] = Decision.Status.EXECUTING
        decision2.frame["STATUS"] = Decision.Status.EXECUTING

        self.agent.identity["HAS-DECISION"] += decision1.frame
        self.agent.identity["HAS-DECISION"] += decision2.frame

        self.agent._assess()

        self.assertEqual(Decision.Status.FINISHED, decision1.status())
        self.assertEqual(Decision.Status.EXECUTING, decision2.status())

    def test_assess_removes_all_non_executing_non_finished_decisions(self):
        step = Step.build(self.g, 1, [])

        decision1 = Decision.build(self.g, "GOAL", "PLAN", step)
        decision2 = Decision.build(self.g, "GOAL", "PLAN", step)
        decision3 = Decision.build(self.g, "GOAL", "PLAN", step)
        decision4 = Decision.build(self.g, "GOAL", "PLAN", step)
        decision5 = Decision.build(self.g, "GOAL", "PLAN", step)

        decision2.frame["HAS-CALLBACK"] = Frame("@EXE.CALLBACK")

        decision1.frame["STATUS"] = Decision.Status.EXECUTING
        decision2.frame["STATUS"] = Decision.Status.EXECUTING
        decision3.frame["STATUS"] = Decision.Status.SELECTED
        decision4.frame["STATUS"] = Decision.Status.DECLINED
        decision5.frame["STATUS"] = Decision.Status.PENDING

        self.agent.identity["HAS-DECISION"] += decision1.frame
        self.agent.identity["HAS-DECISION"] += decision2.frame
        self.agent.identity["HAS-DECISION"] += decision3.frame
        self.agent.identity["HAS-DECISION"] += decision4.frame
        self.agent.identity["HAS-DECISION"] += decision5.frame

        self.agent._assess()

        self.assertIn(decision1, self.agent.decisions())
        self.assertIn(decision2, self.agent.decisions())
        self.assertNotIn(decision3, self.agent.decisions())
        self.assertNotIn(decision4, self.agent.decisions())
        self.assertNotIn(decision5, self.agent.decisions())

    def test_assess_removes_any_output_xmrs_associated_with_removed_decisions(self):
        from backend.models.xmr import XMR

        step = Step.build(self.g, 1, [])

        decision1 = Decision.build(self.g, "GOAL", "PLAN", step)
        decision2 = Decision.build(self.g, "GOAL", "PLAN", step)

        decision1.frame["STATUS"] = Decision.Status.FINISHED
        decision2.frame["STATUS"] = Decision.Status.DECLINED

        output1 = XMR.instance(self.g, "XMR#1", XMR.Signal.OUTPUT, XMR.Type.ACTION, XMR.OutputStatus.PENDING, "@TEST.FRAME.1", "")
        output2 = XMR.instance(self.g, "XMR#2", XMR.Signal.OUTPUT, XMR.Type.ACTION, XMR.OutputStatus.PENDING, "@TEST.FRAME.1", "")

        decision1.frame["HAS-OUTPUT"] = output1.frame
        decision2.frame["HAS-OUTPUT"] = output2.frame

        self.agent.identity["HAS-DECISION"] += decision1.frame
        self.agent.identity["HAS-DECISION"] += decision2.frame

        Space("XMR#1")
        Space("XMR#2")

        self.agent._assess()

        self.assertIn(output1.frame, self.g)
        self.assertNotIn(output2.frame, self.g)

    def test_assess_marks_step_as_finished_if_decision_is_finished(self):
        step1 = Step.build(self.g, 1, [])
        step2 = Step.build(self.g, 1, [])

        decision1 = Decision.build(self.g, "GOAL", "PLAN", step1)
        decision2 = Decision.build(self.g, "GOAL", "PLAN", step2)

        decision1.frame["STATUS"] = Decision.Status.EXECUTING
        decision2.frame["STATUS"] = Decision.Status.DECLINED

        self.agent.identity["HAS-DECISION"] += decision1.frame
        self.agent.identity["HAS-DECISION"] += decision2.frame

        self.assertEqual(Step.Status.PENDING, step1.status())
        self.assertEqual(Step.Status.PENDING, step2.status())

        self.agent._assess()

        self.assertEqual(Step.Status.FINISHED, step1.status())
        self.assertEqual(Step.Status.PENDING, step2.status())

    def test_assess_calls_assess_on_all_non_satisfied_goals(self):
        from backend.models.agenda import Condition

        definition = Goal.define(self.g, "test-goal", 0.5, 0.5, [], [Condition.build(self.g, [], Goal.Status.SATISFIED, on=Condition.On.EXECUTED)], [], [])

        goal1 = Goal.instance_of(self.g, definition, [])
        goal2 = Goal.instance_of(self.g, definition, [])

        goal1.status(status=Goal.Status.ACTIVE)
        goal2.status(status=Goal.Status.ACTIVE)

        self.agent.agenda().add_goal(goal1)
        self.agent.agenda().add_goal(goal2)

        self.assertTrue(goal1.is_active())
        self.assertTrue(goal2.is_active())

        goal1.frame["PLAN"] = Frame("@EXE.PLAN")

        self.agent._assess()

        self.assertTrue(goal1.is_satisfied())
        self.assertTrue(goal2.is_active())

    def test_assess_removes_satisfied_impasses(self):
        step = Step.build(self.g, 1, [])

        subgoal = Frame("@EXE.GOAL.?")
        subgoal["STATUS"] = Goal.Status.SATISFIED

        decision = Decision.build(self.g, "GOAL", "PLAN", step)
        decision.frame["HAS-IMPASSE"] += subgoal
        decision.frame["HAS-CALLBACK"] += Frame("@EXE.CALLBACK.?")
        decision.frame["STATUS"] = Decision.Status.BLOCKED
        self.agent.identity["HAS-DECISION"] += decision.frame

        self.assertEqual(Decision.Status.BLOCKED, decision.status())
        self.assertIn(subgoal, decision.impasses())

        self.agent._assess()
        self.assertEqual(Decision.Status.PENDING, decision.status())
        self.assertEqual(0, len(decision.impasses()))

    def test_assess_decision_not_removed_if_blocked(self):
        step = Step.build(self.g, 1, [])

        subgoal = Frame("@EXE.GOAL.?")
        subgoal["STATUS"] = Goal.Status.ACTIVE

        decision = Decision.build(self.g, "GOAL", "PLAN", step)
        decision.frame["HAS-IMPASSE"] += subgoal
        decision.frame["STATUS"] = Decision.Status.BLOCKED
        self.agent.identity["HAS-DECISION"] += decision.frame

        self.assertEqual(Decision.Status.BLOCKED, decision.status())
        self.assertIn(subgoal, decision.impasses())

        self.agent._assess()
        self.assertIn(decision, self.agent.decisions())

    def test_subgoals_are_cleared_if_a_goal_is_otherwise_satisfied(self):
        step = Step.build(self.g, 1, [])

        goal = Frame("@EXE.GOAL.?")
        goal["STATUS"] = Goal.Status.SATISFIED
        self.agent.agenda().add_goal(goal)

        subgoal = Frame("@EXE.GOAL.?")
        subgoal["STATUS"] = Goal.Status.ACTIVE
        self.agent.agenda().add_goal(subgoal)

        goal["HAS-GOAL"] += subgoal

        decision = Decision.build(self.g, goal, "PLAN", step)
        decision.frame["HAS-IMPASSE"] += subgoal
        decision.frame["STATUS"] = Decision.Status.BLOCKED
        self.agent.identity["HAS-DECISION"] += decision.frame

        self.assertIn(subgoal, self.agent.agenda().goals())

        self.agent._assess()

        self.assertNotIn(subgoal, self.agent.agenda().goals())

    def test_subgoals_are_cleared_if_a_goal_is_otherwise_abandoned(self):
        step = Step.build(self.g, 1, [])

        goal = Frame("@EXE.GOAL.?")
        goal["STATUS"] = Goal.Status.ABANDONED
        self.agent.agenda().add_goal(goal)

        subgoal = Frame("@EXE.GOAL.?")
        subgoal["STATUS"] = Goal.Status.ACTIVE
        self.agent.agenda().add_goal(subgoal)

        goal["HAS-GOAL"] += subgoal

        decision = Decision.build(self.g, goal, "PLAN", step)
        decision.frame["HAS-IMPASSE"] += subgoal
        decision.frame["STATUS"] = Decision.Status.BLOCKED
        self.agent.identity["HAS-DECISION"] += decision.frame

        self.assertIn(subgoal, self.agent.agenda().goals())

        self.agent._assess()

        self.assertNotIn(subgoal, self.agent.agenda().goals())

    def test_newly_generated_impasses_are_added_to_the_agenda(self):
        step = Step.build(self.g, 1, [])

        goal = Frame("@EXE.GOAL.?")
        goal["STATUS"] = Goal.Status.ACTIVE
        self.agent.agenda().add_goal(goal)

        subgoal = Frame("@EXE.GOAL.?")
        subgoal["STATUS"] = Goal.Status.ACTIVE

        goal["HAS-GOAL"] += subgoal

        decision = Decision.build(self.g, goal, "PLAN", step)
        decision.frame["HAS-IMPASSE"] += subgoal
        self.agent.identity["HAS-DECISION"] += decision.frame

        self.assertNotIn(subgoal, self.agent.agenda().goals())

        self.agent._assess()

        self.assertIn(subgoal, self.agent.agenda().goals())

    def test_assess_updates_expectation_status(self):
        # from backend.models.bootstrap import Bootstrap
        from backend.models.statement import IsStatement

        # Bootstrap.bootstrap_resource(None, "backend.resources", "exe.knowledge")
        AgentOntoLang().load_knowledge("backend.resources", "exe.knowledge")

        target = Frame("@EXE.TARGET")
        target["SLOT"] = 123

        goal = Frame("@EXE.GOAL.?")
        goal["STATUS"] = Goal.Status.ACTIVE
        self.agent.agenda().add_goal(goal)

        step = Step.build(self.g, 1, [])

        decision = Decision.build(self.g, goal, "PLAN", step)

        statement = IsStatement.instance(self.g, target, "SLOT", 123)
        expectation = Expectation.build(self.g, Expectation.Status.PENDING, statement)
        decision.frame["HAS-EXPECTATION"] += expectation.frame
        self.agent.identity["HAS-DECISION"] += decision.frame

        self.assertEqual(Expectation.Status.PENDING, expectation.status())

        self.agent._assess()

        self.assertEqual(Expectation.Status.SATISFIED, expectation.status())

    def test_assess_removes_transient_frames_out_of_scope(self):
        # from backend.models.bootstrap import Bootstrap
        from backend.models.statement import TransientFrame
        Frame("@EXE.TRANSIENT-FRAME")

        # Bootstrap.bootstrap_resource(None, "backend.resources", "exe.knowledge")
        AgentOntoLang().load_knowledge("backend.resources", "exe.knowledge")

        f1 = Frame("@EXE.FRAME.?").add_parent("@EXE.TRANSIENT-FRAME")
        f2 = Frame("@EXE.FRAME.?").add_parent("@EXE.TRANSIENT-FRAME")
        f3 = Frame("@EXE.FRAME.?").add_parent("@EXE.TRANSIENT-FRAME")
        f4 = Frame("@EXE.FRAME.?").add_parent("@EXE.TRANSIENT-FRAME")

        count = len(self.g)

        self.agent._assess()

        self.assertEqual(count, len(self.g))

        TransientFrame(f1).update_scope(TestScope())
        TransientFrame(f2).update_scope(TestScope())
        TransientFrame(f3).update_scope(TestScope())
        TransientFrame(f4).update_scope(TestScope())

        self.agent._assess()

        self.assertEqual(count - 4, len(self.g))


class TestScope():
    def __call__(self, *args, **kwargs):
        return False