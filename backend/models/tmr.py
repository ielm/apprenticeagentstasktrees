from backend.models.graph import Frame, Graph, Identifier, Literal, Network
from backend.models.ontology import Ontology
from backend.models.syntax import Syntax
from backend.models.xmr import XMR
from backend.utils.AtomicCounter import AtomicCounter

from typing import Union

import re


class TMR(XMR):

    counter = AtomicCounter()

    @classmethod
    def from_contents(cls, network: Network, ontology: Ontology, sentence: str=None, syntax: dict=None, tmr: dict=None, namespace: str=None, source: Union[str, Identifier, Frame]=None) -> 'TMR':

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

        tmr_dict = {
            "sentence": sentence,
            "syntax": syntax,
            "tmr": tmr
        }

        return TMR.from_json(network, ontology, tmr_dict, namespace=namespace, source=source)

    @classmethod
    def from_json(cls, network: Network, ontology: Ontology, tmr_dict: dict, namespace: str=None, source: Union[str, Identifier, Frame]=None) -> 'TMR':

        if ontology is None:
            raise Exception("TMRs must have an anchoring ontology provided.")
        if namespace is None:
            namespace = "TMR#" + str(TMR.counter.increment())

        graph = network.register(TMRGraph(namespace))

        result = tmr_dict["tmr"][0]["results"][0]["TMR"]
        for key in result:
            if key == key.upper():
                inst_dict = result[key]

                key = re.sub(r"-([0-9]+)$", ".\\1", key)

                concept = inst_dict["concept"]
                if concept is not None and ontology is not None:
                    if not concept.startswith(ontology._namespace):
                        concept = ontology._namespace + "." + concept

                graph[key] = TMRFrame.parse(key, properties=inst_dict, isa=concept, index=inst_dict["sent-word-ind"][1], ontology=ontology)

        for instance in graph._storage.values():
            for slot in instance._storage.values():
                for filler in slot:
                    if isinstance(filler._value, Identifier) and filler._value.graph is None and not filler._value.render() in graph:
                        filler._value.graph = ontology._namespace
                    elif isinstance(filler._value, Identifier) and filler._value.graph is None:
                        filler._value.graph = namespace

        def find_root() -> Frame:
            event = None
            for instance in graph.values():
                try:
                    if instance ^ "ONT.EVENT":
                        event = instance
                        break
                except: pass

            while event is not None and "PURPOSE-OF" in event:
                event = event["PURPOSE-OF"][0].resolve()

            return event

        tmr: TMR = XMR.instance(network["INPUTS"], graph, XMR.Signal.INPUT, XMR.Type.LANGUAGE, XMR.InputStatus.RECEIVED, source, find_root())
        tmr.frame["SENTENCE"] = Literal(tmr_dict["sentence"])
        tmr.frame["SYNTAX"] = Syntax(tmr_dict["syntax"][0])

        return tmr

    def syntax(self) -> Syntax:
        return self.frame["SYNTAX"].singleton()

    def render(self):
        if "SENTENCE" not in self.frame:
            return super().render()
        return self.frame["SENTENCE"].singleton()

    def find_main_event(self):
        event = None
        for instance in self.graph(self.frame._graph._network).values():
            if instance.is_event():
                event = instance
                break

        while event is not None and "PURPOSE-OF" in event:
            event = event["PURPOSE-OF"][0].resolve()

        return event

    def is_prefix(self):
        for instance in self.graph(self.frame._graph._network).values():
            if instance.is_event():
                if instance["TIME"] == [[">", "FIND-ANCHOR-TIME"]]:
                    return True

        return False

    def is_postfix(self):
        for instance in self.graph(self.frame._graph._network).values():
            if instance.is_event():
                if instance["TIME"] == [["<", "FIND-ANCHOR-TIME"]]:
                    return True

        # For closing generic events, such as "Finished."
        for instance in self.graph(self.frame._graph._network).values():
            if instance.isa("ONT.ASPECT"):
                if instance["PHASE"] == "END":
                    scopes = list(map(lambda filler: filler.resolve().concept(), instance["SCOPE"]))  # TODO: this needs search functionality ("is a filler in the slot exactly concept X?")
                    if "ONT.EVENT" in scopes:
                        return True

        return False

    # TODO: Ultimately, replace with a generic querying capability
    def find_by_concept(self, concept):
        instances = list(filter(lambda instance: instance.isa(concept), self.graph(self.frame._graph._network).values()))
        return instances


class TMRFrame(Frame):

    @classmethod
    def parse(cls, name, properties=None, isa=None, index=None, ontology: Ontology=None) -> 'TMRFrame':
        frame = TMRFrame(name, isa=isa)

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
                if not isinstance(value, list):
                    value = [value]
                for v in value:
                    v = re.sub(r"-([0-9]+)$", ".\\1", v)
                    identifier = Identifier.parse(v)

                    if identifier.graph is None and identifier.instance is None:
                        identifier.graph = ontology._namespace

                    frame[key] += identifier
            else:
                frame[key] += Literal(_properties[original_key])

        frame.token_index = index

        return frame

    def _ISA_type(self):
        return "INSTANCE-OF"

    def is_event(self):
        return self.isa("ONT.EVENT")

    def is_object(self):
        return self.isa("ONT.OBJECT")

    def tmr(self) -> TMR:
        network: Network = self._graph._network
        results = network.search(Frame.q(network).f("REFERS-TO-GRAPH", Literal(self._graph._namespace)))
        if len(results) != 1:
            raise Exception("TMR wrapper node not found.")

        return TMR(results[0])


class TMRGraph(Graph):

    def _frame_type(self):
        return TMRFrame

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
            if instance.isa("ONT.ASPECT"):
                if instance["PHASE"] == "END":
                    scopes = list(map(lambda filler: filler.resolve().concept(), instance["SCOPE"]))  # TODO: this needs search functionality ("is a filler in the slot exactly concept X?")
                    if "ONT.EVENT" in scopes:
                        return True

        return False
