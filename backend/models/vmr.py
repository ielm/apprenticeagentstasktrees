from backend.models.environment import Environment
from backend.models.graph import Frame, Graph, Literal
from backend.models.ontology import Ontology
from backend.utils.AtomicCounter import AtomicCounter

import time
from typing import List, Union


class VMR(Graph):
    # TODO - create environment modifier function that takes Environment as input and decides if it needs to change anything in Environment
    counter = AtomicCounter()

    @staticmethod
    def new(ontology: Ontology, refers_to: str=None, timestamp: str=None, contains: dict=None, events: dict=None, namespace: str=None):
        if refers_to is None:
            refers_to = "ENV"

        if timestamp is None:
            timestamp = time.time()

        if contains is None:
            contains = {}

        if events is None:
            events = {}

        vmr_dict = {
            "ENVIRONMENT": {
                "_refers_to": refers_to,
                "timestamp": timestamp,
                "contains": contains
            },
            "EVENTS": events
        }

        return VMR(vmr_dict, ontology, namespace=namespace)

    def __init__(self, vmr_dict: dict, ontology: Ontology, namespace: str = None):
        if ontology is None:
            raise Exception("VMRs must have an anchoring ontology provided.")
        if namespace is None:
            namespace = "VMR#" + str(VMR.counter.increment())

        super().__init__(namespace)

        self.ontology = ontology._namespace

        reference = self.register("ENVIRONMENT", generate_index=False)
        events = self.register("EVENTS", generate_index=False)

        if "ENVIRONMENT" in vmr_dict:

            reference["REFERS-TO"] = Literal(vmr_dict["ENVIRONMENT"]["_refers_to"])
            reference["TIMESTAMP"] = Literal(vmr_dict["ENVIRONMENT"]["timestamp"])

            for frame in vmr_dict["ENVIRONMENT"]["contains"]:
                location = vmr_dict["ENVIRONMENT"]["contains"][frame]["LOCATION"]
                if location == "NOT-HERE":
                    continue

                if location == "HERE":
                    location = reference

                location_frame = self.register("LOCATION", generate_index=True)
                location_frame["DOMAIN"] = frame
                location_frame["RANGE"] = location

        if "EVENTS" in vmr_dict:

            for frame in vmr_dict["EVENTS"]:
                contents = vmr_dict["EVENTS"][frame]
                frame = self.register(frame)
                for slot in contents:
                    for filler in contents[slot]:
                        frame[slot] += filler
                events["HAS-EVENT"] += frame

    def locations(self) -> List[Frame]:
        return list(map(lambda f: self[f], filter(lambda f: self[f]._identifier.name == "LOCATION", self)))

    def update_environment(self, environment: Union[Graph, Environment]):
        if isinstance(environment, Graph):
            environment = Environment(environment)

        environment.advance()
        for object in environment.current():
            environment.exit(object)

        for location_marker in self.locations():
            object = location_marker["DOMAIN"].singleton()
            location = location_marker["RANGE"].singleton()

            if location == self["ENVIRONMENT"]:
                location = "ONT.LOCATION"

            environment.enter(object, location=location)

    def events(self) -> List[Frame]:
        return list(map(lambda f: f.resolve(), self["EVENTS"]["HAS-EVENT"]))

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
