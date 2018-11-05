from backend.models.graph import Frame, Graph, Identifier
from typing import List, Union


class Environment(object):

    def __init__(self, graph: Graph):
        self.graph = graph

    def advance(self) -> Frame:
        # Create a new timestamp
        epochs = self.history()

        epoch = self.graph.register("EPOCH", isa="ENV.EPOCH", generate_index=True)
        epoch["TIME"] = len(epochs) + 1

        if len(epochs) > 0:
            last = epochs[-1]
            epoch["FOLLOWS"] = last

            for obj in last["CONTAINS"]:
                epoch["CONTAINS"] += obj

        return epoch

    def history(self) -> List[Frame]:
        epochs = list(filter(lambda f: f ^ "ENV.EPOCH" and f != self.graph["ENV.EPOCH"], self.graph.values()))
        epochs = sorted(epochs, key=lambda e: e["TIME"].singleton())

        return epochs

    def enter(self, obj: Union[str, Identifier, Frame]):
        # Something new is in the env
        if isinstance(obj, str):
            obj = Identifier.parse(obj)
        if isinstance(obj, Frame):
            obj = obj._identifier

        epoch = self.history()[-1]

        if obj not in epoch["CONTAINS"]:
            epoch["CONTAINS"] += obj

    def exit(self, obj: Union[str, Identifier, Frame]):
        # Something has exited the environment
        if isinstance(obj, str):
            obj = Identifier.parse(obj)
        if isinstance(obj, Frame):
            obj = obj._identifier

        epoch = self.history()[-1]
        epoch["CONTAINS"] -= obj

    def view(self, epoch: Union[int, str, Identifier, Frame]) -> List[Frame]:
        if isinstance(epoch, int):
            epoch = self.history()[epoch]
        if isinstance(epoch, str):
            epoch = Identifier.parse(epoch)
        if isinstance(epoch, Frame):
            epoch = epoch._identifier

        return list(map(lambda f: f.resolve(), self.graph[epoch]["CONTAINS"]))

    def current(self):
        return self.view(self.history()[-1])