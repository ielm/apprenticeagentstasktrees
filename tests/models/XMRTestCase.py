from backend.models.graph import Frame, Literal, Network
from backend.models.tmr import TMR
from backend.models.vmr import VMR
from backend.models.xmr import AMR, MMR, XMR

import time
import unittest


class XMRTestCase(unittest.TestCase):

    def test_signal(self):
        frame = Frame("TEST")
        frame["SIGNAL"] = XMR.Signal.INPUT

        self.assertEqual(XMR.Signal.INPUT, XMR(frame).signal())

    def test_is_input(self):
        frame = Frame("TEST")

        frame["SIGNAL"] = XMR.Signal.INPUT
        self.assertTrue(XMR(frame).is_input())

        frame["SIGNAL"] = XMR.Signal.OUTPUT
        self.assertFalse(XMR(frame).is_input())

    def test_is_output(self):
        frame = Frame("TEST")

        frame["SIGNAL"] = XMR.Signal.OUTPUT
        self.assertTrue(XMR(frame).is_output())

        frame["SIGNAL"] = XMR.Signal.INPUT
        self.assertFalse(XMR(frame).is_output())

    def test_status(self):
        frame = Frame("TEST")
        frame["STATUS"] = XMR.InputStatus.RECEIVED

        self.assertEqual(XMR.InputStatus.RECEIVED, XMR(frame).status())

    def test_type(self):
        frame = Frame("TEST")
        frame["TYPE"] = XMR.Type.LANGUAGE

        self.assertEqual(XMR.Type.LANGUAGE, XMR(frame).type())

    def test_source(self):
        n = Network()
        g = n.register("TEST")
        source = g.register("SOURCE")

        frame = g.register("XMR")
        frame["SOURCE"] = source

        self.assertEqual(source, XMR(frame).source())

    def test_graph(self):
        n = Network()
        g = n.register("TEST")
        f = g.register("XMR")
        f["REFERS-TO-GRAPH"] = Literal(g._namespace)

        self.assertEqual(g, XMR(f).graph(n))

    def test_timestamp(self):
        now = time.time()

        frame = Frame("TEST")
        frame["TIMESTAMP"] = now

        self.assertEqual(now, XMR(frame).timestamp())

    def test_root(self):
        n = Network()
        g = n.register("TEST")
        root = g.register("ROOT")

        frame = g.register("XMR")
        frame["ROOT"] = root

        self.assertEqual(root, XMR(frame).root())

    def test_capability(self):
        from backend.models.effectors import Capability

        n = Network()
        g = n.register("TEST")
        capability = Capability.instance(g, "TestCapability", "TestMP", [])

        frame = g.register("XMR")
        frame["REQUIRES"] = capability.frame

        self.assertEqual(capability, XMR(frame).capability())

    def test_render(self):
        n = Network()
        g = n.register("TEST")
        frame = g.register("XMR", generate_index=True)

        self.assertEqual("TEST.XMR.1", XMR(frame).render())

    def test_set_status(self):
        frame = Frame("TEST")

        frame["STATUS"] = XMR.InputStatus.RECEIVED
        self.assertEqual(XMR.InputStatus.RECEIVED, XMR(frame).status())

        XMR(frame).set_status(XMR.InputStatus.ACKNOWLEDGED)
        self.assertEqual(XMR.InputStatus.ACKNOWLEDGED, XMR(frame).status())

    def test_instance(self):
        from backend.models.effectors import Capability

        n = Network()
        g = n.register("TEST")
        graph = n.register("TARGET")

        source = g.register("SOURCE")
        root = graph.register("ROOT")
        capability = Capability.instance(g, "TestCapability", "TestMP", [])

        xmr = XMR.instance(g, graph, XMR.Signal.INPUT, XMR.Type.LANGUAGE, XMR.InputStatus.RECEIVED, source, root)

        self.assertEqual(graph, xmr.graph(n))
        self.assertTrue(xmr.is_input())
        self.assertEqual(XMR.Type.LANGUAGE, xmr.type())
        self.assertEqual(XMR.InputStatus.RECEIVED, xmr.status())
        self.assertEqual(source, xmr.source())
        self.assertEqual(root, xmr.root())

        xmr = XMR.instance(g, graph, XMR.Signal.OUTPUT, XMR.Type.LANGUAGE, XMR.OutputStatus.FINISHED, source, root, capability=capability)

        self.assertEqual(graph, xmr.graph(n))
        self.assertTrue(xmr.is_output())
        self.assertEqual(XMR.Type.LANGUAGE, xmr.type())
        self.assertEqual(XMR.OutputStatus.FINISHED, xmr.status())
        self.assertEqual(source, xmr.source())
        self.assertEqual(root, xmr.root())
        self.assertEqual(capability, xmr.capability())

    def test_instance_uses_correct_concept_type(self):
        n = Network()
        n.register("EXE")
        g = n.register("TEST")
        graph = n.register("TARGET")

        from backend.models.bootstrap import Bootstrap
        Bootstrap.bootstrap_resource(n, "backend.resources", "exe.knowledge")

        xmr = XMR.instance(g, graph, XMR.Signal.INPUT, XMR.Type.ACTION, XMR.InputStatus.RECEIVED, "TEST.SOURCE", "TARGET.ROOT")
        self.assertTrue(xmr.frame ^ "EXE.AMR")

        xmr = XMR.instance(g, graph, XMR.Signal.INPUT, XMR.Type.MENTAL, XMR.InputStatus.RECEIVED, "TEST.SOURCE", "TARGET.ROOT")
        self.assertTrue(xmr.frame ^ "EXE.MMR")

        xmr = XMR.instance(g, graph, XMR.Signal.INPUT, XMR.Type.LANGUAGE, XMR.InputStatus.RECEIVED, "TEST.SOURCE", "TARGET.ROOT")
        self.assertTrue(xmr.frame ^ "EXE.TMR")

        xmr = XMR.instance(g, graph, XMR.Signal.INPUT, XMR.Type.VISUAL, XMR.InputStatus.RECEIVED, "TEST.SOURCE", "TARGET.ROOT")
        self.assertTrue(xmr.frame ^ "EXE.VMR")

    def test_from_instance(self):
        n = Network()
        g = n.register("TEST")

        xmr1 = g.register("XMR", generate_index=True)
        xmr1["TYPE"] = XMR.Type.ACTION

        xmr2 = g.register("XMR", generate_index=True)
        xmr2["TYPE"] = XMR.Type.MENTAL

        xmr3 = g.register("XMR", generate_index=True)
        xmr3["TYPE"] = XMR.Type.LANGUAGE

        xmr4 = g.register("XMR", generate_index=True)
        xmr4["TYPE"] = XMR.Type.VISUAL

        self.assertIsInstance(XMR.from_instance(xmr1), AMR)
        self.assertIsInstance(XMR.from_instance(xmr2), MMR)
        self.assertIsInstance(XMR.from_instance(xmr3), TMR)
        self.assertIsInstance(XMR.from_instance(xmr4), VMR)


