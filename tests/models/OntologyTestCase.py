from backend.models.ontology import Ontology

import unittest


class OntologyTestCase(unittest.TestCase):

    def test_init_default_wrapped(self):
        o = Ontology.init_default()

        self.assertEqual("ONT", o._namespace)
        self.assertTrue("OBJECT" in o)

        self.assertTrue(o["OBJECT"]["IS-A"] == "ALL")
        self.assertTrue(o["HUMAN"]["IS-A"] ^ "ALL")
        self.assertTrue(o["HUMAN"].isa("PHYSICAL-OBJECT"))
        self.assertTrue(o["HUMAN"] ^ "OBJECT")
        self.assertTrue(o["HUMAN"] ^ "ONT.OBJECT")

        self.assertTrue(9494, len(o))
        self.assertTrue(9494, sum(1 for _ in iter(o)))

        with self.assertRaises(KeyError):
            f = o["XYZ"]
        o.register("XYZ", isa="HUMAN")
        self.assertTrue(o["XYZ"]["IS-A"] ^ "HUMAN")

        del o["HUMAN"]
        self.assertNotIn("HUMAN", o)

    def test_wrapped_caches_for_editing(self):
        o = Ontology.init_default()

        self.assertTrue("OBJECT" in o)

        self.assertEqual(0, len(o["OBJECT"]["XYZ"]))
        self.assertEqual(0, len(o["OBJECT"]["XYZ"]))

        o["OBJECT"]["XYZ"] += "a"

        self.assertEqual(1, len(o["OBJECT"]["XYZ"]))

    def test_unwrapped_ontology_iterates(self):
        o = Ontology("ONT")
        all = o.register("ALL")

        for f in o:
            self.assertEqual(f, all.name())