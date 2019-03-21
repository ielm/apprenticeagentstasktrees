from backend.utils.OntologyLoader import OntologyBinaryLoader, OntologyServiceLoader
from ontograph import graph
from ontograph.Frame import Frame
import unittest


class OntologyServiceLoaderTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()

    def test_load(self):
        self.assertNotIn("@ONT.HUMAN", graph)

        OntologyServiceLoader().load()
        self.assertIn("@ONT.HUMAN", graph)
        self.assertTrue(Frame("@ONT.HUMAN") ^ Frame("@ONT.OBJECT"))


class OntologyBinaryLoaderTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()

    @unittest.skip("Slow, and not the desired way to load the ontology.")
    def test_load(self):
        self.assertNotIn("@ONT.HUMAN", graph)

        OntologyBinaryLoader().load("backend.resources", "ontology_May_2017.p")
        self.assertIn("@ONT.HUMAN", graph)
        self.assertTrue(Frame("@ONT.HUMAN") ^ Frame("@ONT.OBJECT"))