from backend.models.agenda import Goal
from backend.models.effectors import Callback, Capability, Effector
from backend.models.graph import Literal, Network
from backend.models.mps import AgentMethod, MPRegistry
from backend.models.statement import VariableMap

import unittest


class EffectorTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("EXE")
        self.g.register("EFFECTOR")
        self.g.register("PHYSICAL-EFFECTOR", isa="EXE.EFFECTOR")
        self.g.register("VERBAL-EFFECTOR", isa="EXE.EFFECTOR")
        self.g.register("MENTAL-EFFECTOR", isa="EXE.EFFECTOR")

    def test_effector_type(self):
        f1 = self.g.register("TEST-EFFECTOR", isa="EXE.PHYSICAL-EFFECTOR")
        f2 = self.g.register("TEST-EFFECTOR", isa="EXE.VERBAL-EFFECTOR")
        f3 = self.g.register("TEST-EFFECTOR", isa="EXE.MENTAL-EFFECTOR")

        self.assertEqual(Effector.Type.PHYSICAL, Effector(f1).type())
        self.assertEqual(Effector.Type.VERBAL, Effector(f2).type())
        self.assertEqual(Effector.Type.MENTAL, Effector(f3).type())

    def test_effector_status(self):
        f = self.g.register("TEST-EFFECTOR", isa="EXE.EFFECTOR")

        f["STATUS"] = Effector.Status.FREE
        self.assertTrue(Effector(f).is_free())

        f["STATUS"] = Literal(Effector.Status.FREE.name)
        self.assertTrue(Effector(f).is_free())

        f["STATUS"] = Effector.Status.OPERATING
        self.assertFalse(Effector(f).is_free())

        f["STATUS"] = Literal(Effector.Status.OPERATING.name)
        self.assertFalse(Effector(f).is_free())

    def test_effector_effecting(self):
        f1 = self.g.register("TEST-EFFECTOR", isa="EXE.EFFECTOR")
        f2 = self.g.register("GOAL")

        self.assertIsNone(Effector(f1).effecting())

        f1["EFFECTING"] = f2
        self.assertEqual(Effector(f1).effecting(), Goal(f2))

    def test_effector_capabilities(self):
        f1 = self.g.register("TEST-EFFECTOR", isa="EXE.EFFECTOR")
        f2 = self.g.register("CAPABILITY", generate_index=True)
        f3 = self.g.register("CAPABILITY", generate_index=True)

        self.assertEqual([], Effector(f1).capabilities())

        f1["HAS-CAPABILITY"] += f2
        f1["HAS-CAPABILITY"] += f3
        self.assertEqual([Capability(f2), Capability(f3)], Effector(f1).capabilities())

    def test_effector_reserve_with_capability(self):
        f1 = self.g.register("EFFECTOR", isa="EXE.EFFECTOR")
        f2 = self.g.register("GOAL", isa="EXE.GOAL")
        f3 = self.g.register("CAPABILITY", isa="EXE.CAPABILITY")

        goal = Goal(f2)
        capability = Capability(f3)

        effector = Effector(f1)
        effector.reserve(goal, capability)

        self.assertFalse(effector.is_free())
        self.assertEqual(effector.effecting(), goal)
        self.assertTrue(effector.frame in goal.frame["USES"])
        self.assertTrue(capability.frame in goal.frame["USES"])
        self.assertTrue(capability.frame in effector.frame["USES"])
        self.assertTrue(effector.frame in capability.frame["USED-BY"])

    def test_effector_release_with_capability(self):
        f1 = self.g.register("EFFECTOR", isa="EXE.EFFECTOR")
        f2 = self.g.register("GOAL", isa="EXE.GOAL")
        f3 = self.g.register("CAPABILITY", isa="EXE.CAPABILITY")

        goal = Goal(f2)
        capability = Capability(f3)

        effector = Effector(f1)
        effector.reserve(goal, capability)
        effector.release()

        self.assertTrue(effector.is_free())
        self.assertIsNone(effector.effecting())
        self.assertFalse(effector.frame in goal.frame["USES"])
        self.assertFalse(capability.frame in goal.frame["USES"])
        self.assertFalse(capability.frame in effector.frame["USES"])
        self.assertFalse(effector.frame in capability.frame["USED-BY"])


class CapabilityTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("TEST")

        MPRegistry.clear()

        class TestMP(AgentMethod):
            def run(self, var1):
                return var1 + 1

        self.mp = TestMP

        MPRegistry.register(self.mp)

    def test_capability_mp(self):
        f = self.g.register("CAPABILITY")
        f["MP"] = Literal("TestMP")

        capability = Capability(f)
        self.assertEqual("TestMP", capability.mp_name())
        self.assertEqual(2, capability.run(None, 1))

    def test_capability_in_use_by_effector(self):
        f1 = self.g.register("CAPABILITY")
        f2 = self.g.register("EFFECTOR")

        capability = Capability(f1)
        self.assertIsNone(capability.used_by())

        f1["USED-BY"] = f2
        self.assertEqual(Effector(f2), capability.used_by())

    def test_run(self):
        result = 0

        class TestMP(AgentMethod):
            def run(self, var1):
                nonlocal result
                result = var1

        MPRegistry.register(TestMP)

        f = self.g.register("CAPABILITY")
        f["MP"] = Literal(TestMP.__name__)

        capability = Capability(f)
        capability.run(None, 5)

        self.assertEqual(5, result)

    def test_run_with_callbacks(self):
        from backend.models.statement import Statement
        self.n.register(Statement.hierarchy())

        class TestMP(AgentMethod):
            def run(self, var1):
                pass

        MPRegistry.register(TestMP)

        stmt1 = self.g.register("SOME-STATEMENT.1", isa="EXE.STATEMENT")
        stmt2 = self.g.register("SOME-STATEMENT.2", isa="EXE.STATEMENT")
        varmap = self.g.register("SOME-VARIABLE-MAP")

        f = self.g.register("CAPABILITY")
        f["MP"] = Literal(TestMP.__name__)

        capability = Capability(f)
        capability.run(None, 5, graph=self.g, callbacks=[stmt1, stmt2], varmap=varmap)

        callback = Callback(self.g["CALLBACK.1"])
        self.assertEqual([stmt1, stmt2], callback.statements())
        self.assertEqual(varmap, callback.varmap())


class CallbackTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("EXE")

    def test_varmap(self):
        definition = self.g.register("VARMAP-DEFINITION")
        varmap = VariableMap.instance_of(self.g, definition, [])
        callback = Callback.instance(self.g, varmap, [], None)

        self.assertEqual(varmap, callback.varmap())

    def test_statements(self):
        from backend.models.statement import Statement
        self.n.register(Statement.hierarchy())

        stmt1 = self.g.register("STATEMENT", isa="EXE.STATEMENT", generate_index=True)
        stmt2 = self.g.register("STATEMENT", isa="EXE.STATEMENT", generate_index=True)
        callback = Callback.instance(self.g, None, [stmt1, stmt2], None)

        self.assertEqual([Statement(stmt1), Statement(stmt2)], callback.statements())

    def test_capability(self):
        capability = self.g.register("CAPABILITY")
        callback = Callback.instance(self.g, None, [], capability)

        self.assertEqual(Capability(capability), callback.capability())

    def test_callback_runs_statements(self):
        # 1) Define a meaning procedure and associated statement
        result = 0

        class TestMP(AgentMethod):
            def run(self, var1):
                nonlocal result
                result += var1

        self.mp = TestMP
        MPRegistry.clear()
        MPRegistry.register(self.mp)

        from backend.models.statement import MeaningProcedureStatement, Statement
        self.n.register(Statement.hierarchy())

        stmt1 = MeaningProcedureStatement.instance(self.g, self.mp.__name__, ["$var1"])
        stmt2 = MeaningProcedureStatement.instance(self.g, self.mp.__name__, ["$var1"])

        definition = self.g.register("DEFINITION")
        definition["WITH"] = Literal("$var1")
        varmap = VariableMap.instance_of(self.g, definition, [5])

        # 2) Setup the callback
        callback = Callback.instance(self.g, varmap, [stmt1, stmt2], None)
        callback.run()

        self.assertEqual(10, result)

    def test_callback_clears_usages(self):
        f1 = self.g.register("EFFECTOR", isa="EXE.EFFECTOR")
        f2 = self.g.register("GOAL", isa="EXE.GOAL")
        f3 = self.g.register("CAPABILITY", isa="EXE.CAPABILITY")

        goal = Goal(f2)
        capability = Capability(f3)

        effector = Effector(f1)
        effector.reserve(goal, capability)

        callback = Callback.instance(self.g, None, [], capability)

        self.assertFalse(effector.is_free())

        callback.run()

        self.assertTrue(effector.is_free())
        self.assertIsNone(effector.effecting())
        self.assertFalse(effector.frame in goal.frame["USES"])
        self.assertFalse(capability.frame in goal.frame["USES"])
        self.assertFalse(capability.frame in effector.frame["USES"])
        self.assertFalse(effector.frame in capability.frame["USED-BY"])