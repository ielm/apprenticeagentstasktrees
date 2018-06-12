from backend.models.graph import Filler, Fillers, Frame, Graph

import itertools
import pickle


class Ontology(Graph):

    @classmethod
    def init_default(cls, namespace="ONT"):
        path = "../../backend/resources/ontology_May_2017.p"
        return cls.init_from_file(path, namespace)

    @classmethod
    def init_from_file(cls, path, namespace):
        with open(path, mode="rb") as f:
            return Ontology(namespace, wrapped=pickle.load(f))

    def __init__(self, namespace, wrapped=None):
        super().__init__(namespace)
        if wrapped is not None:
            self._wrapped = wrapped

    def __getitem__(self, item):
        try:
            return super().__getitem__(item)
        except KeyError: pass

        if item not in self._wrapped:
            raise KeyError()

        original = self._wrapped[item]

        frame = Frame(item)
        frame._graph = self

        for slot in original:
            for facet in original[slot]:
                fillers = original[slot][facet]
                if not isinstance(fillers, list):
                    fillers = [fillers]
                fillers = list(map(lambda f: OntologyFiller(f, facet), fillers))
                frame[slot] = Fillers(fillers, frame=frame)

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

        return itertools.chain(iters)


class OntologyFiller(Filler):

    def __init__(self, value, facet):
        super().__init__(value)
        self._facet = facet