from collections.abc import Mapping
from uuid import uuid4
import re


class Instance(Mapping):

    def __init__(self, name, concept, uuid=None, properties=None, subtree=None):
        self._storage = dict()

        self.name = name
        self.concept = self._modify_concept(concept)
        self.uuid = uuid if uuid is not None else uuid4()
        self.subtree = subtree

        if self.subtree is None:
            from backend.ontology import Ontology
            ancestors = Ontology.ancestors(concept, include_self=True)
            for candidate in ["EVENT", "OBJECT", "PROPERTY"]:
                if candidate in ancestors:
                    self.subtree = candidate
                    break

        if properties is not None:
            for key in properties:
                self[key] = self._modify_value(properties[key])

    def _modify_concept(self, concept):
        modified_concept = concept if concept != "ASSEMBLE" else "BUILD"
        return modified_concept

    def _modify_value(self, value):
        modified_value = value if not str(value).startswith("ASSEMBLE") else value.replace("ASSEMBLE", "BUILD") + "X"
        return modified_value

    def __setitem__(self, key, value):
        key = re.split('-[0-9]+', key)[0]
        value = [value] if not type(value) == list else value

        if key in self._storage:
            self._storage[key].extend(value)
        else:
            self._storage[key] = value

    def __getitem__(self, key):
        if key in self._storage:
            return self._storage[key]
        return []

    def __delitem__(self, key):
        del self._storage[key]

    def __iter__(self):
        return iter(self._storage)

    def __len__(self):
        return len(self._storage)

    def __contains__(self, key):
        return key in self._storage

    def is_event(self):
        return self.subtree == "EVENT"

    def is_object(self):
        return self.subtree == "OBJECT"
