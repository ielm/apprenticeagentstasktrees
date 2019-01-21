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

        environment.advance()
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
