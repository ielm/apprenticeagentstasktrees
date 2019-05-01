# from backend.models.graph import Frame, Graph, Literal, Network
from backend.models.output import OutputXMRTemplate
from backend.models.xmr import XMR
from ontograph import graph
from ontograph.Frame import Frame
from ontograph.Space import Space
import unittest


class OutputXMRTemplateTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()
        self.capability = Frame("@TEST.CAPABILITY")

    def test_anchor(self):
        f1 = Frame("@TEST.TEMPLATE-ANCHOR.?").add_parent("@EXE.TEMPLATE-ANCHOR")
        f2 = Frame("@TEST.FRAME.?")
        f3 = Frame("@TEST.FRAME.?")

        self.assertEqual(f1, OutputXMRTemplate(Space("TEST")).anchor())

    def test_name(self):
        f = Frame("@TEST.TEMPLATE-ANCHOR.?").add_parent("@EXE.TEMPLATE-ANCHOR")
        f["NAME"] = "Test Name"

        self.assertEqual("Test Name", OutputXMRTemplate(Space("TEST")).name())

    def test_type(self):
        f = Frame("@TEST.TEMPLATE-ANCHOR.?").add_parent("@EXE.TEMPLATE-ANCHOR")
        f["TYPE"] = XMR.Type.ACTION

        self.assertEqual(XMR.Type.ACTION, OutputXMRTemplate(Space("TEST")).type())

    def test_capability(self):
        f = Frame("@TEST.TEMPLATE-ANCHOR.?").add_parent("@EXE.TEMPLATE-ANCHOR")
        f["REQUIRES"] = self.capability

        self.assertEqual(self.capability, OutputXMRTemplate(Space("TEST")).capability())

    def test_params(self):
        f = Frame("@TEST.TEMPLATE-ANCHOR.?").add_parent("@EXE.TEMPLATE-ANCHOR")
        f["PARAMS"] += "$var1"
        f["PARAMS"] += "$var2"

        self.assertEqual(["$var1", "$var2"], OutputXMRTemplate(Space("TEST")).params())

    def test_root(self):
        f = Frame("@TEST.TEMPLATE-ANCHOR.?").add_parent("@EXE.TEMPLATE-ANCHOR")
        self.assertIsNone(OutputXMRTemplate(Space("TEST")).root())

        root = Frame("@TEST.ROOT")
        f["ROOT"] = root

        self.assertEqual(root, OutputXMRTemplate(Space("TEST")).root())

    def test_build(self):
        output = OutputXMRTemplate.build("Test Name", XMR.Type.ACTION, self.capability, ["$var1", "$var2"])

        self.assertEqual("Test Name", output.name())
        self.assertEqual(XMR.Type.ACTION, output.type())
        self.assertEqual("@TEST.CAPABILITY", output.capability().frame.id)
        self.assertEqual(["$var1", "$var2"], output.params())

    def test_create(self):
        output = OutputXMRTemplate.build("Test Name", XMR.Type.ACTION, self.capability, [])
        f = Frame("@" + output.space.name + ".FRAME.?")

        xmr = output.create(Space("SELF"), [])
        self.assertEqual("@SELF.XMR.1", xmr.frame.id)
        self.assertEqual(XMR.Type.ACTION, xmr.type())
        self.assertEqual("@TEST.CAPABILITY", xmr.capability().frame.id)
        self.assertEqual(XMR.OutputStatus.PENDING, xmr.status())
        self.assertEqual(Space("XMR#1"), xmr.space())
        self.assertIn("@XMR#1.FRAME.1", xmr.space())

    def test_create_with_root(self):
        output = OutputXMRTemplate.build("Test Name", XMR.Type.ACTION, self.capability, [])
        f = Frame("@" + output.space.name + ".FRAME.?")

        output.set_root(f)

        xmr = output.create(Space("SELF"), [])
        self.assertEqual("@SELF.XMR.1", xmr.frame.id)
        self.assertEqual(Frame("@XMR#1.FRAME.1"), xmr.root())

    def test_create_with_properties(self):
        output = OutputXMRTemplate.build("Test Name", XMR.Type.ACTION, self.capability, [])
        f1 = Frame("@" + output.space.name + ".FRAME.?")
        f2 = Frame("@" + output.space.name + ".FRAME.?")
        f3 = Frame("@SELF.OTHER.?")

        f1["PROP1"] = "a"
        f1["PROP2"] = "b"
        f1["PROP3"] = f2
        f1["PROP4"] = f3

        xmr = output.create(Space("SELF"), [])
        self.assertEqual("a", Frame("@XMR#1.FRAME.1")["PROP1"])
        self.assertEqual("b", Frame("@XMR#1.FRAME.1")["PROP2"])
        self.assertEqual(Frame("@XMR#1.FRAME.2"), Frame("@XMR#1.FRAME.1")["PROP3"])
        self.assertEqual(f3, Frame("@XMR#1.FRAME.1")["PROP4"])

    def test_create_with_parameters(self):
        output = OutputXMRTemplate.build("Test Name", XMR.Type.ACTION, self.capability, ["$var1", "$var2"])
        f = Frame("@" + output.space.name + ".FRAME.?")
        f["PROP1"] = "$var1"
        f["PROP2"] = "$var1"
        f["PROP3"] = "$var2"

        xmr = output.create(Space("SELF"), ["a", "b"])
        self.assertEqual("a", Frame("@XMR#1.FRAME.1")["PROP1"])
        self.assertEqual("a", Frame("@XMR#1.FRAME.1")["PROP2"])
        self.assertEqual("b", Frame("@XMR#1.FRAME.1")["PROP3"])

    def test_create_with_transient_parameters(self):
        Frame("@EXE.TRANSIENT-FRAME")
        Frame("@SELF.TEST")

        output = OutputXMRTemplate.build("Test Name", XMR.Type.ACTION, self.capability, ["$var1", "$var2"])
        f = Frame("@" + output.space.name + ".FRAME.?")
        f["PROP1"] = "$var1"
        f["PROP2"] = "$var1"
        f["PROP3"] = "$var2"

        transient = Frame("@SELF.TRANSIENT-FRAME.?").add_parent("@EXE.TRANSIENT-FRAME")
        transient["INSTANCE-OF"] = Frame("@SELF.TEST")
        transient["PROP4"] = 123
        transient["PROP5"] = 456

        xmr = output.create(Space("SELF"), ["a", transient])

        self.assertEqual("a", Frame("@XMR#1.FRAME.1")["PROP1"])
        self.assertEqual("a", Frame("@XMR#1.FRAME.1")["PROP2"])
        self.assertEqual("@XMR#1.TEST.1", Frame("@XMR#1.FRAME.1")["PROP3"])

        self.assertEqual(123, Frame("@XMR#1.TEST.1")["PROP4"])
        self.assertEqual(456, Frame("@XMR#1.TEST.1")["PROP5"])

    def test_lookup(self):
        template1 = OutputXMRTemplate.build("Test 1", XMR.Type.ACTION, self.capability, [])
        template2 = OutputXMRTemplate.build("Test 2", XMR.Type.ACTION, self.capability, [])

        self.assertEqual(template1, OutputXMRTemplate.lookup("Test 1"))
        self.assertEqual(template2, OutputXMRTemplate.lookup("Test 2"))
        self.assertIsNone(OutputXMRTemplate.lookup("Test 3"))

    def test_list(self):
        template1 = OutputXMRTemplate.build("Test 1", XMR.Type.ACTION, self.capability, [])
        template2 = OutputXMRTemplate.build("Test 2", XMR.Type.ACTION, self.capability, [])
        other = Frame("@TEST.OTHER")

        self.assertEqual(2, len(OutputXMRTemplate.list()))
        self.assertIn(template1, OutputXMRTemplate.list())
        self.assertIn(template2, OutputXMRTemplate.list())
        self.assertNotIn(other, OutputXMRTemplate.list())