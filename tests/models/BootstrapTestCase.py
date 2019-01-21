from backend.models.agenda import Agenda
from backend.models.bootstrap import BootstrapAddTrigger, BootstrapAppendKnowledge, BootstrapDeclareKnowledge, BootstrapDefineOutputXMRTemplate, BootstrapRegisterMP, BootstrapTriple
from backend.models.graph import Frame, Identifier, Literal, Network
from backend.models.mps import AgentMethod, MPRegistry
from backend.models.output import OutputXMRTemplate
from backend.models.xmr import XMR

import unittest


class BootstrapDeclareKnowledgeTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("TEST")

    def test_call_makes_instance(self):
        boot = BootstrapDeclareKnowledge(self.n, "TEST", "MYFRAME")
        boot()

        self.assertIn("TEST.MYFRAME", self.g)

    def test_call_makes_instance_with_specified_index(self):
        boot = BootstrapDeclareKnowledge(self.n, "TEST", "MYFRAME", index=1)
        boot()

        self.assertIn("TEST.MYFRAME.1", self.g)

    def test_call_makes_instance_with_generated_index(self):
        boot = BootstrapDeclareKnowledge(self.n, "TEST", "MYFRAME", index=True)
        boot()

        self.assertIn("TEST.MYFRAME.1", self.g)

    def test_call_makes_instances_with_parent(self):
        self.g.register("PARENT")

        boot = BootstrapDeclareKnowledge(self.n, "TEST", "MYFRAME", isa="TEST.PARENT")
        boot()

        frame = self.g["MYFRAME"]
        self.assertTrue(frame ^ "TEST.PARENT")

    def test_call_makes_instances_with_parents(self):
        self.g.register("PARENT1")
        self.g.register("PARENT2")

        boot = BootstrapDeclareKnowledge(self.n, "TEST", "MYFRAME", isa=["TEST.PARENT1", "TEST.PARENT2"])
        boot()

        frame = self.g["MYFRAME"]
        self.assertTrue(frame ^ "TEST.PARENT1")
        self.assertTrue(frame ^ "TEST.PARENT2")

    def test_call_adds_property(self):
        prop = BootstrapTriple("MYSLOT", Identifier.parse("ONT.ALL"))

        boot = BootstrapDeclareKnowledge(self.n, "TEST", "MYFRAME", properties=[prop])
        boot()

        frame = self.g["MYFRAME"]
        self.assertTrue(frame["MYSLOT"] == Identifier.parse("ONT.ALL"))

    def test_call_adds_multiple_properties(self):
        prop1 = BootstrapTriple("MYSLOT", Literal("ONT.ALL"))
        prop2 = BootstrapTriple("MYSLOT", Literal(123))

        boot = BootstrapDeclareKnowledge(self.n, "TEST", "MYFRAME", properties=[prop1, prop2])
        boot()

        frame = self.g["MYFRAME"]
        self.assertTrue(frame["MYSLOT"] == "ONT.ALL")
        self.assertTrue(frame["MYSLOT"] == 123)

    def test_call_respects_facets_in_ontology(self):
        from backend.models.ontology import Ontology
        ontology = self.n.register(Ontology("ONT"))

        prop = BootstrapTriple("MYSLOT", Identifier.parse("ONT.ALL"), facet="SEM")

        boot = BootstrapDeclareKnowledge(self.n, "ONT", "MYFRAME", properties=[prop])
        boot()

        frame = ontology["MYFRAME"]
        self.assertTrue(frame["MYSLOT"] == Identifier.parse("ONT.ALL"))
        self.assertEqual("SEM", frame["MYSLOT"][0]._facet)

    def test_call_ignores_facets_in_non_ontology_graphs(self):
        prop = BootstrapTriple("MYSLOT", Identifier.parse("ONT.ALL"), facet="does-not-matter")

        boot = BootstrapDeclareKnowledge(self.n, "TEST", "MYFRAME", properties=[prop])
        boot()

        frame = self.g["MYFRAME"]
        self.assertTrue(frame["MYSLOT"] == Identifier.parse("ONT.ALL"))


class BootstrapAppendKnowledgeTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("TEST")

    def test_call_adds_property(self):
        frame = self.g.register("MYFRAME")

        prop = BootstrapTriple("MYSLOT", Identifier.parse("ONT.ALL"))

        boot = BootstrapAppendKnowledge(self.n, "TEST.MYFRAME", properties=[prop])
        boot()

        self.assertTrue(frame["MYSLOT"] == Identifier.parse("ONT.ALL"))

    def test_call_adds_multiple_properties(self):
        frame = self.g.register("MYFRAME")

        prop1 = BootstrapTriple("MYSLOT", Literal("ONT.ALL"))
        prop2 = BootstrapTriple("MYSLOT", Literal(123))

        boot = BootstrapAppendKnowledge(self.n, "TEST.MYFRAME", properties=[prop1, prop2])
        boot()

        self.assertTrue(frame["MYSLOT"] == "ONT.ALL")
        self.assertTrue(frame["MYSLOT"] == 123)

    def test_call_adds_filler_to_existing_property(self):
        frame = self.g.register("MYFRAME")
        frame["MYSLOT"] = Identifier.parse("ONT.FIRST")

        prop = BootstrapTriple("MYSLOT", Identifier.parse("ONT.SECOND"))

        boot = BootstrapAppendKnowledge(self.n, "TEST.MYFRAME", properties=[prop])
        boot()

        self.assertTrue(frame["MYSLOT"] == Identifier.parse("ONT.FIRST"))
        self.assertTrue(frame["MYSLOT"] == Identifier.parse("ONT.SECOND"))

    def test_call_respects_facets_in_ontology(self):
        from backend.models.ontology import Ontology
        ontology = self.n.register(Ontology("ONT"))

        frame = ontology.register("MYFRAME")

        prop = BootstrapTriple("MYSLOT", Identifier.parse("ONT.ALL"), facet="SEM")

        boot = BootstrapAppendKnowledge(self.n, "ONT.MYFRAME", properties=[prop])
        boot()

        self.assertTrue(frame["MYSLOT"] == Identifier.parse("ONT.ALL"))
        self.assertEqual("SEM", frame["MYSLOT"][0]._facet)

    def test_call_ignores_facets_in_non_ontology_graphs(self):
        frame = self.g.register("MYFRAME")

        prop = BootstrapTriple("MYSLOT", Identifier.parse("ONT.ALL"), facet="does-not-matter")

        boot = BootstrapAppendKnowledge(self.n, "TEST.MYFRAME", properties=[prop])
        boot()

        self.assertTrue(frame["MYSLOT"] == Identifier.parse("ONT.ALL"))


class BootstrapRegisterMPTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("TEST")
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
        self.n = Network()
        self.g = self.n.register("TEST")

    def test_call(self):
        agenda = self.g.register("AGENDA")
        definition = self.g.register("DEFINITION")
        query = Frame.q(self.n).id("TEST.SOMETHING.123")

        boot = BootstrapAddTrigger(self.n, agenda, definition, query)
        boot()

        self.assertEqual(1, len(Agenda(agenda).triggers()))
        self.assertEqual(definition, Agenda(agenda).triggers()[0].definition())
        self.assertEqual(query, Agenda(agenda).triggers()[0].query())


class BootstrapDefineOutputXMRTemplateTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("TEST")
        self.capability = self.g.register("CAPABILITY")

    def test_call(self):
        name = "Test Name"
        type = XMR.Type.ACTION
        capability = self.capability
        params = ["$var1", "$var2"]
        root = "OUT.EVENT.1"
        frames = [
            BootstrapDeclareKnowledge(self.n, "OUT", "EVENT", index=1, properties=[BootstrapTriple("THEME", Identifier.parse("OUT.OBJECT.1"))]),
            BootstrapDeclareKnowledge(self.n, "OUT", "OBJECT", index=1, properties=[BootstrapTriple("PROP", Literal("$var1"))])
        ]

        boot = BootstrapDefineOutputXMRTemplate(self.n, name, type, capability, params, root, frames)
        boot()

        template = self.n["XMR-TEMPLATE#1"]
        event = template["XMR-TEMPLATE#1.EVENT.1"]
        object = template["XMR-TEMPLATE#1.OBJECT.1"]

        self.assertEqual(object, event["THEME"])
        self.assertEqual("$var1", object["PROP"])

        self.assertEqual("Test Name", OutputXMRTemplate(template).name())
        self.assertEqual(XMR.Type.ACTION, OutputXMRTemplate(template).type())
        self.assertEqual("TEST.CAPABILITY", OutputXMRTemplate(template).capability().name())
        self.assertEqual(["$var1", "$var2"], OutputXMRTemplate(template).params())