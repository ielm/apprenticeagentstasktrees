from backend.models.environment import Environment
from backend.models.graph import Frame, Graph, Identifier, Literal, Network
from backend.models.ontology import Ontology
from backend.models.xmr import XMR
from backend.utils.AtomicCounter import AtomicCounter

import time
from typing import List, Union


class VMR(XMR):
    counter = AtomicCounter()

    @classmethod
    def from_contents(cls, network: Network, ontology: Ontology, contains: dict=None, events: dict=None, namespace: str=None, source: Union[str, Identifier, Frame]=None) -> 'VMR':

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

        return VMR.from_json(network, ontology, vmr_dict, namespace=namespace, source=source)

    @classmethod
    def from_json(cls, network: Network, ontology: Ontology, vmr_dict: dict, namespace: str=None, source: Union[str, Identifier, Frame]=None) -> 'VMR':
        if ontology is None:
            raise Exception("VMRs must have an anchoring ontology provided.")
        if namespace is None:
            namespace = "VMR#" + str(VMR.counter.increment())

        graph = network.register(namespace)

        reference = graph.register("ENVIRONMENT", generate_index=False)
        events = graph.register("EVENTS", generate_index=False)

        if "ENVIRONMENT" in vmr_dict:

            reference["REFERS-TO"] = Literal(vmr_dict["ENVIRONMENT"]["_refers_to"])
            reference["TIMESTAMP"] = Literal(vmr_dict["ENVIRONMENT"]["timestamp"])

            for frame in vmr_dict["ENVIRONMENT"]["contains"]:
                location = vmr_dict["ENVIRONMENT"]["contains"][frame]["LOCATION"]
                if location == "NOT-HERE":
                    continue

                if location == "HERE":
                    location = reference

                location_frame = graph.register("LOCATION", generate_index=True)
                location_frame["DOMAIN"] = frame
                location_frame["RANGE"] = location

        if "EVENTS" in vmr_dict:

            for frame in vmr_dict["EVENTS"]:
                contents = vmr_dict["EVENTS"][frame]
                frame = graph.register(frame)
                for slot in contents:
                    for filler in contents[slot]:
                        frame[slot] += filler
                events["HAS-EVENT"] += frame

        vmr: VMR = XMR.instance(network["INPUTS"], graph, XMR.Signal.INPUT, XMR.Type.VISUAL, XMR.InputStatus.RECEIVED, source, graph["ENVIRONMENT"])
        return vmr

    def _network(self) -> Network:
        return self.frame._graph._network

    def locations(self) -> List[Frame]:
        graph = self.graph(self._network())
        return list(map(lambda f: graph[f], filter(lambda f: graph[f]._identifier.name == "LOCATION", graph)))

    def update_environment(self, environment: Union[Graph, Environment]):
        if isinstance(environment, Graph):
            environment = Environment(environment)

        epoch = environment.advance()
        self.frame["EPOCH"] = epoch

        for object in environment.current():
            environment.exit(object)

        for location_marker in self.locations():
            object = location_marker["DOMAIN"].singleton()
            location = location_marker["RANGE"].singleton()

            if location == self.graph(self._network())["ENVIRONMENT"]:
                location = "ONT.LOCATION"

            environment.enter(object, location=location)

    def events(self) -> List[Frame]:
        return list(map(lambda f: f.resolve(), self.graph(self._network())["EVENTS"]["HAS-EVENT"]))

    def epoch(self) -> Frame:
        return self.frame["EPOCH"].singleton()

    def update_memory(self, graph: Graph):
        for event in self.events():
            parents = event.parents()
            if len(parents) == 0:
                parents = [event._identifier.name]

            frame = graph.register(event._identifier.name, isa=parents, generate_index=True)

            for slot in event:
                if slot == event._ISA_type():
                    continue
                for filler in event[slot]:
                    frame[slot] += filler

    def render(self):

        observations = []

        def get_location(env: Environment, object: Frame, epoch: Frame) -> Union[Frame, None]:
            try:
                return env.location(object, epoch)
            except:
                return None

        def get_then(now: Frame) -> Frame:
            if len(now["FOLLOWS"]) == 0:
                return Frame("NO-SUCH-EPOCH")
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
            return frame.name()

        try:
            env = Environment(self.frame._graph._network["ENV"])

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
                action = e._identifier.name

                observations.append("I see that " + get_name(agent) + " did " + action + "(" + get_name(theme) + ")")


        except: pass

        if len(observations) == 0:
            return super().render()

        return "; and ".join(observations) + "."
