from collections.abc import Mapping
import re


class Instance(Mapping):

    def __init__(self, inst_dict, name=None):
        self._storage = dict()

        self.subtree = inst_dict["is-in-subtree"] if "is-in-subtree" in inst_dict else None
        self.concept = inst_dict["concept"]
        self.name = name if name is not None else self.concept + "-X"
        self.token = inst_dict["token"] if "token" in inst_dict else None
        self.properties = {}

        for key in inst_dict:
            if "_constraint_info" in key:
                pass

            if key == key.upper():
                self[key] = inst_dict[key]

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
