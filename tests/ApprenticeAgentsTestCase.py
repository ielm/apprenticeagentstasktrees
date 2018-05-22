import json
import unittest

from backend.ontology import Ontology


class ApprenticeAgentsTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Ontology.init_default()

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

    class TestOntology:

        def __init__(self, include_t1=False):
            self._storage = dict()
            self["ALL"] = {
                "IS-A": {
                    "VALUE": None
                },
                "SUBCLASSES": {
                    "VALUE": []
                }
            }

            if include_t1:
                self.subclass("ALL", "OBJECT")
                self.subclass("ALL", "EVENT")
                self.subclass("ALL", "PROPERTY")

        def __setitem__(self, key, value):
            self._storage[key] = value

        def __getitem__(self, key):
            return self._storage[key]

        def __delitem__(self, key):
            del self._storage[key]

        def __iter__(self):
            return iter(self._storage)

        def __len__(self):
            return len(self._storage)

        def subclass(self, parent, child):
            if "SUBCLASSES" not in self[parent]:
                self[parent]["SUBCLASSES"] = {}
            if "VALUE" not in self[parent]["SUBCLASSES"]:
                self[parent]["SUBCLASSES"]["VALUE"] = []
            self[parent]["SUBCLASSES"]["VALUE"].append(child)

            self[child] = {
                "IS-A": {
                    "VALUE": [parent]
                }
            }