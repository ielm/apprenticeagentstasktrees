import json
import unittest

from backend import mini_ontology


class ApprenticeAgentsTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        mini_ontology.init_default()

    def resource(self, fp):
        r = None
        with open(fp) as f:
            r = json.load(f)
        return r

    def assertNode(self, node, name=None, children=None, terminal=None, type=None, disputed=None, relationships=None):
        if name:
            self.assertEqual(node.name, name)
        if children:
            self.assertEqual(len(node.children), children)
        if terminal is not None:
            self.assertEqual(node.terminal, terminal)
        if type:
            self.assertEqual(node.type, type)
        if disputed:
            self.assertEqual(node.disputedWith, disputed)
        if relationships:
            self.assertEqual(node.relationships, relationships)