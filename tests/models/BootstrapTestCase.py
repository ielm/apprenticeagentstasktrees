from backend.models.agenda import Agenda
from backend.models.bootstrap import BootstrapAddTrigger, BootstrapAppendKnowledge, BootstrapDeclareKnowledge, BootstrapDefineOutputXMRTemplate, BootstrapRegisterMP, BootstrapTriple
# from backend.models.graph import Frame, Identifier, Literal, Network
from backend.models.mps import AgentMethod, MPRegistry
from backend.models.output import OutputXMRTemplate
from backend.models.xmr import XMR

from ontograph import graph
from ontograph.Frame import Frame
from ontograph.Index import Identifier
from ontograph.Query import IdComparator, Query
from ontograph.Space import Space

import unittest


class BootstrapDeclareKnowledgeTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()

    def test_call_makes_instance(self):
        boot = BootstrapDeclareKnowledge("TEST", "MYFRAME")
        boot()

        self.assertIn("@TEST.MYFRAME", graph)

    def test_call_makes_instance_with_specified_index(self):
        boot = BootstrapDeclareKnowledge("TEST", "MYFRAME", index=1)
        boot()

        self.assertIn("@TEST.MYFRAME.1", graph)

    def test_call_makes_instance_with_generated_index(self):
        boot = BootstrapDeclareKnowledge("TEST", "MYFRAME", index=True)
        boot()

        self.assertIn("@TEST.MYFRAME.1", graph)

    def test_call_makes_instances_with_parent(self):
        boot = BootstrapDeclareKnowledge("TEST", "MYFRAME", isa="@TEST.PARENT")
        boot()

        frame = Frame("@TEST.MYFRAME")
        self.assertTrue(frame ^ "@TEST.PARENT")

    def test_call_makes_instances_with_parents(self):
        boot = BootstrapDeclareKnowledge("TEST", "MYFRAME", isa=["@TEST.PARENT1", "@TEST.PARENT2"])
        boot()

        frame = Frame("@TEST.MYFRAME")
        self.assertTrue(frame ^ "@TEST.PARENT1")
        self.assertTrue(frame ^ "@TEST.PARENT2")

    def test_call_adds_property(self):
        prop = BootstrapTriple("MYSLOT", Identifier("@ONT.ALL"))

        boot = BootstrapDeclareKnowledge("TEST", "MYFRAME", properties=[prop])
        boot()

        frame = Frame("@TEST.MYFRAME")
        self.assertTrue(frame["MYSLOT"] == Frame("@ONT.ALL"))

    def test_call_adds_multiple_properties(self):
        prop1 = BootstrapTriple("MYSLOT", "ONT.ALL")
        prop2 = BootstrapTriple("MYSLOT", 123)

        boot = BootstrapDeclareKnowledge("TEST", "MYFRAME", properties=[prop1, prop2])
        boot()

        frame = Frame("@TEST.MYFRAME")
        self.assertTrue(frame["MYSLOT"] == "ONT.ALL")
        self.assertTrue(frame["MYSLOT"] == 123)

    def test_call_adds_properties_with_facets(self):
        prop = BootstrapTriple("MYSLOT", 123, facet="XYZ")

        boot = BootstrapDeclareKnowledge(Space("TEST"), "FRAME", 1, properties=[prop])
        boot()

        frame = Frame("@TEST.FRAME.1")
        self.assertTrue(frame["MYSLOT"]["VALUE"] != 123)
        self.assertTrue(frame["MYSLOT"]["XYZ"] == 123)


class BootstrapAppendKnowledgeTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()

    def test_call_adds_property(self):
        frame = Frame("@TEST.MYFRAME")

        prop = BootstrapTriple("MYSLOT", Identifier("@ONT.ALL"))

        boot = BootstrapAppendKnowledge("@TEST.MYFRAME", properties=[prop])
        boot()

        self.assertTrue(frame["MYSLOT"] == Frame("@ONT.ALL"))

    def test_call_adds_multiple_properties(self):
        frame = Frame("@TEST.MYFRAME")

        prop1 = BootstrapTriple("MYSLOT", "ONT.ALL")
        prop2 = BootstrapTriple("MYSLOT", 123)

        boot = BootstrapAppendKnowledge("@TEST.MYFRAME", properties=[prop1, prop2])
        boot()

        self.assertTrue(frame["MYSLOT"] == "ONT.ALL")
        self.assertTrue(frame["MYSLOT"] == 123)

    def test_call_adds_filler_to_existing_property(self):
        frame = Frame("@TEST.MYFRAME")
        frame["MYSLOT"] = Frame("@ONT.FIRST")

        prop = BootstrapTriple("MYSLOT", Identifier("@ONT.SECOND"))

        boot = BootstrapAppendKnowledge("@TEST.MYFRAME", properties=[prop])
        boot()

        self.assertTrue(frame["MYSLOT"] == Frame("@ONT.FIRST"))
        self.assertTrue(frame["MYSLOT"] == Frame("@ONT.SECOND"))

    def test_call_adds_properties_with_facets(self):
        prop = BootstrapTriple("MYSLOT", 123, facet="XYZ")

        boot = BootstrapAppendKnowledge("@TEST.FRAME.1", properties=[prop])
        boot()

        frame = Frame("@TEST.FRAME.1")
        self.assertTrue(frame["MYSLOT"]["VALUE"] != 123)
        self.assertTrue(frame["MYSLOT"]["XYZ"] == 123)


class BootstrapRegisterMPTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()
        MPRegistry.clear()

        class MP(AgentMethod):
            def run(self):
                return True

        self.mp = MP

    def test_call(self):
        boot = BootstrapRegisterMP(self.mp)
        boot()

        self.assertTrue(MPRegistry.has_mp(self.mp.__name__))
        self.assertTrue(MPRegistry.run(self.mp.__name__, None))

    def test_call_with_name(self):
        boot = BootstrapRegisterMP(self.mp, name="TestMP")
        boot()

        self.assertTrue(MPRegistry.has_mp("TestMP"))
        self.assertTrue(MPRegistry.run("TestMP", None))


class BootstrapAddTriggerTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()

    def test_call(self):
        agenda = Frame("@TEST.AGENDA")
        definition = Frame("@TEST.DEFINITION")
        query = Query().search(IdComparator("@TEST.SOMETHING.123"))

        boot = BootstrapAddTrigger(agenda, definition, query)
        boot()

        self.assertEqual(1, len(Agenda(agenda).triggers()))
        self.assertEqual(definition, Agenda(agenda).triggers()[0].definition())
        self.assertEqual(query, Agenda(agenda).triggers()[0].query())


class BootstrapDefineOutputXMRTemplateTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()
        self.capability = Frame("@TEST.CAPABILITY")

    def test_call(self):
        name = "Test Name"
        type = XMR.Type.ACTION
        capability = self.capability
        params = ["$var1", "$var2"]
        root = "@OUT.EVENT.1"
        frames = [
            BootstrapDeclareKnowledge("OUT", "EVENT", index=1, properties=[BootstrapTriple("THEME", Identifier("@OUT.OBJECT.1"))]),
            BootstrapDeclareKnowledge( "OUT", "OBJECT", index=1, properties=[BootstrapTriple("PROP", "$var1")])
        ]

        boot = BootstrapDefineOutputXMRTemplate(name, type, capability, params, root, frames)
        boot()

        template = Space("XMR-TEMPLATE#1")
        event = Frame("@XMR-TEMPLATE#1.EVENT.1")
        object = Frame("@XMR-TEMPLATE#1.OBJECT.1")

        self.assertEqual(object, event["THEME"])
        self.assertEqual("$var1", object["PROP"])

        self.assertEqual("Test Name", OutputXMRTemplate(template).name())
        self.assertEqual(XMR.Type.ACTION, OutputXMRTemplate(template).type())
        self.assertEqual(Frame("@TEST.CAPABILITY"), OutputXMRTemplate(template).capability().frame)
        self.assertEqual(["$var1", "$var2"], OutputXMRTemplate(template).params())