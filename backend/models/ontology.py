from backend.models.graph import Filler, Frame, Graph, Identifier, Literal, Slot

import itertools
import pickle
from pkgutil import get_data
from typing import List, Union


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

    def _frame_type(self):
        return OntologyFrame

    def register(self, id, isa=None, generate_index=False):
        return super().register(id, isa=isa, generate_index=generate_index)

    def __getitem__(self, item):
        try:
            return super().__getitem__(item)
        except KeyError: pass

        if isinstance(item, Identifier):
            item = item.name

        if item not in self._wrapped:
            raise KeyError()

        original = self._wrapped[item]

        frame = self._frame_type()(Identifier(self._namespace, item))
        frame._graph = self

        for slot in original:
            relation = self._is_relation(slot)
            for facet in original[slot]:
                fillers = original[slot][facet]
                if fillers is None:
                    continue

                if not isinstance(fillers, list):
                    fillers = [fillers]
                fillers = list(map(lambda f: OntologyFiller(Identifier(self._namespace, f) if relation else Literal(f), facet), fillers))
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

        if slot in ["RELATION", "INVERSE", "IS-A", "INSTANCES", "ONTO-INSTANCES", "DOMAIN", "RANGE"]:
            return True

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


class OntologyFrame(Frame):

    def __init__(self, identifier: Union[Identifier, str], isa: Union['Slot', 'Filler', List['Filler'], Identifier, List['Identifier'], str, List[str]]=None):
        super().__init__(identifier, isa)


class OntologyFiller(Filler):

    def __init__(self, value, facet):
        super().__init__(value)
        self._facet = facet


class ServiceOntology(Ontology):

    @classmethod
    def init_service(cls, host=None, port=None, namespace="ONT"):
        from backend.services.environment import ONTOLOGY_HOST
        from backend.services.environment import ONTOLOGY_PORT
        if host is None:
            host = ONTOLOGY_HOST
        if port is None:
            port = ONTOLOGY_PORT

        from backend.services.ontology import Ontology as ONT
        wrap = ONT(host=host, port=port)

        return ServiceOntology(namespace, wrapped=wrap)

    def __init__(self, namespace, wrapped=None):
        super().__init__(namespace, wrapped=wrapped)

        self._cache = dict()
        self._relscache = self._wrapped.all_relations(inverses=True)

    def __getitem__(self, item):
        if isinstance(item, str):
            item = Identifier.parse(item)
        if isinstance(item, Identifier):
            item.graph = self._namespace

        try:
            return self._cache[item.render().upper()]
        except: pass

        try:
            return self._storage[item.render().upper()]
        except: pass

        item = item.name.lower()

        try:
            original: ServiceOntologyFrame = self._wrapped[item]
        except:
            raise KeyError()

        frame = self._frame_type()(Identifier(self._namespace, item))
        frame._graph = self

        for slot in original:
            relation = self._is_relation(slot)
            for facet in original[slot]:
                fillers = original[slot][facet]
                if fillers is None:
                    continue

                if not isinstance(fillers, list):
                    fillers = [fillers]
                fillers = list(map(lambda f: OntologyFiller(Identifier(self._namespace, f) if relation else Literal(f), facet), fillers))
                frame[slot] = Slot(slot, values=fillers, frame=frame)
        result = self._fix_case(frame)

        self._cache[result._identifier.render()] = result
        return result

    def __len__(self):
        length = len(self._storage)

        if self._wrapped is not None:
            length += len(self._wrapped.descendants("all"))

        return length

    def __iter__(self):
        iters = [iter(self._storage)]

        if self._wrapped is not None:
            iters += iter(self._wrapped.descendants("all"))

        return itertools.chain(*iters)

    def __delitem__(self, key):
        try:
            super().__delitem__(key)
        except TypeError:
            pass

    def _frame_type(self):
        return ServiceOntologyFrame

    def _is_relation(self, slot):
        return slot.lower() in self._relscache or slot.upper() == "IS-A"

    def _fix_case(self, result):
        result._identifier.name = result._identifier.name.upper()
        slots = dict()

        for slot in result:
            slot = result[slot]
            slot._name = slot._name.upper()

            for filler in slot:
                if isinstance(filler._value, Identifier):
                    filler._value.name = filler._value.name.upper()

            slots[slot._name] = slot
        result._storage = slots

        return result


class ServiceOntologyFrame(OntologyFrame):

    def _ISA_type(self):
        return "IS-A"

    def isa(self, parent: Union['Frame', Identifier, str]):
        if isinstance(parent, Frame):
            parent = parent._identifier
        if isinstance(parent, str):
            parent = Identifier.parse(parent)
        if isinstance(parent, Identifier):
            parent = parent.name

        result = self._graph._wrapped.is_parent(self._identifier.name.lower(), parent.lower())
        return result