from ontograph.Frame import Frame
from ontograph.Index import Identifier
from ontograph.Space import Space
from typing import List, Union


class Environment(object):

    def __init__(self, space: Space):
        self.space = space

    def advance(self) -> Frame:
        # Create a new timestamp
        epochs = self.history()

        epoch = Frame("@" + self.space.name + ".EPOCH.?").add_parent("@ENV.EPOCH")
        epoch["TIME"] = len(epochs) + 1

        if len(epochs) > 0:
            last = epochs[-1]
            epoch["FOLLOWS"] = last

            for obj in last["CONTAINS"]:
                epoch["CONTAINS"] += obj

            for location in last["LOCATION"]:
                copy = Frame("@" + self.space.name + ".SPATIAL-LOCATION.?").add_parent("@ONT.LOCATION")
                copy["DOMAIN"] = location["DOMAIN"].singleton()
                copy["RANGE"] = location["RANGE"].singleton()
                epoch["LOCATION"] += copy
        return epoch

    def history(self) -> List[Frame]:
        epochs = list(filter(lambda f: f ^ "@ENV.EPOCH" and f != Frame("@ENV.EPOCH"), self.space))
        epochs = sorted(epochs, key=lambda e: e["TIME"].singleton())

        return epochs

    def enter(self, obj: Union[str, Identifier, Frame], location: Frame=None):
        if isinstance(obj, str):
            obj = Frame(obj)

        if location is None:
            location = "@ONT.LOCATION"

        epoch = self.history()[-1]

        if obj not in epoch["CONTAINS"]:
            epoch["CONTAINS"] += obj
            self.move(obj, location=location)

    def exit(self, obj: Union[str, Identifier, Frame]):
        if isinstance(obj, str):
            obj = Frame(obj)

        epoch = self.history()[-1]
        epoch["CONTAINS"] -= obj

        for d in epoch["LOCATION"]:
            if d["DOMAIN"] == obj:
                d["RANGE"] = None

    def move(self, obj: Union[str, Identifier, Frame], location: Frame):
        if isinstance(obj, str):
            obj = Frame(obj)

        epoch = self.history()[-1]
        for d in epoch["LOCATION"]:
            if d["DOMAIN"] == obj:
                d["RANGE"] = location
                return

        d = Frame("@" + self.space.name + ".LOCATION.?").add_parent("@ONT.LOCATION")
        d["DOMAIN"] = obj
        d["RANGE"] = location
        epoch["LOCATION"] += d

    def view(self, epoch: Union[int, str, Identifier, Frame]) -> List[Frame]:
        if isinstance(epoch, int):
            epoch = self.history()[epoch]
        if isinstance(epoch, str):
            epoch = Frame(epoch)
        if isinstance(epoch, Identifier):
            epoch = Frame(epoch.id)

        return list(epoch["CONTAINS"])

    def current(self):
        return self.view(self.history()[-1])

    def location(self, obj: Union[str, Identifier, Frame], epoch: Union[int, str, Identifier, Frame]=-1) -> Frame:
        if isinstance(epoch, int):
            epoch = self.history()[epoch]
        if isinstance(epoch, str):
            epoch = Frame(epoch)
        if isinstance(epoch, Identifier):
            epoch = Frame(epoch.id)

        if isinstance(obj, str):
            obj = Frame(obj)
        if isinstance(obj, Identifier):
            obj = Frame(obj.id)

        for d in epoch["LOCATION"]:
            if d["DOMAIN"] == obj:
                location = d["RANGE"].singleton()
                if location is not None:
                    return location
        raise Exception("Location unknown.")