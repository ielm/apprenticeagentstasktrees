from backend.models.graph import Frame
from typing import Any, Callable, List

import sys


class Registry(object):

    def __init__(self):
        self._storage = dict()

    def has_mp(self, name: str) -> bool:
        return name in self._storage

    def register(self, mp: Callable, name: str=None):
        if name is None:
            name = mp.__name__

        if name in self._storage:
            print("Warning, overwriting meaning procedure '" + name + "'.")

        self._storage[name] = mp

    def run(self, mp: str, *args, **kwargs) -> Any:
        if mp not in self._storage:
            raise Exception("Unknown meaning procedure '" + mp + "'.")
        return self._storage[mp](*args, **kwargs)

    def clear(self):
        self._storage = dict()


class Executable(object):

    def __init__(self, frame: Frame):
        self.frame = frame

    def mps(self, slot="RUN") -> List['MeaningProcedure']:
        return list(map(lambda mp: MeaningProcedure(mp.resolve()), self.frame[slot]))

    def run(self, *args, slot="RUN", **kwargs) -> Any:
        if len(self.frame[slot]) == 0:
            raise Exception("No " + slot + " properties found in EXECUTABLE.")

        mps = sorted(self.mps(), key=lambda mp: mp.order())
        for mp in mps:
            mp.run(*args, **kwargs)


class MeaningProcedure(object):

    def __init__(self, frame: Frame):
        self.frame = frame

    def calls(self) -> str:
        if len(self.frame["CALLS"]) == 0:
            raise Exception("No CALLS property found in MEANING-PROCEDURE.")
        if len(self.frame["CALLS"]) > 1:
            raise Exception("Too many CALLS properties found in MEANING-PROCEDURE.")

        name = self.frame["CALLS"][0].resolve().value
        return name

    def order(self) -> int:
        if len(self.frame["ORDER"]) == 0:
            return sys.maxsize
        if len(self.frame["ORDER"]) == 1:
            return self.frame["ORDER"][0].resolve().value

        return max(map(lambda filler: filler.resolve().value, self.frame["ORDER"]))

    def run(self, *args, **kwargs) -> Any:
        name = self.calls()
        return MPRegistry.run(name, *args, **kwargs)

    def __eq__(self, other):
        if isinstance(other, MeaningProcedure):
            return self.frame == other.frame
        if isinstance(other, Frame):
            return self.frame == other
        return super().__eq__(other)


MPRegistry = Registry()