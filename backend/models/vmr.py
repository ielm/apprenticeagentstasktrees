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
    def new(ontology: Ontology, refers_to: str=None, timestamp: str=None, contains: dict=None, namespace: str=None):
        if refers_to is None:
            refers_to = "ENV"

        if timestamp is None:
            timestamp = time.time()

        if contains is None:
            contains = {}

        vmr_dict = {
            "ENVIRONMENT": {
                "_refers_to": refers_to,
                "timestamp": timestamp,
                "contains": contains
            }
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

