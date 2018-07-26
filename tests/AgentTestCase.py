from backend.agent import Agent
from backend.models.agenda import Goal
from backend.models.graph import Frame, Literal, Network
from backend.models.mps import MPRegistry
from backend.models.ontology import Ontology

import json
import unittest


class AgentTestCase(unittest.TestCase): # TODO: Clean up AATestCase and move back to that

    def setUp(self):

        class TestableAgent(Agent):
            def _bootstrap(self):
                pass

        self.n = Network()
        self.ontology = self.n.register(Ontology("ONT"))#self.n.register(Ontology.init_default())

        self.ontology.register("ALL")
        self.ontology.register("OBJECT", isa="ONT.ALL")
        self.ontology.register("EVENT", isa="ONT.ALL")
        self.ontology.register("PROPERTY", isa="ONT.ALL")
        self.ontology.register("FASTEN", isa="ONT.EVENT")
        self.ontology.register("ASSEMBLE", isa="ONT.EVENT")

        self.agent = TestableAgent(ontology=self.ontology)

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
        self.assertEqual(4, len(self.agent))
        self.assertEqual(0, len(self.agent.input_memory))

        self.agent._input()
        self.assertEqual(4, len(self.agent))
        self.assertEqual(0, len(self.agent.input_memory))

        self.agent._input(input=self.tmr())
        self.assertEqual(5, len(self.agent))
        self.assertIn("TMR#1", self.agent)
        self.assertEqual(1, len(self.agent.input_memory))

    def test_idea_decision(self):
        def priority_calculation(agent):
            return 0.5

        def action_selection(agent):
            return Frame("IDLE.1")

        goal = Goal.register(self.agent.internal, "GOAL", pcalc=[priority_calculation], aselect=[action_selection])

        self.agent.agenda().add_goal(goal)
        self.agent._decision()

        self.assertTrue(goal.is_active())
        self.assertEqual(0.5, goal.priority())
        self.assertTrue(self.agent.identity["ACTION-TO-TAKE"] == "IDLE.1")

    def test_idea_decision_deactivates_other_goals(self):
        def p1_calc(agent):
            return 0.1

        def p2_calc(agent):
            return 0.2

        def a_select(agent):
            return None

        goal1 = Goal.register(self.agent.internal, "GOAL", pcalc=[p1_calc], aselect=[a_select])
        goal1.status(Goal.Status.ACTIVE)

        goal2 = Goal.register(self.agent.internal, "GOAL", pcalc=[p2_calc], aselect=[a_select])
        goal1.status(Goal.Status.PENDING)

        self.agent.agenda().add_goal(goal1)
        self.agent.agenda().add_goal(goal2)
        self.agent._decision()

        self.assertTrue(goal1.is_pending())
        self.assertTrue(goal2.is_active())

    def test_idea_execute(self):
        ran = False
        def action_method(agent):
            nonlocal ran
            ran = True

        MPRegistry[action_method.__name__] = action_method

        mp = self.agent.internal.register("MEANING-PROCEDURE")
        mp["CALLS"] = Literal(action_method.__name__)

        action = self.agent.internal.register("ACTION")
        action["RUN"] = mp

        self.agent.identity["ACTION-TO-TAKE"] = action

        self.agent._execute()
        self.assertTrue(ran)
        self.assertNotIn("ACTION-TO-TAKE", self.agent.identity)

    def test_idea_assess(self):
        target = self.agent.internal.register("FRAME")
        target["COLOR"] = "yellow"

        goal = Goal.register(self.agent.internal, "GOAL", condition=[("SELF.FRAME.1", "COLOR", "yellow")])
        goal.status(Goal.Status.ACTIVE)
        self.agent.agenda().add_goal(goal)

        self.agent._assess()
        self.assertTrue(goal.is_satisfied())

    def test_idea(self):
        agent = Agent(ontology=self.ontology)
        agent.logger().enable()

        agent.idea(None)