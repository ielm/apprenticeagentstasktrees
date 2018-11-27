from backend.models.graph import Frame, Graph, Identifier, Literal
from backend.models.ontology import Ontology
from backend.utils.AtomicCounter import AtomicCounter
from backend.models.environment import Environment

import re
import datetime
from uuid import uuid1, uuid4


class VMR(Graph):
    """
    VMR is a relational DAG. Maybe we will want to use Spatio-Temporal DAGs for this?

    Each temporal "slice" is a time-stamped DAG, which contains the main ENV node, all OBJECT or EVENT nodes that are "in" the environment, and all properties associated with OBJECT/EVENT nodes.
    For now, each "slice" gets its own full ENV graph; for the future, maybe we can look at version control systems to update only what has changed in the ENV graph for each slice, but maintain temporality.
    Slices don't have to be recorded with any specific frequency, so a VMR may have a range from a few milliseconds to multiple minutes in between slice timestamps.


    All objects in the environment are OBJECT nodes, which have an [_IN] relational mapping to the environment, which is an ENV node.
    All OBJECT nodes also have relative position relations with all other objects, kept at the coarsest possible granularity until more accurate positioning is needed.

    OBJECT nodes can be EFFECTOR/s which are special objects that are a part of the agent itself and have functional capabilities defined in bootstrap.knowledge, as well as properties
    The robot/agent is also a special object type, SELF, which refers to itself. EFFECTOR/s are connected to SELF by the _EFFECTOR_OF relation. Needless to say that SELF also has a set of properties.


    Properties of OBJECT nodes include:
        - general (approximate) location using current position as reference

                     {<timestamp>}
                     [Environment]
                  __/      |     \__
                 /    [__SELF__]    \
           [Jake.#]                [Chair.#]
        __/   |   \__             __/     \__
       /      |      \           /           \
     [_pos][_name][_interax]   [_status]     [_pos]

The environment contains STORAGE.1, STORAGE.2, and WORKSPACE.1, which are each their own micro environments. They always come first in the ENVIRONMENT graph.
    "slices": {
        "SLICE.1": {
            "ENVIRONMENT.1": {
                "_refers_to": {},
                "contains": {
                    "STORAGE.1": {
                        "contains": {}
                    },
                    "STORAGE.2": {
                        "contains": {}
                    },
                    "WORKSPACE.1": {
                        "contains": {}
                    },
                }
            },
            "_timestamp": datetime.datetime.now(),
            "_id": uuid1(),  # use uuid1 for slice IDs
        }
    """
    # TODO - create environment modifier function that takes Environment as input and decides if it needs to change anything in Environment
    counter = AtomicCounter()

    @staticmethod
    def new(ontology: Ontology, vmr=None, namespace=None, id=None):
        if vmr is None:
            vmr = [{
                "_id": uuid4() if not id else id,  # use uuid4 for vmr IDs
                "slices": [{
                    "SLICE.1": [{
                        "ENVIRONMENT.1": [{
                            "_refers_to": {},
                            "contains": {}
                        }],
                        "_timestamp": datetime.datetime.now(),
                        "_id": uuid1(),  # use uuid1 for slice IDs
                    }],
                }],
                "_label": None,
                "_visual_frames": None,
            }]
            return VMR(vmr[0], ontology, namespace=namespace)

    def __init__(self, vmr_dict: dict, ontology: Ontology, namespace: str = None):
        if ontology is None:
            raise Exception("VMRs must have an anchoring ontology provided.")
        if namespace is None:
            namespace = "VMR#" + str(VMR.counter.increment())

        super().__init__(namespace)

        self.ontology = ontology._namespace

        self.slices = []
        # TODO - create Slice instance for each slice in VMR

        for key in vmr_dict:
            if key == "_id":
                self._id = uuid4() if not vmr_dict[key] else vmr_dict[key]
            if key == "slices":
                for s in vmr_dict[key]:
                    # print()
                    print(vmr_dict[key][s])
                    self.slices.append(Slice(vmr_dict[key][s]))

        for instance in self._storage.values():
            for slot in instance._storage.values():
                for filler in slot:
                    if isinstance(filler._value, Identifier) and filler._value.graph is None and not filler._value.render() in self:
                        filler._value.graph = self.ontology

    def update_environment(self, env: Environment, vmr=None):
        env.advance()
        # TODO -  Decide whether obj has entered or exited the environment
        # TODO - For every slice call advance, then for everything in env, exit. For everything in slice, enter. For all, move
        return


class VMRInstance(Frame):
    def __init__(self, name, properties=None, isa=None, ontology: Ontology = None):
        super().__init__(name, isa=isa)

        if properties is None:
            properties = {}

        _properties = {}
        for key in properties:
            if key == key.upper():
                _properties[key] = properties[key]

        for key in properties:
            original_key = key
            key = re.sub(r"-[0-9]+$", "", key)

            # if key == "slices":
            #     if ontology is not None \
            #     and key in ontology \
            #     and


class Slice(Frame):
    def __init__(self, name, slice=None, isa=None, ontology: Ontology = None):
        super().__init__(name, isa=isa)

        # g = agent.register("ENV")

        # environment = Environment(g)



