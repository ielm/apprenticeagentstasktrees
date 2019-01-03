from backend.models.agenda import Goal
from backend.models.effectors import Callback, Capability, Effector
from backend.models.graph import Literal, Network
from backend.models.mps import MPRegistry, OutputMethod
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

    def test_effector_capabilities(self):
        f1 = self.g.register("TEST-EFFECTOR", isa="EXE.EFFECTOR")
        f2 = self.g.register("CAPABILITY", generate_index=True)
        f3 = self.g.register("CAPABILITY", generate_index=True)

        self.assertEqual([], Effector(f1).capabilities())

        f1["HAS-CAPABILITY"] += f2
        f1["HAS-CAPABILITY"] += f3
        self.assertEqual([Capability(f2), Capability(f3)], Effector(f1).capabilities())

    def test_effector_on_decision(self):
        from backend.models.agenda import Decision

        decision = Decision.build(self.g, "GOAL", "PLAN", "STEP")

        f = self.g.register("TEST-EFFECTOR", isa="EXE.EFFECTOR")
        f["ON-DECISION"] = decision.frame

        self.assertEqual(decision, Effector(f).on_decision())

    def test_effector_on_output(self):
        from backend.models.output import OutputXMR, OutputXMRTemplate

        output = OutputXMR.build(self.g, OutputXMRTemplate.Type.PHYSICAL, "CAPABILITY", "TEST")

        f = self.g.register("TEST-EFFECTOR", isa="EXE.EFFECTOR")
        f["ON-OUTPUT"] = output.frame

        self.assertEqual(output, Effector(f).on_output())

    def test_effector_on_capability(self):
        capability = Capability.instance(self.g, "TEST-CAPABILITY", "TestMP", ["ONT.EVENT"])

        f = self.g.register("TEST-EFFECTOR", isa="EXE.EFFECTOR")
        f["ON-CAPABILITY"] = capability.frame

        self.assertEqual(capability, Effector(f).on_capability())

    def test_reserve(self):
        from backend.models.agenda import Decision
        from backend.models.output import OutputXMR, OutputXMRTemplate

        effector = Effector.instance(self.g, Effector.Type.PHYSICAL, [])

        self.assertTrue(effector.is_free())
        self.assertIsNone(effector.on_decision())
        self.assertIsNone(effector.on_output())
        self.assertIsNone(effector.on_capability())

        decision = Decision.build(self.g, "GOAL", "PLAN", "STEP")
        output = OutputXMR.build(self.g, OutputXMRTemplate.Type.PHYSICAL, "CAPABILITY", "TEST")
        capability = Capability.instance(self.g, "TEST-CAPABILITY", "TestMP", ["ONT.EVENT"])

        effector.reserve(decision, output, capability)

        self.assertFalse(effector.is_free())
        self.assertEqual(decision, effector.on_decision())
        self.assertEqual(output, effector.on_output())
        self.assertEqual(capability, effector.on_capability())

    def test_release(self):
        from backend.models.agenda import Decision
        from backend.models.output import OutputXMR, OutputXMRTemplate

        effector = Effector.instance(self.g, Effector.Type.PHYSICAL, [])

        decision = Decision.build(self.g, "GOAL", "PLAN", "STEP")
        output = OutputXMR.build(self.g, OutputXMRTemplate.Type.PHYSICAL, "CAPABILITY", "TEST")
        capability = Capability.instance(self.g, "TEST-CAPABILITY", "TestMP", ["ONT.EVENT"])

        effector.reserve(decision, output, capability)

        self.assertFalse(effector.is_free())
        self.assertEqual(decision, effector.on_decision())
        self.assertEqual(output, effector.on_output())
        self.assertEqual(capability, effector.on_capability())

        effector.release()

        self.assertTrue(effector.is_free())
        self.assertIsNone(effector.on_decision())
        self.assertIsNone(effector.on_output())
        self.assertIsNone(effector.on_capability())


class CapabilityTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("TEST")

        MPRegistry.clear()

    def test_capability_mp(self):

        out = False

        class TestMP(OutputMethod):
            def run(self):
                nonlocal out
                out = True

        MPRegistry.register(TestMP)

        f = self.g.register("CAPABILITY")
        f["MP"] = Literal("TestMP")

        capability = Capability(f)
        self.assertEqual("TestMP", capability.mp_name())

        capability.run(None, None, None)
        self.assertTrue(out)

    def test_capability_events(self):
        f = self.g.register("CAPABILITY")
        f["COVERS-EVENT"] += self.g.register("A-EVENT")
        f["COVERS-EVENT"] += self.g.register("B-EVENT")

        self.assertEqual(2, len(Capability(f).events()))
        self.assertIn(self.g["A-EVENT"], Capability(f).events())
        self.assertIn(self.g["B-EVENT"], Capability(f).events())

    def test_instance(self):
        e1 = self.g.register("PHYSICAL-EVENT")
        e2 = self.g.register("MENTAL-EVENT")

        c = Capability.instance(self.g, "TEST-CAPABILITY", "SomeMP", ["TEST.PHYSICAL-EVENT", "TEST.MENTAL-EVENT"])
        self.assertEqual("TEST.TEST-CAPABILITY", c.frame.name())
        self.assertEqual("SomeMP", c.mp_name())
        self.assertEqual([e1, e2], c.events())

    def test_run(self):
        from backend.models.mps import OutputMethod
        from backend.models.output import OutputXMR, OutputXMRTemplate

        out = []

        class TestMP(OutputMethod):
            def run(self):
                nonlocal out
                out.append(self.output.frame)
                out.append(self.callback.frame)

        MPRegistry.register(TestMP)

        capability = Capability.instance(self.g, "TEST-CAPABILITY", TestMP.__name__, ["ONT.EVENT"])

        output = OutputXMR.build(self.g, OutputXMRTemplate.Type.PHYSICAL, capability, "TEST")
        callback = Callback.build(self.g, "DECISION", "EFFECTOR")

        capability.run(None, output, callback)

        self.assertEqual([output.frame, callback.frame], out)


class CallbackTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("EXE")

    def test_decision(self):
        decision = self.g.register("DECISION")

        callback = self.g.register("CALLBACK")
        callback["FOR-DECISION"] = decision

        self.assertEqual(decision, Callback(callback).decision())

    def test_effector(self):
        effector = self.g.register("EFFECTOR")

        callback = self.g.register("CALLBACK")
        callback["FOR-EFFECTOR"] = effector

        self.assertEqual(effector, Callback(callback).effector())

    def test_status(self):
        callback = self.g.register("CALLBACK")
        callback["STATUS"] = Callback.Status.WAITING

        self.assertEqual(Callback.Status.WAITING, Callback(callback).status())

    def test_build(self):
        decision = self.g.register("DECISION")
        effector = self.g.register("EFFECTOR")

        callback = Callback.build(self.g, decision, effector)

        self.assertEqual(decision, callback.decision())
        self.assertEqual(effector, callback.effector())
        self.assertEqual(Callback.Status.WAITING, callback.status())

    def test_received(self):
        callback = self.g.register("CALLBACK")
        callback["STATUS"] = Callback.Status.WAITING

        self.assertEqual(Callback.Status.WAITING, Callback(callback).status())

        Callback(callback).received()

        self.assertEqual(Callback.Status.RECEIVED, Callback(callback).status())

    def test_process(self):
        from backend.models.agenda import Decision

        decision = Decision.build(self.g, "GOAL", "PLAN", "STEP")
        effector = Effector.instance(self.g, Effector.Type.PHYSICAL, [])

        output = self.g.register("OUTPUT")
        capability = self.g.register("CAPABILITY")
        effector.reserve(decision, output, capability)

        callback = Callback.build(self.g, decision, effector)

        decision.frame["HAS-CALLBACK"] += callback.frame
        decision.frame["HAS-EFFECTOR"] += effector.frame

        self.assertIn(callback.frame._identifier, self.g)
        self.assertEqual(decision, effector.on_decision())
        self.assertEqual(output, effector.on_output())
        self.assertEqual(capability, effector.on_capability())
        self.assertIn(effector, decision.effectors())
        self.assertIn(callback, decision.callbacks())

        callback.process()

        self.assertNotIn(callback.frame._identifier, self.g)
        self.assertNotEqual(decision, effector.on_decision())
        self.assertNotEqual(output, effector.on_output())
        self.assertNotEqual(capability, effector.on_capability())
        self.assertNotIn(effector, decision.effectors())
        self.assertNotIn(callback, decision.callbacks())