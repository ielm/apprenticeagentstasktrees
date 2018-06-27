from backend.models.graph import Filler, Frame, Graph, Identifier, Slot

import itertools
import pickle
from pkgutil import get_data


class Ontology(Graph):

    @classmethod
    def init_default(cls, namespace="ONT"):
        binary = get_data("backend.resources", "ontology_May_2017.p")
        return cls.init_from_binary(binary, namespace=namespace)

    @classmethod
    def init_from_file(cls, path, namespace):
        with open(path, mode="rb") as f:
            return Ontology(namespace, wrapped=pickle.load(f))

    @classmethod
    def init_from_binary(cls, binary, namespace):
        return Ontology(namespace, wrapped=pickle.loads(binary))

    def __init__(self, namespace, wrapped=None):
        super().__init__(namespace)
        self._wrapped = wrapped

    def __getitem__(self, item):
        try:
            return super().__getitem__(item)
        except KeyError: pass

        if isinstance(item, Identifier):
            item = item.name

        if item not in self._wrapped:
            raise KeyError()

        original = self._wrapped[item]

        frame = Frame(Identifier(self._namespace, item))
        frame._graph = self

        for slot in original:
            for facet in original[slot]:
                fillers = original[slot][facet]
                if fillers is None:
                    continue

                if not isinstance(fillers, list):
                    fillers = [fillers]
                fillers = list(map(lambda f: OntologyFiller(Identifier(self._namespace, f), facet), fillers))
                frame[slot] = Slot(slot, values=fillers, frame=frame)

        self[item] = frame

        return frame

    def __delitem__(self, key):
        try:
            super().__delitem__(key)
        except KeyError: pass

        if self._wrapped is not None:
            del self._wrapped[key]

    def __len__(self):
        length = super().__len__()

        if self._wrapped is not None:
            length += len(self._wrapped)

        return length

    def __iter__(self):
        iters = [super().__iter__()]

        if self._wrapped is not None:
            iters += iter(self._wrapped)

        return itertools.chain(*iters)

    def _is_relation(self, slot):
        if slot not in self._wrapped:
            return False

        frame = self._wrapped[slot]

        parents = None
        if "IS-A" in frame and frame["IS-A"] is not None:
            if "VALUE" in frame["IS-A"] and frame["IS-A"]["VALUE"] is not None:
                parents = frame["IS-A"]["VALUE"]
                if not isinstance(parents, list):
                    parents = [parents]

        if parents is None:
            return False

        for parent in parents:
            if parent == "RELATION":
                return True
            if self._is_relation(parent):
                return True
        return False


class OntologyFiller(Filler):

    def __init__(self, value, facet):
        super().__init__(value)
        self._facet = facet