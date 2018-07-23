from backend.models.graph import Frame, Graph, Identifier, Literal
from backend.models.ontology import Ontology
from backend.models.syntax import Syntax
from backend.utils.AtomicCounter import AtomicCounter

import re


class TMR(Graph):

    counter = AtomicCounter()

    @staticmethod
    def new(ontology: Ontology, sentence=None, syntax=None, tmr=None, namespace=None):
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

    def __init__(self, tmr_dict: dict, ontology: Ontology, namespace: str=None):
        if ontology is None:
            raise Exception("TMRs must have an anchoring ontology provided.")
        if namespace is None:
            namespace = "TMR#" + str(TMR.counter.increment())

        super().__init__(namespace)

        self.ontology = ontology._namespace
        self.sentence = tmr_dict["sentence"]
        self.syntax = Syntax(tmr_dict["syntax"][0])

        result = tmr_dict["tmr"][0]["results"][0]["TMR"]
        for key in result:
            if key == key.upper():
                inst_dict = result[key]

                key = re.sub(r"-([0-9]+)$", ".\\1", key)

                concept = inst_dict["concept"]
                if concept is not None and ontology is not None:
                    if not concept.startswith(self.ontology):
                        concept = self.ontology + "." + concept

                self[key] = TMRInstance(key, properties=inst_dict, isa=concept, index=inst_dict["sent-word-ind"][1], ontology=ontology)

        for instance in self._storage.values():
            for slot in instance._storage.values():
                for filler in slot:
                    if isinstance(filler._value, Identifier) and filler._value.graph is None and not filler._value.render() in self:
                        filler._value.graph = self.ontology


    def __setitem__(self, key, value):
        if not isinstance(value, TMRInstance):
            raise TypeError("TMR elements must be TMRInstance objects.")
        super().__setitem__(key, value)

    def __getitem__(self, key):
        return super().__getitem__(key)

    def _frame_type(self):
        return TMRInstance

    def register(self, id, isa=None, generate_index=True):
        return super().register(id, isa=isa, generate_index=generate_index)

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
                if instance["TIME"] == [[">", "FIND-ANCHOR-TIME"]]:
                    return True

        return False

    def is_postfix(self):
        for instance in self.values():
            if instance.is_event():
                if instance["TIME"] == [["<", "FIND-ANCHOR-TIME"]]:
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

    def __init__(self, name, properties=None, isa=None, index=None, ontology: Ontology=None):
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
            # Sometimes TMR instance slots have a -1, etc., rather than being a list; by dropping this value,
            # and using += below, they are automatically converted to a list if required.
            original_key = key
            key = re.sub(r"-[0-9]+$", "", key)

            if ontology is not None \
                    and key in ontology \
                    and (ontology[key] ^ ontology["RELATION"] or ontology[key] ^ ontology["ONTOLOGY-SLOT"]):
                value = _properties[original_key]
                value = re.sub(r"-([0-9]+)$", ".\\1", value)
                identifier = Identifier.parse(value)

                if identifier.graph is None and identifier.instance is None:
                    identifier.graph = ontology._namespace

                self[key] += identifier
            else:
                self[key] += Literal(_properties[original_key])

        self.token_index = index

    def _ISA_type(self):
        return "INSTANCE-OF"

    def is_event(self):
        return self.isa(self._graph.ontology + ".EVENT")

    def is_object(self):
        return self.isa(self._graph.ontology + ".OBJECT")