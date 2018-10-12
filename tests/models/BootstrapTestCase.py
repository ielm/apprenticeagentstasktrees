from backend.models.bootstrap import BootstrapAppendKnowledge, BootstrapDeclareKnowledge, BootstrapTriple
from backend.models.graph import Identifier, Literal, Network

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

    def test_call(self):
        n = Network()
        g = n.register("TEST")
        f = g.register("SOMEFRAME")

        boot = BootstrapAppendKnowledge(n, "TEST.SOMEFRAME", "slot", Literal(123))
        boot()

        self.assertTrue(123 in f["slot"])