class AMRTestCase(unittest.TestCase):

    def test_render(self):
        n = Network()
        g = n.register("TEST")
        f = g.register("AMR", generate_index=True)

        self.assertEqual("TEST.AMR.1", AMR(f).render())

    def test_render_with_contents(self):
        n = Network()

        g = n.register("SELF")
        g.register("ROBOT", generate_index=True)

        env = n.register("ENV")
        env.register("BRACKET", generate_index=True)

        amr_graph = n.register("AMR")
        root = amr_graph.register("GET", generate_index=True)
        root["AGENT"] = "SELF.ROBOT.1"
        root["THEME"] = "ENV.BRACKET.1"

        amr = AMR.instance(g, "AMR", XMR.Signal.OUTPUT, XMR.Type.ACTION, XMR.OutputStatus.PENDING, "SELF.ROBOT.1", root)

        self.assertEqual("I am taking the GET(ENV.BRACKET.1) action.", amr.render())


class MMRTestCase(unittest.TestCase):

    def test_render(self):
        n = Network()
        g = n.register("TEST")
        f = g.register("MMR", generate_index=True)

        self.assertEqual("TEST.MMR.1", MMR(f).render())

    def test_render_on_init_goal(self):
        n = Network()

        g = n.register("SELF")
        g.register("ROBOT", generate_index=True)
        goal = g.register("GOAL")
        goal["NAME"] = Literal("BUILD-A-CHAIR")

        mmr_graph = n.register("MMR")
        root = mmr_graph.register("INIT-GOAL", generate_index=True)
        root["AGENT"] = "SELF.ROBOT.1"
        root["THEME"] = goal

        mmr = MMR.instance(g, "MMR", XMR.Signal.OUTPUT, XMR.Type.MENTAL, XMR.OutputStatus.PENDING, "SELF.ROBOT.1", root)
        self.assertEqual("I am adding the BUILD-A-CHAIR goal.", mmr.render())


class TMRTestCase(unittest.TestCase):

    def test_render(self):
        frame = Frame("TMR")
        frame["SENTENCE"] = Literal("This is the test sentence.")

        self.assertEqual("This is the test sentence.", TMR(frame).render())


class VMRTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.env = self.n.register("ENV")
        self.ont = self.n.register("ONT")

        self.env.register("EPOCH")
        self.ont.register("LOCATION")

    def test_render(self):
        g = self.n.register("TEST")
        f = g.register("VMR", generate_index=True)

        self.assertEqual("TEST.VMR.1", VMR(f).render())

    def test_render_entered_location(self):
        from backend.models.environment import Environment

        g = self.n.register("TEST")

        human = g.register("HUMAN")
        location = g.register("LOCATION")

        env = Environment(self.env)

        epoch = env.advance()
        env.enter(human, location)

        vmr_graph = self.n.register("VMR")
        vmr_graph.register("EVENTS")

        vmr = VMR.instance(g, "VMR", XMR.Signal.INPUT, XMR.Type.VISUAL, XMR.InputStatus.RECEIVED, "SELF.ROBOT.1", "")
        vmr.frame["EPOCH"] = epoch

        self.assertEqual("I see that TEST.HUMAN is now in the environment, at the TEST.LOCATION.", vmr.render())

        human["HAS-NAME"] = Literal("Jake")
        location["HAS-NAME"] = Literal("workshop")
        self.assertEqual("I see that Jake is now in the environment, at the workshop.", vmr.render())

    def test_render_changed_location(self):
        from backend.models.environment import Environment

        g = self.n.register("TEST")

        human = g.register("HUMAN")
        location1 = g.register("LOCATION", generate_index=True)
        location2 = g.register("LOCATION", generate_index=True)

        env = Environment(self.env)

        epoch = env.advance()
        env.enter(human, location1)

        epoch = env.advance()
        env.enter(human, location2)

        vmr_graph = self.n.register("VMR")
        vmr_graph.register("EVENTS")

        vmr = VMR.instance(g, "VMR", XMR.Signal.INPUT, XMR.Type.VISUAL, XMR.InputStatus.RECEIVED, "SELF.ROBOT.1", "")
        vmr.frame["EPOCH"] = epoch

        self.assertEqual("I see that TEST.HUMAN moved from the TEST.LOCATION.1 to the TEST.LOCATION.2.", vmr.render())

        human["HAS-NAME"] = Literal("Jake")
        location1["HAS-NAME"] = Literal("workshop")
        location2["HAS-NAME"] = Literal("bench")
        self.assertEqual("I see that Jake moved from the workshop to the bench.", vmr.render())

    def test_render_left_environment(self):
        from backend.models.environment import Environment

        g = self.n.register("TEST")

        human = g.register("HUMAN")
        location = g.register("LOCATION", generate_index=True)

        env = Environment(self.env)

        epoch = env.advance()
        env.enter(human, location)

        epoch = env.advance()
        env.exit(human)

        vmr_graph = self.n.register("VMR")
        vmr_graph.register("EVENTS")

        vmr = VMR.instance(g, "VMR", XMR.Signal.INPUT, XMR.Type.VISUAL, XMR.InputStatus.RECEIVED, "SELF.ROBOT.1", "")
        vmr.frame["EPOCH"] = epoch

        self.assertEqual("I see that TEST.HUMAN has left the environment.", vmr.render())

        human["HAS-NAME"] = Literal("Jake")
        location["HAS-NAME"] = Literal("workshop")
        self.assertEqual("I see that Jake has left the environment.", vmr.render())

    def test_render_observed_event(self):

        human = self.env.register("HUMAN")
        bracket = self.env.register("BRACKET")

        vmr_graph = self.n.register("VMR")
        vmr_graph.register("EVENTS")

        root = vmr_graph.register("GET", generate_index=True)
        root["AGENT"] = "ENV.HUMAN"
        root["THEME"] = "ENV.BRACKET"

        events = vmr_graph.register("EVENTS")
        events["HAS-EVENT"] += root

        vmr = VMR.instance(self.n.register("TEST"), "VMR", XMR.Signal.INPUT, XMR.Type.VISUAL, XMR.InputStatus.RECEIVED, "SELF.ROBOT.1", "")
        vmr.frame["EPOCH"] = self.env.register("EPOCH", isa="ENV.EPOCH", generate_index=True)

        self.assertEqual("I see that ENV.HUMAN did GET(ENV.BRACKET).", vmr.render())

        human["HAS-NAME"] = Literal("Jake")
        bracket["HAS-NAME"] = Literal("bracket")
        self.assertEqual("I see that Jake did GET(bracket).", vmr.render())

    def test_render_multiple_observations(self):

        human = self.env.register("HUMAN")
        bracket = self.env.register("BRACKET")

        vmr_graph = self.n.register("VMR")
        vmr_graph.register("EVENTS")

        get = vmr_graph.register("GET", generate_index=True)
        get["AGENT"] = "ENV.HUMAN"
        get["THEME"] = "ENV.BRACKET"

        hold = vmr_graph.register("HOLD", generate_index=True)
        hold["AGENT"] = "ENV.HUMAN"
        hold["THEME"] = "ENV.BRACKET"

        events = vmr_graph.register("EVENTS")
        events["HAS-EVENT"] += get
        events["HAS-EVENT"] += hold

        vmr = VMR.instance(self.n.register("TEST"), "VMR", XMR.Signal.INPUT, XMR.Type.VISUAL, XMR.InputStatus.RECEIVED, "SELF.ROBOT.1", "")
        vmr.frame["EPOCH"] = self.env.register("EPOCH", isa="ENV.EPOCH", generate_index=True)

        self.assertEqual("I see that ENV.HUMAN did GET(ENV.BRACKET); and I see that ENV.HUMAN did HOLD(ENV.BRACKET).", vmr.render())

        human["HAS-NAME"] = Literal("Jake")
        bracket["HAS-NAME"] = Literal("bracket")
        self.assertEqual("I see that Jake did GET(bracket); and I see that Jake did HOLD(bracket).", vmr.render())