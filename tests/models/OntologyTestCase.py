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