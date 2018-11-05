from backend.models.graph import Frame, Graph, Identifier, Literal
from backend.models.ontology import Ontology
from backend.utils.AtomicCounter import AtomicCounter
from backend.models.environment import Environment

import re


class VMR(Graph):
    # TODO - create environment modifier function that takes Environment as input and decides if it needs to change anything in Environment
    counter = AtomicCounter()

    @staticmethod
    def new(ontology: Ontology, vmr=None, namespace=None):
        if vmr is None:
            # Create VMR that says "environment has not changed"
            vmr = [{
                "@ENV.ENVIRONMENT.1": {
                    "CHANGED": False
                }
            }]
            return VMR(vmr[0], ontology, namespace=namespace)

    def __init__(self, vmr_dict: dict, ontology: Ontology, namespace: str = None):
        if ontology is None:
            raise Exception("VMRs must have an anchoring ontology provided.")
        if namespace is None:
            namespace = "VMR#" + str(VMR.counter.increment())

        super().__init__(namespace)

        self.ontology = ontology._namespace

        # I know there will be a better way to do this
        # At the moment keys in VMRs need to be known concepts in the environment
        for key in vmr_dict:
            if key == key.upper():
                inst_dict = vmr_dict[key]

                key = re.sub(r"-([0-9]+)$", ".\\1", key)

                #     TODO - create self[key] VMRInstance for all keys in vmr
                self[key] = VMRInstance(key, properties=inst_dict, isa=None, ontology=ontology)

        for instance in self._storage.values():
            for slot in instance._storage.values():
                for filler in slot:
                    if isinstance(filler._value, Identifier) and filler._value.graph is None and not filler._value.render() in self:
                        filler._value.graph = self.ontology

    def update_environment(self, env: Environment, vmr=None):
        env.advance()
        # Decide whether obj has entered or exited the environment

        return


class VMRInstance(Frame):
    def __init__(self, name, properties=None, isa=None, ontology: Ontology = None):
        super().__init__(name, isa=isa)

        if properties is None:
            properties = {}

        _properties = {}
        for key in properties:
            # Not sure if this is relevant in VMR
            if "_constraint_info" in key:
                pass
            if key == key.upper():
                _properties[key] = properties[key]

        for key in _properties:
            original_key = key
            key = re.sub(r"-[0-9]+$", "", key)

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