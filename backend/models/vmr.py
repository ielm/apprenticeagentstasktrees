from backend.models.graph import Frame, Graph, Identifier, Literal
from backend.models.ontology import Ontology
from backend.utils.AtomicCounter import AtomicCounter
from backend.models.environment import Environment
from backend.models.graph import Network

import re
import datetime
from uuid import uuid1, uuid4


class VMR(Graph):
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

    def __init__(self, vmr_dict: dict, ontology: Ontology, agent, namespace: str = None):
        if ontology is None:
            raise Exception("VMRs must have an anchoring ontology provided.")
        if namespace is None:
            namespace = "VMR#" + str(VMR.counter.increment())

        super().__init__(namespace)

        self.ontology = ontology._namespace

        self.objects = []
        self.slices = []

        # add objects in slices to vmr objects list for reference
        for o in vmr_dict["slices"]["SLICE.1"]["contains"]:
            obj = VMRObject(o, vmr_dict["slices"]["SLICE.1"]["contains"][o])
            self.objects.append(obj)

        for key in vmr_dict:
            if key == "_id":
                self._id = uuid4() if not vmr_dict[key] else vmr_dict[key]
            elif key == "_timestamp":
                self._timestamp = datetime.datetime.now() if not vmr_dict[key] else vmr_dict[key]
            elif key == "slices":
                for s in vmr_dict[key]:
                    # update env
                    self[s] = Slice(self.objects, name=s, slice=vmr_dict[key][s])
                    # self.slices.append(Slice(name=vmr_dict[key][s]["_label"], slice=vmr_dict[key][s]))
        # self.update_environment(agent)

    def update_environment(self, agent):
        # agent.env().advance()
        # TODO -  Decide whether obj has entered or exited the environment
        # TODO - For every slice call advance, then for everything in env, exit. For everything in slice, enter. For all, move

        for slice in self._storage:
            agent.env().advance()
            # print(agent.env())
            for obj in agent.env().current():
                print(obj)
                agent.env().exit(obj)

            for obj in self[slice]:
                agent.env().enter(obj)
        print(agent.env())
        # return


class VMRObject(Frame):
    def __init__(self, name, obj, isa=None):
        super().__init__(name, isa=isa)
        self["_refers_to"] = obj["_refers_to"]
        self["_name"] = obj["_name"]
        self["_in"] = obj["_in"]
        self["LOCATION"] = obj["LOCATION"]



class Slice(Frame):
    def __init__(self, vmr_objects, name, slice=None, isa=None, ontology: Ontology = None):
        super().__init__(name, isa=isa)

        print("SLICES")
        for key in slice:
            if "contains" in key:
                # for each obj in contains
                #     refer to VMR obj frames
                #     create location per obj per slice
                # self["environment"] = Environment(slice[key])
                print(slice[key])
            elif key == "_id":
                self._id = uuid1() if not slice[key] else slice[key]
            elif key == "_timestamp":
                self._timestamp = datetime.datetime.now() if not slice[key] else slice[key]

