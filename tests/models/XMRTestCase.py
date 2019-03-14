# from backend.models.graph import Frame, Literal, Network
from backend.models.tmr import TMR
from backend.models.vmr import VMR
from backend.models.xmr import AMR, MMR, XMR
from ontograph import graph
from ontograph.Frame import Frame
from ontograph.Space import Space

import time
import unittest


class XMRTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()

    def test_signal(self):
        frame = Frame("@TEST.FRAME")
        frame["SIGNAL"] = XMR.Signal.INPUT

        self.assertEqual(XMR.Signal.INPUT, XMR(frame).signal())

    def test_is_input(self):
        frame = Frame("@TEST.FRAME")

        frame["SIGNAL"] = XMR.Signal.INPUT
        self.assertTrue(XMR(frame).is_input())

        frame["SIGNAL"] = XMR.Signal.OUTPUT
        self.assertFalse(XMR(frame).is_input())

    def test_is_output(self):
        frame = Frame("@TEST.FRAME")

        frame["SIGNAL"] = XMR.Signal.OUTPUT
        self.assertTrue(XMR(frame).is_output())

        frame["SIGNAL"] = XMR.Signal.INPUT
        self.assertFalse(XMR(frame).is_output())

    def test_status(self):
        frame = Frame("@TEST.FRAME")
        frame["STATUS"] = XMR.InputStatus.RECEIVED

        self.assertEqual(XMR.InputStatus.RECEIVED, XMR(frame).status())

    def test_type(self):
        frame = Frame("@TEST.FRAME")
        frame["TYPE"] = XMR.Type.LANGUAGE

        self.assertEqual(XMR.Type.LANGUAGE, XMR(frame).type())

    def test_source(self):
        source = Frame("@TEST.SOURCE")

        frame = Frame("@TEST.XMR")
        frame["SOURCE"] = source

        self.assertEqual(source, XMR(frame).source())

    def test_graph(self):
        f = Frame("@TEST.XMR")
        f["REFERS-TO-GRAPH"] = "TEST"

        self.assertEqual(Space("TEST"), XMR(f).graph())

    def test_timestamp(self):
        now = time.time()

        frame = Frame("@TEST.FRAME")
        frame["TIMESTAMP"] = now

        self.assertEqual(now, XMR(frame).timestamp())

    def test_root(self):
        root = Frame("@TEST.ROOT")

        frame = Frame("@TEST.XMR")
        frame["ROOT"] = root

        self.assertEqual(root, XMR(frame).root())

    def test_capability(self):
        from backend.models.effectors import Capability

        capability = Capability.instance(Space("TEST"), "TestCapability", "TestMP", [])

        frame = Frame("@TEST.XMR")
        frame["REQUIRES"] = capability.frame

        self.assertEqual(capability, XMR(frame).capability())

    def test_render(self):
        frame = Frame("@TEST.XMR.?")

        self.assertEqual("@TEST.XMR.1", XMR(frame).render())

    def test_set_status(self):
        frame = Frame("@TEST.FRAME")

        frame["STATUS"] = XMR.InputStatus.RECEIVED
        self.assertEqual(XMR.InputStatus.RECEIVED, XMR(frame).status())

        XMR(frame).set_status(XMR.InputStatus.ACKNOWLEDGED)
        self.assertEqual(XMR.InputStatus.ACKNOWLEDGED, XMR(frame).status())

    def test_instance(self):
        from backend.models.effectors import Capability

        source = Frame("@TEST.SOURCE")
        root = Frame("@TARGET.ROOT")
        capability = Capability.instance(Space("TEST"), "TestCapability", "TestMP", [])

        xmr = XMR.instance(Space("TEST"), Space("TARGET"), XMR.Signal.INPUT, XMR.Type.LANGUAGE, XMR.InputStatus.RECEIVED, source, root)

        self.assertEqual(Space("TARGET"), xmr.graph())
        self.assertTrue(xmr.is_input())
        self.assertEqual(XMR.Type.LANGUAGE, xmr.type())
        self.assertEqual(XMR.InputStatus.RECEIVED, xmr.status())
        self.assertEqual(source, xmr.source())
        self.assertEqual(root, xmr.root())

        xmr = XMR.instance(Space("TEST"), Space("TARGET"), XMR.Signal.OUTPUT, XMR.Type.LANGUAGE, XMR.OutputStatus.FINISHED, source, root, capability=capability)

        self.assertEqual(Space("TARGET"), xmr.graph())
        self.assertTrue(xmr.is_output())
        self.assertEqual(XMR.Type.LANGUAGE, xmr.type())
        self.assertEqual(XMR.OutputStatus.FINISHED, xmr.status())
        self.assertEqual(source, xmr.source())
        self.assertEqual(root, xmr.root())
        self.assertEqual(capability, xmr.capability())

    def test_instance_uses_correct_concept_type(self):
        from backend.models.bootstrap import Bootstrap
        Bootstrap.bootstrap_resource(None, "backend.resources", "exe.knowledge")

        xmr = XMR.instance(Space("TEST"), Space("TARGET"), XMR.Signal.INPUT, XMR.Type.ACTION, XMR.InputStatus.RECEIVED, "@TEST.SOURCE", "@TARGET.ROOT")
        self.assertTrue(xmr.frame ^ "@EXE.AMR")

        xmr = XMR.instance(Space("TEST"), Space("TARGET"), XMR.Signal.INPUT, XMR.Type.MENTAL, XMR.InputStatus.RECEIVED, "@TEST.SOURCE", "@TARGET.ROOT")
        self.assertTrue(xmr.frame ^ "@EXE.MMR")

        xmr = XMR.instance(Space("TEST"), Space("TARGET"), XMR.Signal.INPUT, XMR.Type.LANGUAGE, XMR.InputStatus.RECEIVED, "@TEST.SOURCE", "@TARGET.ROOT")
        self.assertTrue(xmr.frame ^ "@EXE.TMR")

        xmr = XMR.instance(Space("TEST"), Space("TARGET"), XMR.Signal.INPUT, XMR.Type.VISUAL, XMR.InputStatus.RECEIVED, "@TEST.SOURCE", "@TARGET.ROOT")
        self.assertTrue(xmr.frame ^ "@EXE.VMR")

    def test_from_instance(self):
        xmr1 = Frame("@TEST.XMR.?")
        xmr1["TYPE"] = XMR.Type.ACTION

        xmr2 = Frame("@TEST.XMR.?")
        xmr2["TYPE"] = XMR.Type.MENTAL

        xmr3 = Frame("@TEST.XMR.?")
        xmr3["TYPE"] = XMR.Type.LANGUAGE

        xmr4 = Frame("@TEST.XMR.?")
        xmr4["TYPE"] = XMR.Type.VISUAL

        self.assertIsInstance(XMR.from_instance(xmr1), AMR)
        self.assertIsInstance(XMR.from_instance(xmr2), MMR)
        self.assertIsInstance(XMR.from_instance(xmr3), TMR)
        self.assertIsInstance(XMR.from_instance(xmr4), VMR)


class AMRTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()

    def test_render(self):
        f = Frame("@TEST.AMR.1")

        self.assertEqual("@TEST.AMR.1", AMR(f).render())

    def test_render_with_contents(self):
        # n = Network()

        # g = n.register("SELF")
        Frame("@SELF.ROBOT.?")

        # env = n.register("ENV")
        Frame("@ENV.BRACKET.?")

        # amr_graph = n.register("AMR")
        root = Frame("@AMR.GET.?")
        root["AGENT"] = Frame("@SELF.ROBOT.1")
        root["THEME"] = Frame("@ENV.BRACKET.1")

        amr = AMR.instance(Space("SELF"), "AMR", XMR.Signal.OUTPUT, XMR.Type.ACTION, XMR.OutputStatus.PENDING, "@SELF.ROBOT.1", root)

        self.assertEqual("I am taking the GET(@ENV.BRACKET.1) action.", amr.render())


class MMRTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()

    def test_render(self):
        f = Frame("@TEST.MMR.?")

        self.assertEqual("@TEST.MMR.1", MMR(f).render())

    def test_render_on_init_goal(self):
        robot = Frame("@SELF.ROBOT.?")
        goal = Frame("@SELF.GOAL")
        goal["NAME"] = "BUILD-A-CHAIR"

        root = Frame("@MMR.INIT-GOAL.?")
        root["AGENT"] = robot
        root["THEME"] = goal

        mmr = MMR.instance(Space("SELF"), "MMR", XMR.Signal.OUTPUT, XMR.Type.MENTAL, XMR.OutputStatus.PENDING, "@SELF.ROBOT.1", root)
        self.assertEqual("I am adding the BUILD-A-CHAIR goal.", mmr.render())


class TMRTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()

    def test_render(self):
        frame = Frame("TMR")
        frame["SENTENCE"] = "This is the test sentence."

        self.assertEqual("This is the test sentence.", TMR(frame).render())


class VMRTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()

        self.env = Space("ENV")
        self.ont = Space("ONT")

        Frame("@ENV.EPOCH")
        Frame("@ONT.LOCATION")

    def test_render(self):
        f = Frame("@TEST.VMR.?")

        self.assertEqual("@TEST.VMR.1", VMR(f).render())

    def test_render_entered_location(self):
        from backend.models.environment import Environment

        human = Frame("@TEST.HUMAN")
        location = Frame("@TEST.LOCATION")

        env = Environment(self.env)

        epoch = env.advance()
        env.enter(human, location)

        Frame("@VMR.EVENTS")

        vmr = VMR.instance(Space("TEST"), "VMR", XMR.Signal.INPUT, XMR.Type.VISUAL, XMR.InputStatus.RECEIVED, "@SELF.ROBOT.1", "")
        vmr.frame["EPOCH"] = epoch

        self.assertEqual("I see that @TEST.HUMAN is now in the environment, at the @TEST.LOCATION.", vmr.render())

        human["HAS-NAME"] = "Jake"
        location["HAS-NAME"] = "workshop"
        self.assertEqual("I see that Jake is now in the environment, at the workshop.", vmr.render())

    def test_render_changed_location(self):
        from backend.models.environment import Environment

        human = Frame("@TEST.HUMAN")
        location1 = Frame("@TEST.LOCATION.?")
        location2 = Frame("@TEST.LOCATION.?")

        env = Environment(self.env)

        epoch = env.advance()
        env.enter(human, location1)

        epoch = env.advance()
        env.move(human, location2)

        Frame("@VMR.EVENTS")

        vmr = VMR.instance(Space("TEST"), "VMR", XMR.Signal.INPUT, XMR.Type.VISUAL, XMR.InputStatus.RECEIVED, "@SELF.ROBOT.1", "")
        vmr.frame["EPOCH"] = epoch

        self.assertEqual("I see that @TEST.HUMAN moved from the @TEST.LOCATION.1 to the @TEST.LOCATION.2.", vmr.render())

        human["HAS-NAME"] = "Jake"
        location1["HAS-NAME"] = "workshop"
        location2["HAS-NAME"] = "bench"
        self.assertEqual("I see that Jake moved from the workshop to the bench.", vmr.render())

    def test_render_left_environment(self):
        from backend.models.environment import Environment

        human = Frame("@TEST.HUMAN")
        location = Frame("@TEST.LOCATION.?")

        env = Environment(self.env)

        epoch = env.advance()
        env.enter(human, location)

        epoch = env.advance()
        env.exit(human)

        Frame("@VMR.EVENTS")

        vmr = VMR.instance(Space("TEST"), "VMR", XMR.Signal.INPUT, XMR.Type.VISUAL, XMR.InputStatus.RECEIVED, "@SELF.ROBOT.1", "")
        vmr.frame["EPOCH"] = epoch

        self.assertEqual("I see that @TEST.HUMAN has left the environment.", vmr.render())

        human["HAS-NAME"] = "Jake"
        location["HAS-NAME"] = "workshop"
        self.assertEqual("I see that Jake has left the environment.", vmr.render())

    def test_render_observed_event(self):

        human = Frame("@ENV.HUMAN")
        bracket = Frame("@ENV.BRACKET")

        Frame("@VMR.EVENTS")

        root = Frame("@VMR.GET.?")
        root["AGENT"] = human
        root["THEME"] = bracket

        events = Frame("@VMR.EVENTS")
        events["HAS-EVENT"] += root

        vmr = VMR.instance(Space("TEST"), "VMR", XMR.Signal.INPUT, XMR.Type.VISUAL, XMR.InputStatus.RECEIVED, "@SELF.ROBOT.1", "")
        vmr.frame["EPOCH"] = Frame("@ENV.EPOCH.?").add_parent("@ENV.EPOCH")

        self.assertEqual("I see that @ENV.HUMAN did GET(@ENV.BRACKET).", vmr.render())

        human["HAS-NAME"] = "Jake"
        bracket["HAS-NAME"] = "bracket"
        self.assertEqual("I see that Jake did GET(bracket).", vmr.render())

    def test_render_multiple_observations(self):

        human = Frame("@ENV.HUMAN")
        bracket = Frame("@ENV.BRACKET")

        Frame("@VMR.EVENTS")

        get = Frame("@VMR.GET.?")
        get["AGENT"] = human
        get["THEME"] = bracket

        hold = Frame("@VMR.HOLD.?")
        hold["AGENT"] = human
        hold["THEME"] = bracket

        events = Frame("@VMR.EVENTS")
        events["HAS-EVENT"] += get
        events["HAS-EVENT"] += hold

        vmr = VMR.instance(Space("TEST"), "VMR", XMR.Signal.INPUT, XMR.Type.VISUAL, XMR.InputStatus.RECEIVED, "@SELF.ROBOT.1", "")
        vmr.frame["EPOCH"] = Frame("@ENV.EPOCH.?").add_parent("@ENV.EPOCH")

        self.assertEqual("I see that @ENV.HUMAN did GET(@ENV.BRACKET); and I see that @ENV.HUMAN did HOLD(@ENV.BRACKET).", vmr.render())

        human["HAS-NAME"] = "Jake"
        bracket["HAS-NAME"] = "bracket"
        self.assertEqual("I see that Jake did GET(bracket); and I see that Jake did HOLD(bracket).", vmr.render())