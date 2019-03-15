# TODO: X

# from backend.models.graph import Filler, Frame, Graph, Identifier, Literal, Slot

# import itertools
# import pickle
# from pkgutil import get_data
# from typing import List, Union
#
#
# class Ontology(Graph):
#
#     @classmethod
#     def init_default(cls, namespace="ONT"):
#         try:
#             return cls.init_from_service(namespace=namespace)
#         except:
#             print("WARNING: failed to init default ontology service, using binary data instead.")
#             binary = get_data("backend.resources", "ontology_May_2017.p")
#             return cls.init_from_binary(binary, namespace=namespace)
#
#     @classmethod
#     def init_from_service(cls, host: str=None, port: int=None, database: str=None, collection: str=None, namespace: str="ONT"):
#         wrapper = OntologyServiceWrapper(host=host, port=port, database=database, collection=collection)
#         return Ontology(namespace, wrapped=wrapper)
#
#     @classmethod
#     def init_from_file(cls, path, namespace):
#         with open(path, mode="rb") as f:
#             return Ontology(namespace, wrapped=pickle.load(f))
#
#     @classmethod
#     def init_from_binary(cls, binary, namespace):
#         return Ontology(namespace, wrapped=pickle.loads(binary))
#
#     def __init__(self, namespace, wrapped=None):
#         super().__init__(namespace)
#         self._wrapped = wrapped
#
#     def _frame_type(self):
#         return OntologyFrame
#
#     def register(self, id, isa=None, generate_index=False):
#         return super().register(id, isa=isa, generate_index=generate_index)
#
#     def __getitem__(self, item):
#         try:
#             return super().__getitem__(item)
#         except KeyError: pass
#
#         if isinstance(item, Identifier):
#             item = item.name
#
#         if item not in self._wrapped:
#             raise KeyError()
#
#         original = self._wrapped[item]
#
#         frame = self._frame_type()(Identifier(self._namespace, item))
#         frame._graph = self
#
#         for slot in original:
#             relation = self._is_relation(slot)
#             for facet in original[slot]:
#                 fillers = original[slot][facet]
#                 if fillers is None:
#                     continue
#
#                 if not isinstance(fillers, list):
#                     fillers = [fillers]
#                 fillers = list(map(lambda f: OntologyFiller(Identifier(self._namespace, f) if relation else Literal(f), facet), fillers))
#                 frame[slot] = Slot(slot, values=fillers, frame=frame)
#
#         self[item] = frame
#
#         return frame
#
#     def __delitem__(self, key):
#         try:
#             super().__delitem__(key)
#         except KeyError: pass
#
#         if self._wrapped is not None:
#             del self._wrapped[key]
#
#     def __len__(self):
#         length = super().__len__()
#
#         if self._wrapped is not None:
#             length += len(self._wrapped)
#
#         return length
#
#     def __iter__(self):
#         iters = [super().__iter__()]
#
#         if self._wrapped is not None:
#             iters += iter(self._wrapped)
#
#         return itertools.chain(*iters)
#
#     def _is_relation(self, slot):
#         if slot not in self._wrapped:
#             return False
#
#         if slot in ["RELATION", "INVERSE", "IS-A", "INSTANCES", "ONTO-INSTANCES", "DOMAIN", "RANGE"]:
#             return True
#
#         frame = self._wrapped[slot]
#
#         parents = None
#         if "IS-A" in frame and frame["IS-A"] is not None:
#             if "VALUE" in frame["IS-A"] and frame["IS-A"]["VALUE"] is not None:
#                 parents = frame["IS-A"]["VALUE"]
#                 if not isinstance(parents, list):
#                     parents = [parents]
#
#         if parents is None:
#             return False
#
#         for parent in parents:
#             if parent == "RELATION":
#                 return True
#             if self._is_relation(parent):
#                 return True
#         return False
#
#
# class OntologyFrame(Frame):
#
#     def __init__(self, identifier: Union[Identifier, str], isa: Union['Slot', 'Filler', List['Filler'], Identifier, List['Identifier'], str, List[str]]=None):
#         super().__init__(identifier, isa)
#
#
# class OntologyFiller(Filler):
#
#     def __init__(self, value, facet):
#         super().__init__(value)
#         self._facet = facet
#
#
# class OntologyServiceWrapper(object):
#
#     def __init__(self, host: str=None, port: int=None, database: str=None, collection: str=None):
#         from backend.utils.LEIAEnvironment import ONTOLOGY_HOST, MONGO_PORT, ONTOLOGY_DATABASE, ONTOLOGY_COLLECTION
#
#         host = host if host is not None else ONTOLOGY_HOST
#         port = port if port is not None else MONGO_PORT
#         database = database if database is not None else ONTOLOGY_DATABASE
#         collection = collection if collection is not None else ONTOLOGY_COLLECTION
#
#         self._cache = {}
#
#         handle = self._handle(host, port, database, collection)
#         for record in handle.find({}):
#             self._cache[record["name"]] = record
#
#         self._index()
#
#     def _get_client(self, host: str, port: int):
#         from pymongo import MongoClient
#
#         client = MongoClient(host, port)
#         with client:
#             return client
#
#     def _handle(self, host: str, port: int, database: str, collection: str):
#         client = self._get_client(host, port)
#         db = client[database]
#         return db[collection]
#
#     def _index(self):
#         self._domains = {}
#         self._ranges = {}
#         for r in self._cache:
#             record = self._cache[r]
#             for slot in record["localProperties"]:
#                 s = slot["slot"]
#                 if s not in self._domains:
#                     self._domains[s] = []
#                 if s not in self._ranges:
#                     self._ranges[s] = []
#                 self._domains[s].append(record["name"])
#                 self._ranges[s].append(slot["filler"])
#
#         self._subclasses = {}
#         for r in self._cache:
#             self._subclasses[r] = []
#
#         inverses = []
#         for r in self._cache:
#             record = self._cache[r]
#             for parent in record["parents"]:
#                 self._subclasses[parent].append(r)
#             if "inverse" in map(lambda property: property["slot"], record["localProperties"]):
#                 self._calculate_domain_and_range(record)
#                 inverses.append(self._make_inverse(record))
#
#         for inverse in inverses:
#             self._cache[inverse["name"]] = inverse
#             self._subclasses[inverse["name"]] = []
#
#     def _calculate_domain_and_range(self, property):
#         if property["name"] in self._domains:
#             for domain in self._domains[property["name"]]:
#                 property["localProperties"].append({
#                     "slot": "domain",
#                     "facet": "sem",
#                     "filler": domain
#                 })
#         if property["name"] in self._ranges:
#             for range in self._ranges[property["name"]]:
#                 property["localProperties"].append({
#                     "slot": "range",
#                     "facet": "sem",
#                     "filler": range
#                 })
#
#     def _make_inverse(self, relation):
#         localProperties = [
#             {
#                 "slot": "inverse",
#                 "facet": "value",
#                 "filler": relation["name"]
#             }
#         ]
#
#         for lp in relation["localProperties"]:
#             if lp["slot"] == "domain":
#                 localProperties.append({
#                     "slot": "range",
#                     "facet": "sem",
#                     "filler": lp["filler"]
#                 })
#             elif lp["slot"] == "range":
#                 localProperties.append({
#                     "slot": "domain",
#                     "facet": "sem",
#                     "filler": lp["filler"]
#                 })
#
#         inverse = list(filter(lambda property: property["slot"] == "inverse", relation["localProperties"]))[0]["filler"]
#
#         return {
#             "localProperties": localProperties,
#             "parents": relation["parents"],
#             "name": inverse,
#             "overriddenFillers": [],
#             "totallyRemovedProperties": []
#         }
#
#     def __delitem__(self, key):
#         del self._cache[key.lower()]
#
#     def __len__(self):
#         return len(self._cache)
#
#     def __contains__(self, item):
#         return item.lower() in self._cache
#
#     def __iter__(self):
#         return iter(self._cache)
#
#     def __getitem__(self, item):
#         item = item.lower()
#
#         original = self._cache[item]
#
#         isa = list(map(lambda parent: parent.upper(), original["parents"]))
#         if len(isa) == 0:
#             isa = None
#         elif len(isa) == 1:
#             isa = isa[0]
#
#         subclasses = list(map(lambda sc: sc.upper(), self._subclasses[item]))
#         if len(subclasses) == 1:
#             subclasses = subclasses[0]
#
#         output = {
#             "IS-A": {"VALUE": isa},
#             "SUBCLASSES": {"VALUE": subclasses}
#         }
#
#         for property in self._inherit(original):
#             self._add_property(output, property)
#
#         for property in output:
#             for slot in output[property]:
#                 value = output[property][slot]
#                 if isinstance(value, list):
#                     if len(value) == 0:
#                         output[property][slot] = None
#                     elif len(value) == 1:
#                         output[property][slot] = value[0]
#
#         return output
#
#     def _add_property(self, output, property):
#         slot = property["slot"].upper()
#         facet = property["facet"].upper()
#         filler = property["filler"] if property["filler"] not in self._cache else property["filler"].upper()
#
#         if slot not in output:
#             output[slot] = {}
#         if facet not in output[slot]:
#             output[slot][facet] = [filler]
#         elif type(output[slot][facet]) != list:
#             output[slot][facet] = [output[slot][facet], filler]
#         else:
#             output[slot][facet].append(filler)
#
#     def _inherit(self, concept):
#         properties = concept["localProperties"]
#
#         for parent_name in concept["parents"]:
#             parent = self._cache[parent_name]
#
#             inherited = self._inherit(parent)
#             inherited = self._remove_overridden_fillers(inherited, concept["overriddenFillers"])
#             inherited = self._remove_deleted_fillers(inherited, concept["totallyRemovedProperties"])
#             inherited = self._prune_list(inherited, properties) # Clean up any duplicates, retaining local copies
#
#             properties = properties + inherited
#
#         return properties
#
#     def _remove_overridden_fillers(self, properties, overridden_fillers):
#         properties = self._prune_list(properties, overridden_fillers)
#         return properties
#
#     def _remove_deleted_fillers(self, properties, deleted_fillers):
#         return self._prune_list(properties, deleted_fillers)
#
#     def _prune_list(self, enclosing_list, to_remove):
#         pruned = [e for e in enclosing_list if e not in to_remove]
#         return pruned

