# from backend.models.graph import Literal
# from backend.models.ontology import Ontology
# from backend.models.ontology import OntologyServiceWrapper
#
# import unittest
# from unittest import skip
#
#
# class OntologyTestCase(unittest.TestCase):
#
#     def test_init_default_wrapped(self):
#         from pkgutil import get_data
#         o = Ontology.init_from_binary(get_data("backend.resources", "ontology_May_2017.p"), "ONT")
#
#         self.assertEqual("ONT", o._namespace)
#         self.assertTrue("OBJECT" in o)
#
#         self.assertTrue(o["OBJECT"]["IS-A"] == "ALL")
#         self.assertTrue(o["HUMAN"]["IS-A"] ^ "ALL")
#         self.assertTrue(o["HUMAN"].isa("PHYSICAL-OBJECT"))
#         self.assertTrue(o["HUMAN"] ^ "OBJECT")
#         self.assertTrue(o["HUMAN"] ^ "ONT.OBJECT")
#
#         self.assertTrue(isinstance(o["FASTEN"]["ABSOLUTE-DAY"][0]._value, Literal))
#
#         self.assertTrue(9494, len(o))
#         self.assertTrue(9494, sum(1 for _ in iter(o)))
#
#         with self.assertRaises(KeyError):
#             f = o["XYZ"]
#         o.register("XYZ", isa="HUMAN")
#         self.assertTrue(o["XYZ"]["IS-A"] ^ "HUMAN")
#
#         del o["HUMAN"]
#         self.assertNotIn("HUMAN", o)
#
#     def test_wrapped_caches_for_editing(self):
#         o = Ontology.init_default()
#
#         self.assertTrue("OBJECT" in o)
#
#         self.assertEqual(0, len(o["OBJECT"]["XYZ"]))
#         self.assertEqual(0, len(o["OBJECT"]["XYZ"]))
#
#         o["OBJECT"]["XYZ"] += "a"
#
#         self.assertEqual(1, len(o["OBJECT"]["XYZ"]))
#
#     def test_unwrapped_ontology_iterates(self):
#         o = Ontology("ONT")
#         all = o.register("ALL")
#
#         for f in o:
#             self.assertEqual(f, all.name())
#
#
# class OntologyServiceWrapperTestCase(unittest.TestCase):
#
#     class TestableOntologyServiceWrapper(OntologyServiceWrapper):
#         def __init__(self):
#             self._cache = {}
#
#     def test_service_wrapper(self):
#         w = OntologyServiceWrapper(host="localhost", port=27017, database="leia-ontology", collection="robot-v.1.0.0")
#         self.assertEqual(9175, len(w._cache))
#
#         o = Ontology("ONT", wrapped=w)
#         all = o["ALL"]
#         self.assertTrue(all["SUBCLASSES"] == "ONT.EVENT")
#
#         self.assertEqual("ONT", o._namespace)
#         self.assertTrue("OBJECT" in o)
#
#         self.assertTrue(o["OBJECT"]["IS-A"] == "ALL")
#         self.assertTrue(o["HUMAN"]["IS-A"] ^ "ALL")
#         self.assertTrue(o["HUMAN"].isa("PHYSICAL-OBJECT"))
#         self.assertTrue(o["HUMAN"] ^ "OBJECT")
#         self.assertTrue(o["HUMAN"] ^ "ONT.OBJECT")
#
#         self.assertTrue(isinstance(o["FASTEN"]["ABSOLUTE-DAY"][0]._value, Literal))
#
#         self.assertTrue(9494, len(o))
#         self.assertTrue(9494, sum(1 for _ in iter(o)))
#
#         with self.assertRaises(KeyError):
#             f = o["XYZ"]
#         o.register("XYZ", isa="HUMAN")
#         self.assertTrue(o["XYZ"]["IS-A"] ^ "HUMAN")
#
#         del o["HUMAN"]
#         self.assertNotIn("HUMAN", o)
#
#     def test_service_wrapper_get_converts(self):
#         w = OntologyServiceWrapperTestCase.TestableOntologyServiceWrapper()
#
#         w._cache["parent"] = {
#             "localProperties": [
#                 {
#                     "slot": "x",
#                     "facet": "sem",
#                     "filler": 1
#                 }, {
#                     "slot": "y",
#                     "facet": "sem",
#                     "filler": 2
#                 }
#             ],
#             "parents": [],
#             "name": "parent",
#             "overriddenFillers": [],
#             "totallyRemovedProperties": []
#         }
#
#         w._cache["child"] = {
#             "localProperties": [
#                 {
#                     "slot": "x",
#                     "facet": "sem",
#                     "filler": 3
#                 },
#                 {
#                     "slot": "x",
#                     "facet": "relaxable-to",
#                     "filler": 3.5
#                 },
#                 {
#                     "slot": "y",
#                     "facet": "sem",
#                     "filler": 4
#                 },
#                 {
#                     "slot": "z",
#                     "facet": "sem",
#                     "filler": 5
#                 },
#                 {
#                     "slot": "a",
#                     "facet": "sem",
#                     "filler": "abc"
#                 },
#                 {
#                     "slot": "b",
#                     "facet": "sem",
#                     "filler": "parent"
#                 },
#             ],
#             "parents": ["parent"],
#             "name": "child",
#             "overriddenFillers": [
#                 {
#                     "slot": "y",
#                     "facet": "sem",
#                     "filler": 2
#                 }
#             ],
#             "totallyRemovedProperties": []
#         }
#
#         w._index()
#
#         parent = w["parent"]
#         expected = {
#             "IS-A": {"VALUE": None},
#             "SUBCLASSES": {"VALUE": "CHILD"},
#             "X": {"SEM": 1},
#             "Y": {"SEM": 2}
#         }
#
#         self.assertEqual(expected, parent)
#
#         child = w["child"]
#         # 2 possible values; where the "X" has a list but the order doesn't matter (functionally, this is a set)
#         expected1 = {
#             "IS-A": {"VALUE": "PARENT"},
#             "SUBCLASSES": {"VALUE": None},
#             "X": {"SEM": [1, 3], "RELAXABLE-TO": 3.5},
#             "Y": {"SEM": 4},
#             "Z": {"SEM": 5},
#             "A": {"SEM": "abc"},
#             "B": {"SEM": "PARENT"}
#         }
#         expected2 = {
#             "IS-A": {"VALUE": "PARENT"},
#             "SUBCLASSES": {"VALUE": None},
#             "X": {"SEM": [3, 1], "RELAXABLE-TO": 3.5},
#             "Y": {"SEM": 4},
#             "Z": {"SEM": 5},
#             "A": {"SEM": "abc"},
#             "B": {"SEM": "PARENT"}
#         }
#
#         self.assertTrue(expected1 == child or expected2 == child)
#
#     def test_service_wrapper_relations_and_inverses(self):
#         w = OntologyServiceWrapperTestCase.TestableOntologyServiceWrapper()
#
#         w._cache["rel-parent"] = {
#             "localProperties": [],
#             "parents": [],
#             "name": "rel-parent",
#             "overriddenFillers": [],
#             "totallyRemovedProperties": []
#         }
#
#         w._cache["rel"] = {
#             "localProperties": [
#                 {
#                     "slot": "inverse",
#                     "facet": "value",
#                     "filler": "rel-of"
#                 }
#             ],
#             "parents": ["rel-parent"],
#             "name": "rel",
#             "overriddenFillers": [],
#             "totallyRemovedProperties": []
#         }
#
#         w._index()
#
#         relation = w["rel"]
#         expected = {
#             "IS-A": {"VALUE": "REL-PARENT"},
#             "SUBCLASSES": {"VALUE": None},
#             "INVERSE": {"VALUE": "REL-OF"}
#         }
#
#         self.assertEqual(expected, relation)
#
#         inverse = w["rel-of"]
#         expected = {
#             "IS-A": {"VALUE": "REL-PARENT"},
#             "SUBCLASSES": {"VALUE": None},
#             "INVERSE": {"VALUE": "REL"}
#         }
#
#         self.assertEqual(expected, inverse)
#
#     def test_calculate_domain_and_range(self):
#         w = OntologyServiceWrapperTestCase.TestableOntologyServiceWrapper()
#         w._cache["obj"] = {
#             "localProperties": [
#                 {
#                     "slot": "rel",
#                     "facet": "sem",
#                     "filler": "evt"
#                 }
#             ],
#             "parents": [],
#             "name": "obj",
#             "overriddenFillers": [],
#             "totallyRemovedProperties": []
#         }
#
#         w._cache["evt"] = {
#             "localProperties": [],
#             "parents": [],
#             "name": "evt",
#             "overriddenFillers": [],
#             "totallyRemovedProperties": []
#         }
#
#         w._cache["rel"] = {
#             "localProperties": [
#                 {
#                     "slot": "inverse",
#                     "facet": "sem",
#                     "filler": "rel-of"
#                 }
#             ],
#             "parents": [],
#             "name": "rel",
#             "overriddenFillers": [],
#             "totallyRemovedProperties": []
#         }
#
#         w._index()
#
#         relation = w["rel"]
#         expected = {
#             "IS-A": {"VALUE": None},
#             "SUBCLASSES": {"VALUE": None},
#             "INVERSE": {"SEM": "REL-OF"},
#             "DOMAIN": {"SEM": "OBJ"},
#             "RANGE": {"SEM": "EVT"}
#         }
#         self.assertEqual(expected, relation)
#
#         relation = w["rel-of"]
#         self.assertEqual(relation["DOMAIN"], {"SEM": "EVT"})
#         self.assertEqual(relation["RANGE"], {"SEM": "OBJ"})