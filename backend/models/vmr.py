from backend.models.graph import Frame, Graph, Identifier, Literal
from backend.models.ontology import Ontology
from backend.utils.AtomicCounter import AtomicCounter
from backend.models.environment import Environment

import re
import datetime


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


    To represent Jake leaving:

    VMR: [
        SLICES: [
            SLICE#1:[
                ENVIRONMENT#1: [
                    _CONTAINS:[
                        LT.HUMAN.1: [
                            _IDENTIFIER: "Jake",
                            _LOCATION: HERE,
                            _IN: ENVIRONMENT#1,
                        ],
                        LT.CHAIR.1: [
                            _LOCATION: HERE,
                            _IN: ENVIRONMENT#1,
                        ],
                    ]
                ],
                _timestamp: <FIND-ANCHOR-TIME>
            ],
            SLICE#2:[
                ENVIRONMENT#1: [
                    _IN:[
                        LT.HUMAN.1: [
                            _IDENTIFIER: "Jake",
                            _LOCATION: NOT_HERE,
                            _IN: ENVIRONMENT#1,
                        ],
                        LT.CHAIR.1: [
                            _LOCATION: HERE,
                            _IN: ENVIRONMENT#1,
                        ],
                    ]
                ],
                _timestamp: <FIND-ANCHOR-TIME += 1>
            ]
        ],
        _LABEL: "Jake has left.",
        _VISUAL_FRAMES: <sequence of images corresponding to vmr>,
    ]


    """
    # TODO - create environment modifier function that takes Environment as input and decides if it needs to change anything in Environment
    counter = AtomicCounter()

    @staticmethod
    def new(ontology: Ontology, vmr=None, namespace=None):
        if vmr is None:
            vmr = [{
                "SLICES": [{
                    "VMR.SLICE.1": [{
                        "@ENV.ENVIRONMENT.1": [{
                            "_CONTAINS": {},
                        }],
                        "_timestamp": datetime.datetime.now(),
                    }],
                }],
                "_label": None,
                "_VISUAL_FRAMES": None,
            }]
            return VMR(vmr[0], ontology, namespace=namespace)

    def __init__(self, vmr_dict: dict, ontology: Ontology, namespace: str = None):
        if ontology is None:
            raise Exception("VMRs must have an anchoring ontology provided.")
        if namespace is None:
            namespace = "VMR#" + str(VMR.counter.increment())

        super().__init__(namespace)

        self.ontology = ontology._namespace
        # self.environment = Environment()

        for key in vmr_dict:
            if key == "_timestamp" or key == "_label":
                self._timestamp = vmr_dict[key]
            if key == key.upper():
                inst_dict = vmr_dict[key]

                key = re.sub(r"-([0-9]+)$", ".\\1", key)

                #     TODO - create self[key] VMRInstance for all keys in vmr
                self[key] = VMRInstance(key, properties=inst_dict, isa=None, ontology=ontology)

        """
        for instance in self._storage.values():
            for slot in instance._storage.values():
                for filler in slot:
                    if isinstance(filler._value, Identifier) and filler._value.graph is None and not filler._value.render() in self:
                        filler._value.graph = self.ontology
        """

    def update_environment(self, env: Environment, vmr=None):
        env.advance()
        # TODO -  Decide whether obj has entered or exited the environment
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

            # if key == "SLICES":
            #     if ontology is not None \
            #     and key in ontology \
            #     and

    """

            if ontology is not None \
                    and key in ontology \
                    and (ontology[key] ^ ontology["RELATION"]
                         or ontology[key] ^ ontology["ONTOLOGY-SLOT"]):
                value = _properties[original_key]
                if not isinstance(value, list):
                    value = [value]
                for v in value:
                    v = re.sub(r"-([0-9]+)$", ".\\1", v)
                    identifier = Identifier.parse(v)

                    if identifier.graph is None and identifier.instance is None:
                        identifier.graph = ontology._namespace

                    self[key] += identifier
            else:
                self[key] += Literal(_properties[original_key])
    """