from backend.utils.LEIAEnvironment import MONGO_HOST, MONGO_PORT, ONTOLOGY_COLLECTION, ONTOLOGY_DATABASE
from ontograph import graph
from ontograph.Index import Identifier
from pkgutil import get_data
from pymongo import MongoClient
import pickle


class OntologyServiceLoader(object):

    def load(self):
        self.__import_graph()

    def __get_client(self, host: str, port: int) -> MongoClient:
        client = MongoClient(host, port)
        with client:
            return client

    def __get_handle(self):
        client = self.__get_client(MONGO_HOST, MONGO_PORT)
        db = client[ONTOLOGY_DATABASE]
        return db[ONTOLOGY_COLLECTION]

    def __list_concepts(self, handle):
        concepts = list(handle.find({}))
        return concepts

    def __import_graph(self):

        index = graph.index
        handle = self.__get_handle()
        concepts = self.__list_concepts(handle)
        all = set(map(lambda c: c["name"], concepts))

        for c in concepts:
            name = "@ONT." + c["name"].upper()
            for parent in c["parents"]:
                parent = Identifier("@ONT." + parent.upper())
                index.add_row(name, "IS-A", "SEM", parent)
            for prop in c["localProperties"]:
                filler = prop["filler"]
                if filler in all:
                    filler = Identifier("@ONT." + filler.upper())
                index.add_row(name, prop["slot"].upper(), prop["facet"].upper(), filler)


class OntologyBinaryLoader(object):

    def load(self, package: str, resource: str):

        index = graph.index
        binary = get_data(package, resource)
        concepts = pickle.loads(binary)

        count = 0

        all = set(concepts.keys())
        for c in all:
            name = "@ONT." + c.upper()
            concept = concepts[c]
            for prop in concept.keys():
                slot = concept[prop]
                for facet in slot:
                    fillers = slot[facet]
                    if not isinstance(fillers, list):
                        fillers = [fillers]
                    for filler in fillers:
                        if filler in all:
                            filler = Identifier("@ONT." + filler.upper())
                        if filler is None:
                            continue
                        count += 1
                        index.add_row(name, prop.upper(), facet.upper(), filler)