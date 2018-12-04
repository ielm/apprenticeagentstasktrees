from backend.models.graph import Frame, Graph, Literal, Network
from backend.models.output import OutputXMR, OutputXMRTemplate
import unittest


class OutputXMRTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("TEST")
        self.capability = self.g.register("CAPABILITY")

    def test_type(self):
        f = self.g.register("XMR")
        f["TYPE"] = OutputXMRTemplate.Type.PHYSICAL

        self.assertEqual(OutputXMRTemplate.Type.PHYSICAL, OutputXMR(f).type())

    def test_capability(self):
        f = self.g.register("XMR")
        f["REQUIRES"] = self.capability

        self.assertEqual(self.capability, OutputXMR(f).capability())

    def test_graph(self):
        f = self.g.register("XMR")
        f["REFERS-TO-GRAPH"] = Literal("TEST")

        self.assertEqual(self.g, OutputXMR(f).graph(self.n))

    def test_status(self):
        f = self.g.register("XMR")
        f["STATUS"] = OutputXMR.Status.PENDING

        self.assertEqual(OutputXMR.Status.PENDING, OutputXMR(f).status())

    def test_root(self):
        f = self.g.register("XMR")
        self.assertIsNone(OutputXMR(f).root())

        root = self.g.register("ROOT")
        f["ROOT"] = root

        self.assertEqual(root, OutputXMR(f).root())

    def test_build(self):
        root = self.g.register("ROOT")

        xmr = OutputXMR.build(self.g, OutputXMRTemplate.Type.PHYSICAL, self.capability, "TEST", root=root)
        self.assertEqual(OutputXMRTemplate.Type.PHYSICAL, xmr.type())
        self.assertEqual(self.capability, xmr.capability())
        self.assertEqual(self.g, xmr.graph(self.n))
        self.assertEqual(OutputXMR.Status.PENDING, xmr.status())
        self.assertEqual(root, xmr.root())


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
        f["TYPE"] = OutputXMRTemplate.Type.PHYSICAL

        self.assertEqual(OutputXMRTemplate.Type.PHYSICAL, OutputXMRTemplate(self.g).type())

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
        output = OutputXMRTemplate.build(self.n, "Test Name", OutputXMRTemplate.Type.PHYSICAL, self.capability, ["$var1", "$var2"])

        self.assertEqual("Test Name", output.name())
        self.assertEqual(OutputXMRTemplate.Type.PHYSICAL, output.type())
        self.assertEqual("TEST.CAPABILITY", output.capability().name())
        self.assertEqual(["$var1", "$var2"], output.params())

    def test_create(self):
        agent = self.n.register(Graph("SELF"))

        output = OutputXMRTemplate.build(self.n, "Test Name", OutputXMRTemplate.Type.PHYSICAL, self.capability, [])
        f = output.graph.register("FRAME", generate_index=True)

        xmr = output.create(self.n, agent, [])
        self.assertEqual("SELF.XMR.1", xmr.frame.name())
        self.assertEqual(OutputXMRTemplate.Type.PHYSICAL, xmr.type())
        self.assertEqual("TEST.CAPABILITY", xmr.capability().name())
        self.assertEqual(OutputXMR.Status.PENDING, xmr.status())
        self.assertEqual(self.n["XMR#1"], xmr.graph(self.n))
        self.assertIn("XMR#1.FRAME.1", xmr.graph(self.n))

    def test_create_with_root(self):
        agent = self.n.register(Graph("SELF"))

        output = OutputXMRTemplate.build(self.n, "Test Name", OutputXMRTemplate.Type.PHYSICAL, self.capability, [])
        f = output.graph.register("FRAME", generate_index=True)

        output.set_root(f)

        xmr = output.create(self.n, agent, [])
        self.assertEqual("SELF.XMR.1", xmr.frame.name())
        self.assertEqual(xmr.graph(self.n)["XMR#1.FRAME.1"], xmr.root())

    def test_create_with_properties(self):
        agent = self.n.register(Graph("SELF"))

        output = OutputXMRTemplate.build(self.n, "Test Name", OutputXMRTemplate.Type.PHYSICAL, self.capability, [])
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

        output = OutputXMRTemplate.build(self.n, "Test Name", OutputXMRTemplate.Type.PHYSICAL, self.capability, ["$var1", "$var2"])
        f = output.graph.register("FRAME", generate_index=True)
        f["PROP1"] = Literal("$var1")
        f["PROP2"] = Literal("$var1")
        f["PROP3"] = Literal("$var2")

        xmr = output.create(self.n, agent, ["a", "b"])
        self.assertEqual("a", xmr.graph(self.n)["XMR#1.FRAME.1"]["PROP1"])
        self.assertEqual("a", xmr.graph(self.n)["XMR#1.FRAME.1"]["PROP2"])
        self.assertEqual("b", xmr.graph(self.n)["XMR#1.FRAME.1"]["PROP3"])