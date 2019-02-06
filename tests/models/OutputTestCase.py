from backend.models.graph import Frame, Graph, Literal, Network
from backend.models.output import OutputXMRTemplate
from backend.models.xmr import XMR
import unittest


class OutputXMRTemplateTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("TEST")
        self.capability = self.g.register("CAPABILITY")

    def test_anchor(self):
        f1 = self.g.register("TEMPLATE-ANCHOR", generate_index=True)
        f2 = self.g.register("FRAME", generate_index=True)
        f3 = self.g.register("FRAME", generate_index=True)

        self.assertEqual(f1, OutputXMRTemplate(self.g).anchor())

    def test_name(self):
        f = self.g.register("TEMPLATE-ANCHOR", generate_index=True)
        f["NAME"] = Literal("Test Name")

        self.assertEqual("Test Name", OutputXMRTemplate(self.g).name())

    def test_type(self):
        f = self.g.register("TEMPLATE-ANCHOR", generate_index=True)
        f["TYPE"] = XMR.Type.ACTION

        self.assertEqual(XMR.Type.ACTION, OutputXMRTemplate(self.g).type())

    def test_capability(self):
        f = self.g.register("TEMPLATE-ANCHOR", generate_index=True)
        f["REQUIRES"] = self.capability

        self.assertEqual(self.capability, OutputXMRTemplate(self.g).capability())

    def test_params(self):
        f = self.g.register("TEMPLATE-ANCHOR", generate_index=True)
        f["PARAMS"] += Literal("$var1")
        f["PARAMS"] += Literal("$var2")

        self.assertEqual(["$var1", "$var2"], OutputXMRTemplate(self.g).params())

    def test_root(self):
        f = self.g.register("TEMPLATE-ANCHOR", generate_index=True)
        self.assertIsNone(OutputXMRTemplate(self.g).root())

        root = self.g.register("ROOT")
        f["ROOT"] = root

        self.assertEqual(root, OutputXMRTemplate(self.g).root())

    def test_build(self):
        output = OutputXMRTemplate.build(self.n, "Test Name", XMR.Type.ACTION, self.capability, ["$var1", "$var2"])

        self.assertEqual("Test Name", output.name())
        self.assertEqual(XMR.Type.ACTION, output.type())
        self.assertEqual("TEST.CAPABILITY", output.capability().name())
        self.assertEqual(["$var1", "$var2"], output.params())

    def test_create(self):
        agent = self.n.register(Graph("SELF"))

        output = OutputXMRTemplate.build(self.n, "Test Name", XMR.Type.ACTION, self.capability, [])
        f = output.graph.register("FRAME", generate_index=True)

        xmr = output.create(self.n, agent, [])
        self.assertEqual("SELF.XMR.1", xmr.frame.name())
        self.assertEqual(XMR.Type.ACTION, xmr.type())
        self.assertEqual("TEST.CAPABILITY", xmr.capability().frame.name())
        self.assertEqual(XMR.OutputStatus.PENDING, xmr.status())
        self.assertEqual(self.n["XMR#1"], xmr.graph(self.n))
        self.assertIn("XMR#1.FRAME.1", xmr.graph(self.n))

    def test_create_with_root(self):
        agent = self.n.register(Graph("SELF"))

        output = OutputXMRTemplate.build(self.n, "Test Name", XMR.Type.ACTION, self.capability, [])
        f = output.graph.register("FRAME", generate_index=True)

        output.set_root(f)

        xmr = output.create(self.n, agent, [])
        self.assertEqual("SELF.XMR.1", xmr.frame.name())
        self.assertEqual(xmr.graph(self.n)["XMR#1.FRAME.1"], xmr.root())

    def test_create_with_properties(self):
        agent = self.n.register(Graph("SELF"))

        output = OutputXMRTemplate.build(self.n, "Test Name", XMR.Type.ACTION, self.capability, [])
        f1 = output.graph.register("FRAME", generate_index=True)
        f2 = output.graph.register("FRAME", generate_index=True)
        f3 = self.g.register("OTHER", generate_index=True)

        f1["PROP1"] = Literal("a")
        f1["PROP2"] = Literal("b")
        f1["PROP3"] = f2
        f1["PROP4"] = f3

        xmr = output.create(self.n, agent, [])
        self.assertEqual("a", xmr.graph(self.n)["XMR#1.FRAME.1"]["PROP1"])
        self.assertEqual("b", xmr.graph(self.n)["XMR#1.FRAME.1"]["PROP2"])
        self.assertEqual(xmr.graph(self.n)["XMR#1.FRAME.2"], xmr.graph(self.n)["XMR#1.FRAME.1"]["PROP3"])
        self.assertEqual(f3, xmr.graph(self.n)["XMR#1.FRAME.1"]["PROP4"])

    def test_create_with_parameters(self):
        agent = self.n.register(Graph("SELF"))

        output = OutputXMRTemplate.build(self.n, "Test Name", XMR.Type.ACTION, self.capability, ["$var1", "$var2"])
        f = output.graph.register("FRAME", generate_index=True)
        f["PROP1"] = Literal("$var1")
        f["PROP2"] = Literal("$var1")
        f["PROP3"] = Literal("$var2")

        xmr = output.create(self.n, agent, ["a", "b"])
        self.assertEqual("a", xmr.graph(self.n)["XMR#1.FRAME.1"]["PROP1"])
        self.assertEqual("a", xmr.graph(self.n)["XMR#1.FRAME.1"]["PROP2"])
        self.assertEqual("b", xmr.graph(self.n)["XMR#1.FRAME.1"]["PROP3"])

    def test_create_with_transient_parameters(self):
        exe = self.n.register("EXE")
        exe.register("TRANSIENT-FRAME")

        agent = self.n.register(Graph("SELF"))
        agent.register("TEST")

        output = OutputXMRTemplate.build(self.n, "Test Name", XMR.Type.ACTION, self.capability, ["$var1", "$var2"])
        f = output.graph.register("FRAME", generate_index=True)
        f["PROP1"] = Literal("$var1")
        f["PROP2"] = Literal("$var1")
        f["PROP3"] = Literal("$var2")

        transient = self.g.register("TRANSIENT-FRAME", isa="EXE.TRANSIENT-FRAME", generate_index=True)
        transient["INSTANCE-OF"] = "SELF.TEST"
        transient["PROP4"] = 123
        transient["PROP5"] = 456

        xmr = output.create(self.n, agent, ["a", transient._identifier])

        self.assertEqual("a", xmr.graph(self.n)["XMR#1.FRAME.1"]["PROP1"])
        self.assertEqual("a", xmr.graph(self.n)["XMR#1.FRAME.1"]["PROP2"])
        self.assertEqual("XMR#1.TEST.1", xmr.graph(self.n)["XMR#1.FRAME.1"]["PROP3"])

        self.assertEqual(123, xmr.graph(self.n)["XMR#1.TEST.1"]["PROP4"])
        self.assertEqual(456, xmr.graph(self.n)["XMR#1.TEST.1"]["PROP5"])

    def test_lookup(self):
        template1 = OutputXMRTemplate.build(self.n, "Test 1", XMR.Type.ACTION, self.capability, [])
        template2 = OutputXMRTemplate.build(self.n, "Test 2", XMR.Type.ACTION, self.capability, [])

        self.assertEqual(template1, OutputXMRTemplate.lookup(self.n, "Test 1"))
        self.assertEqual(template2, OutputXMRTemplate.lookup(self.n, "Test 2"))
        self.assertIsNone(OutputXMRTemplate.lookup(self.n, "Test 3"))

    def test_list(self):
        template1 = OutputXMRTemplate.build(self.n, "Test 1", XMR.Type.ACTION, self.capability, [])
        template2 = OutputXMRTemplate.build(self.n, "Test 2", XMR.Type.ACTION, self.capability, [])
        other = self.n.register("OTHER")

        self.assertEqual(2, len(OutputXMRTemplate.list(self.n)))
        self.assertIn(template1, OutputXMRTemplate.list(self.n))
        self.assertIn(template2, OutputXMRTemplate.list(self.n))
        self.assertNotIn(other, OutputXMRTemplate.list(self.n))