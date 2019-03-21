from backend.models.environment import Environment
from backend.models.xmr import XMR
from backend.utils.AtomicCounter import AtomicCounter
from ontograph.Frame import Frame
from ontograph.Index import Identifier
from ontograph.Space import Space
from typing import List, Union

import time


class VMR(XMR):
    counter = AtomicCounter()

    @classmethod
    def from_contents(cls, contains: dict=None, events: dict=None, namespace: str=None, source: Union[str, Identifier, Frame]=None) -> 'VMR':

        if contains is None:
            contains = {}

        if events is None:
            events = {}

        vmr_dict = {
            "ENVIRONMENT": {
                "_refers_to": "ENV",
                "timestamp": time.time(),
                "contains": contains
            },
            "EVENTS": events
        }

        return VMR.from_json(vmr_dict, namespace=namespace, source=source)

    @classmethod
    def from_json(cls, vmr_dict: dict, namespace: str=None, source: Union[str, Identifier, Frame]=None) -> 'VMR':
        if namespace is None:
            namespace = "VMR#" + str(VMR.counter.increment())

        space = Space(namespace)

        reference = Frame("@" + space.name + ".ENVIRONMENT")
        events = Frame("@" + space.name + ".EVENTS")

        if "ENVIRONMENT" in vmr_dict:

            reference["REFERS-TO"] = vmr_dict["ENVIRONMENT"]["_refers_to"]
            reference["TIMESTAMP"] = vmr_dict["ENVIRONMENT"]["timestamp"]

            for frame in vmr_dict["ENVIRONMENT"]["contains"]:
                location = vmr_dict["ENVIRONMENT"]["contains"][frame]["LOCATION"]
                if location == "NOT-HERE":
                    continue

                if location == "HERE":
                    location = reference

                location_frame = Frame("@" + space.name + ".LOCATION.?")
                location_frame["DOMAIN"] = frame
                location_frame["RANGE"] = location

        if "EVENTS" in vmr_dict:

            for frame in vmr_dict["EVENTS"]:
                contents = vmr_dict["EVENTS"][frame]
                parts = Identifier.parse(frame)
                if isinstance(parts[0], str) and isinstance(parts[1], str) and parts[2] is None:
                    frame = "@" + space.name + "." + parts[0] + "." + str(parts[1])
                frame = Frame(frame)
                for slot in contents:
                    for filler in contents[slot]:
                        frame[slot] += filler
                events["HAS-EVENT"] += frame

        vmr: VMR = XMR.instance(Space("INPUTS"), space, XMR.Signal.INPUT, XMR.Type.VISUAL, XMR.InputStatus.RECEIVED, source, reference)
        return vmr

    def locations(self) -> List[Frame]:
        space = self.space()
        return list(filter(lambda f: Identifier.parse(f.id)[1] == "LOCATION", space))

    def update_environment(self, environment: Union[Space, Environment]):
        if isinstance(environment, Space):
            environment = Environment(environment)

        epoch = environment.advance()
        self.frame["EPOCH"] = epoch

        for object in environment.current():
            environment.exit(object)

        for location_marker in self.locations():
            object = location_marker["DOMAIN"].singleton()
            location = location_marker["RANGE"].singleton()

            if location == Frame("@" + self.space().name + ".ENVIRONMENT"):
                location = "@ONT.LOCATION"

            environment.enter(object, location=location)

    def events(self) -> List[Frame]:
        return list(Frame("@" + self.space().name + ".EVENTS")["HAS-EVENT"])

    def epoch(self) -> Frame:
        return self.frame["EPOCH"].singleton()

    def update_memory(self, space: Space):
        for event in self.events():
            parents = event.parents()
            if len(parents) == 0:
                parents = [event.id]

            frame = Frame("@" + space.name + "." + Identifier.parse(event.id)[1] + ".?")
            for parent in parents:
                frame.add_parent(parent)

            for slot in event:
                if slot.property == "IS-A":
                    continue
                for filler in slot:
                    frame[slot.property] += filler

    def render(self):

        observations = []

        def get_location(env: Environment, object: Frame, epoch: Frame) -> Union[Frame, None]:
            try:
                return env.location(object, epoch)
            except:
                return None

        def get_then(now: Frame) -> Frame:
            if len(now["FOLLOWS"]) == 0:
                return Frame("@ENV.NO-SUCH-EPOCH", declare=False)
            return now["FOLLOWS"].singleton()

        def get_view(env: Environment, epoch: Frame) -> List[Frame]:
            try:
                return env.view(epoch)
            except:
                return []

        def get_name(frame: Frame) -> str:
            if "NAME" in frame:
                return frame["NAME"].singleton()
            if "HAS-NAME" in frame:
                return frame["HAS-NAME"].singleton()
            return frame.id

        try:
            env = Environment(Space("ENV"))

            now = self.epoch()
            then = get_then(now)

            all_known_objects = set(get_view(env, now))
            all_known_objects = all_known_objects.union(get_view(env, then))

            for o in all_known_objects:
                location_now = get_location(env, o, now)
                location_then = get_location(env, o, then)

                if location_now != None and location_then != None and location_now != location_then:
                    observations.append("I see that " + get_name(o) + " moved from the " + get_name(location_then) + " to the " + get_name(location_now))

                if location_now != None and location_then == None:
                    observations.append("I see that " + get_name(o) + " is now in the environment, at the " + get_name(location_now))

                if location_now == None and location_then != None:
                    observations.append("I see that " + get_name(o) + " has left the environment")
        except: pass

        try:
            for e in self.events():
                agent = e["AGENT"].singleton()
                theme = e["THEME"].singleton()
                action = Identifier.parse(e.id)[1]

                observations.append("I see that " + get_name(agent) + " did " + action + "(" + get_name(theme) + ")")


        except: pass

        if len(observations) == 0:
            return super().render()

        return "; and ".join(observations) + "."
