from backend.models.effectors import Callback, Capability, Effector
from backend.models.mps import MPRegistry, OutputMethod
from backend.models.xmr import XMR

from ontograph import graph
from ontograph.Frame import Frame
from ontograph.Space import Space

import unittest


class EffectorTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()

        self.g = Space("EXE")
        self.effector = Frame("@EXE.EFFECTOR")

        self.physical_effector = Frame("@EXE.PHYSICAL-EFFECTOR").add_parent(Frame("@EXE.EFFECTOR"))
        self.verbal_effector = Frame("@EXE.VERBAL-EFFECTOR").add_parent(Frame("@EXE.EFFECTOR"))
        self.mental_effector = Frame("@EXE.MENTAL-EFFECTOR").add_parent(Frame("@EXE.EFFECTOR"))

    def test_effector_type(self):
        f1 = Frame("@EXE.TEST-EFFECTOR.?").add_parent(self.physical_effector)
        f2 = Frame("@EXE.TEST-EFFECTOR.?").add_parent(self.verbal_effector)
        f3 = Frame("@EXE.TEST-EFFECTOR.?").add_parent(self.mental_effector)

        self.assertEqual(Effector.Type.PHYSICAL, Effector(f1).type())
        self.assertEqual(Effector.Type.VERBAL, Effector(f2).type())
        self.assertEqual(Effector.Type.MENTAL, Effector(f3).type())

    def test_effector_status(self):
        f = Frame("@EXE.TEST-EFFECTOR").add_parent(self.effector)

        f["STATUS"] = Effector.Status.FREE
        self.assertTrue(Effector(f).is_free())

        f["STATUS"] = Effector.Status.OPERATING
        self.assertFalse(Effector(f).is_free())

    def test_effector_capabilities(self):
        f1 = Frame("@EXE.TEST-EFFECTOR").add_parent(self.effector)
        f2 = Frame("@EXE.CAPABILITY.?")
        f3 = Frame("@EXE.CAPABILITY.?")

        self.assertEqual([], Effector(f1).capabilities())

        f1["HAS-CAPABILITY"] += f2
        f1["HAS-CAPABILITY"] += f3
        self.assertEqual([Capability(f2), Capability(f3)], Effector(f1).capabilities())

    def test_effector_on_decision(self):
        from backend.models.agenda import Decision

        decision = Decision.build(self.g, "GOAL", "PLAN", "STEP")

        f = Frame("@EXE.TEST-EFFECTOR").add_parent(self.effector)
        f["ON-DECISION"] = decision.frame

        self.assertEqual(decision, Effector(f).on_decision())

    def test_effector_on_output(self):
        output = XMR.instance(self.g, "TEST", XMR.Signal.OUTPUT, XMR.Type.ACTION, XMR.OutputStatus.PENDING, "", "", capability="CAPABILITY")

        f = Frame("@EXE.TEST-EFFECTOR").add_parent(self.effector)
        f["ON-OUTPUT"] = output.frame

        self.assertEqual(output, Effector(f).on_output())

    def test_effector_on_capability(self):
        capability = Capability.instance(self.g, "TEST-CAPABILITY", "TestMP", ["ONT.EVENT"])

        f = Frame("@EXE.TEST-EFFECTOR").add_parent(self.effector)
        f["ON-CAPABILITY"] = capability.frame

        self.assertEqual(capability, Effector(f).on_capability())

    def test_reserve(self):
        from backend.models.agenda import Decision

        effector = Effector.instance(self.g, Effector.Type.PHYSICAL, [])

        self.assertTrue(effector.is_free())
        self.assertIsNone(effector.on_decision())
        self.assertIsNone(effector.on_output())
        self.assertIsNone(effector.on_capability())

        decision = Decision.build(self.g, "GOAL", "PLAN", "STEP")
        output = XMR.instance(self.g, "TEST", XMR.Signal.OUTPUT, XMR.Type.ACTION, XMR.OutputStatus.PENDING, "", "", capability="CAPABILITY")
        capability = Capability.instance(self.g, "TEST-CAPABILITY", "TestMP", ["ONT.EVENT"])

        effector.reserve(decision, output, capability)

        self.assertFalse(effector.is_free())
        self.assertEqual(decision, effector.on_decision())
        self.assertEqual(output, effector.on_output())
        self.assertEqual(capability, effector.on_capability())

    def test_release(self):
        from backend.models.agenda import Decision

        effector = Effector.instance(self.g, Effector.Type.PHYSICAL, [])

        decision = Decision.build(self.g, "GOAL", "PLAN", "STEP")
        output = XMR.instance(self.g, "TEST", XMR.Signal.OUTPUT, XMR.Type.ACTION, XMR.OutputStatus.PENDING, "", "", capability="CAPABILITY")
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
        graph.reset()
        self.g = Space("TEST")

        MPRegistry.clear()

    def test_capability_mp(self):

        out = False

        class TestMP(OutputMethod):
            def run(self):
                nonlocal out
                out = True

        MPRegistry.register(TestMP)

        f = Frame("@TEST.CAPABILITY")
        f["MP"] = "TestMP"

        capability = Capability(f)
        self.assertEqual("TestMP", capability.mp_name())

        capability.run(None, None, None)
        self.assertTrue(out)

    def test_capability_events(self):
        f = Frame("@TEST.CAPABILITY")
        f["COVERS-EVENT"] += Frame("@TEST.A-EVENT")
        f["COVERS-EVENT"] += Frame("@TEST.B-EVENT")

        self.assertEqual(2, len(Capability(f).events()))
        self.assertIn(Frame("@TEST.A-EVENT"), Capability(f).events())
        self.assertIn(Frame("@TEST.B-EVENT"), Capability(f).events())

    def test_instance(self):
        e1 = Frame("@TEST.PHYSICAL-EVENT")
        e2 = Frame("@TEST.MENTAL-EVENT")

        c = Capability.instance(self.g, "TEST-CAPABILITY", "SomeMP", ["@TEST.PHYSICAL-EVENT", "@TEST.MENTAL-EVENT"])
        self.assertEqual("@TEST.TEST-CAPABILITY.1", c.frame.id)
        self.assertEqual("SomeMP", c.mp_name())
        self.assertEqual([e1, e2], c.events())

    def test_run(self):
        from backend.models.mps import OutputMethod

        out = []

        class TestMP(OutputMethod):
            def run(self):
                nonlocal out
                out.append(self.output.frame)
                out.append(self.callback.frame)

        MPRegistry.register(TestMP)

        capability = Capability.instance(self.g, "TEST-CAPABILITY", TestMP.__name__, ["ONT.EVENT"])

        output = XMR.instance(self.g, "TEST", XMR.Signal.OUTPUT, XMR.Type.ACTION, XMR.OutputStatus.PENDING, "", "", capability=capability)
        callback = Callback.build(self.g, "DECISION", "EFFECTOR")

        capability.run(None, output, callback)

        self.assertEqual([output.frame, callback.frame], out)


class CallbackTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()

    def test_decision(self):
        decision = Frame("@EXE.DECISION")

        callback = Frame("@EXE.CALLBACK")
        callback["FOR-DECISION"] = decision

        self.assertEqual(decision, Callback(callback).decision())

    def test_effector(self):
        effector = Frame("@EXE.EFFECTOR")

        callback = Frame("@EXE.CALLBACK")
        callback["FOR-EFFECTOR"] = effector

        self.assertEqual(effector, Callback(callback).effector())

    def test_status(self):
        callback = Frame("@EXE.CALLBACK")
        callback["STATUS"] = Callback.Status.WAITING

        self.assertEqual(Callback.Status.WAITING, Callback(callback).status())

    def test_build(self):
        decision = Frame("@EXE.DECISION")
        effector = Frame("@EXE.EFFECTOR")

        callback = Callback.build(Space("EXE"), decision, effector)

        self.assertEqual(decision, callback.decision())
        self.assertEqual(effector, callback.effector())
        self.assertEqual(Callback.Status.WAITING, callback.status())

    def test_received(self):
        callback = Frame("@EXE.CALLBACK")
        callback["STATUS"] = Callback.Status.WAITING

        self.assertEqual(Callback.Status.WAITING, Callback(callback).status())

        Callback(callback).received()

        self.assertEqual(Callback.Status.RECEIVED, Callback(callback).status())

    def test_process(self):
        from backend.models.agenda import Decision

        space = Space("EXE")

        decision = Decision.build(space, "GOAL", "PLAN", "STEP")
        effector = Effector.instance(space, Effector.Type.PHYSICAL, [])

        output = Frame("@EXE.OUTPUT")
        capability = Frame("@EXE.CAPABILITY")
        effector.reserve(decision, output, capability)

        callback = Callback.build(space, decision, effector)

        decision.frame["HAS-CALLBACK"] += callback.frame
        decision.frame["HAS-EFFECTOR"] += effector.frame

        self.assertIn(callback.frame.id, space)
        self.assertEqual(decision, effector.on_decision())
        self.assertEqual(output, effector.on_output())
        self.assertEqual(capability, effector.on_capability())
        self.assertIn(effector, decision.effectors())
        self.assertIn(callback, decision.callbacks())

        callback.process()

        self.assertNotIn(callback.frame.id, space)
        self.assertNotEqual(decision, effector.on_decision())
        self.assertNotEqual(output, effector.on_output())
        self.assertNotEqual(capability, effector.on_capability())
        self.assertNotIn(effector, decision.effectors())
        self.assertNotIn(callback, decision.callbacks())