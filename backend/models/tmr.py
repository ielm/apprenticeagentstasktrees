from backend.models.graph import Frame, Graph
from backend.models.ontology import Ontology
from backend.models.syntax import Syntax

from typing import Union
from uuid import uuid4


class TMR(Graph):

    @staticmethod
    def new(ontology, sentence=None, syntax=None, tmr=None, namespace=None):
        if sentence is None:
            sentence = ""
        if syntax is None:
            syntax = [{
                "basicDeps": {}
            }]
        if tmr is None:
            tmr = [{
                "results": [{
                    "TMR": {}
                }]
            }]

        return TMR({
            "sentence": sentence,
            "syntax": syntax,
            "tmr": tmr
        }, ontology, namespace=namespace)

    def __init__(self, tmr_dict: dict, ontology: Union[Ontology, str], namespace: str=None):
        if ontology is None:
            raise Exception("TMRs must have an anchoring ontology provided.")
        if namespace is None:
            namespace = "TMR#" + str(uuid4())

        super().__init__(namespace)

        if isinstance(ontology, Ontology):
            ontology = ontology._namespace

        self.ontology = ontology
        self.sentence = tmr_dict["sentence"]
        self.syntax = Syntax(tmr_dict["syntax"][0])

        result = tmr_dict["tmr"][0]["results"][0]["TMR"]
        for key in result:
            if key == key.upper():
                inst_dict = result[key]

                concept = inst_dict["concept"]
                if concept is not None and ontology is not None:
                    if not concept.startswith(ontology):
                        concept = ontology + "." + concept

                self[key] = TMRInstance(key, properties=inst_dict, isa=concept, index=inst_dict["sent-word-ind"][1])

    def __setitem__(self, key, value):
        if not isinstance(value, TMRInstance):
            raise TypeError("TMR elements must be TMRInstance objects.")
        super().__setitem__(key, value)

    def __getitem__(self, key):
        if key == "HUMAN" or key == "ROBOT":
            return key

        return super().__getitem__(key)

    def _frame_type(self):
        return TMRInstance

    def find_main_event(self):
        event = None
        for instance in self.values():
            if instance.is_event():
                event = instance
                break

        while event is not None and "PURPOSE-OF" in event:
            event = event["PURPOSE-OF"][0].resolve()

        return event

    def is_prefix(self):
        for instance in self.values():
            if instance.is_event():
                if instance["TIME"] == ">" and instance["TIME"] == "FIND-ANCHOR-TIME":
                    return True

        return False

    def is_postfix(self):
        for instance in self.values():
            if instance.is_event():
                if instance["TIME"] == "<" and instance["TIME"] == "FIND-ANCHOR-TIME":
                    return True

        # For closing generic events, such as "Finished."
        for instance in self.values():
            if instance.isa(self.ontology + ".ASPECT"):
                if instance["PHASE"] == "END":
                    scopes = list(map(lambda filler: filler.resolve().concept(), instance["SCOPE"]))  # TODO: this needs search functionality ("is a filler in the slot exactly concept X?")
                    if self.ontology + ".EVENT" in scopes:
                        return True

        return False

    # TODO: Ultimately, replace with a generic querying capability
    def find_by_concept(self, concept):
        instances = list(filter(lambda instance: instance.isa(concept), self.values()))
        return instances


class TMRInstance(Frame):

    def __init__(self, name, properties=None, isa=None, index=None):
        super().__init__(name, isa=isa)

        if properties is None:
            properties = {}

        _properties = {}
        for key in properties:
            if "_constraint_info" in key:
                pass
            if key == key.upper():
                _properties[key] = properties[key]

        for key in _properties:
            self[key] = _properties[key]

        self.token_index = index

    def is_event(self):
        return self.isa(self._graph.ontology + ".EVENT")

    def is_object(self):
        return self.isa(self._graph.ontology + ".OBJECT")