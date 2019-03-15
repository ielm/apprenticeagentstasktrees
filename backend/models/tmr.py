from backend.models.syntax import Syntax
from backend.models.xmr import XMR
from backend.utils.AtomicCounter import AtomicCounter
from ontograph.Frame import Frame
from ontograph.Index import Identifier
from ontograph.Space import Space
from typing import Union

import re


class TMR(XMR):

    counter = AtomicCounter()

    @classmethod
    def from_contents(cls, sentence: str=None, syntax: dict=None, tmr: dict=None, namespace: str=None, source: Union[str, Identifier, Frame]=None) -> 'TMR':

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

        return TMR.from_json(tmr_dict, namespace=namespace, source=source)

    @classmethod
    def from_json(cls, tmr_dict: dict, namespace: str=None, source: Union[str, Identifier, Frame]=None) -> 'TMR':

        if namespace is None:
            namespace = "TMR#" + str(TMR.counter.increment())

        space = Space(namespace)

        result = tmr_dict["tmr"][0]["results"][0]["TMR"]

        frame_ids = {}
        for key in result:
            if key == key.upper():
                frame_id = "@" + space.name + "." + re.sub(r"-([0-9]+)$", ".\\1", key)
                frame_ids[key] = frame_id

        for key in result:
            if key == key.upper():
                inst_dict = result[key]
                frame_id = frame_ids[key]

                concept = inst_dict["concept"]
                if concept is not None:
                    if not concept.startswith("@ONT."):
                        concept = "@ONT." + concept

                TMRFrame.parse(frame_id, space, frame_ids, properties=inst_dict, isa=concept, index=inst_dict["sent-word-ind"][1])

        def find_root() -> Frame:
            event = None
            for instance in space:
                try:
                    if instance ^ "@ONT.EVENT":
                        event = instance
                        break
                except: pass

            while event is not None and "PURPOSE-OF" in event:
                event = event["PURPOSE-OF"][0]

            return event

        tmr: TMR = XMR.instance(Space("INPUTS"), space, XMR.Signal.INPUT, XMR.Type.LANGUAGE, XMR.InputStatus.RECEIVED, source, find_root())
        tmr.frame["SENTENCE"] = tmr_dict["sentence"]
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
        for instance in self.graph():
            if TMRFrame(instance.id).is_event():
                event = instance
                break

        while event is not None and "PURPOSE-OF" in event:
            event = event["PURPOSE-OF"][0]

        return event

    def is_prefix(self):
        for instance in self.graph():
            if TMRFrame(instance.id).is_event():
                if [">", "FIND-ANCHOR-TIME"] in instance["TIME"]:
                    return True

        return False

    def is_postfix(self):
        for instance in self.graph():
            if TMRFrame(instance.id).is_event():
                if ["<", "FIND-ANCHOR-TIME"] in instance["TIME"]:
                    return True

        # For closing generic events, such as "Finished."
        for instance in self.graph():
            if instance.isa("@ONT.ASPECT"):
                if instance["PHASE"] == "END":
                    scopes = list(map(lambda filler: filler.parents()[0], instance["SCOPE"]))  # TODO: this needs search functionality ("is a filler in the slot exactly concept X?")
                    if "@ONT.EVENT" in scopes:
                        return True

        return False

    # TODO: Ultimately, replace with a generic querying capability
    def find_by_concept(self, concept):
        instances = list(filter(lambda instance: instance.isa(concept), self.graph()))
        return instances


class TMRFrame(Frame):

    @classmethod
    def parse(cls, name, space: Space, frame_ids: dict, properties=None, isa=None, index=None) -> 'TMRFrame':
        frame = TMRFrame(name)
        if isa is not None:
            frame.add_parent(isa)

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

            key_as_frame = Frame("@ONT." + key, declare=False)
            if key_as_frame ^ "@ONT.RELATION" or key_as_frame ^ "@ONT.ONTOLOGY-SLOT":
                value = _properties[original_key]
                if not isinstance(value, list):
                    value = [value]
                for v in value:
                    v = "@" + re.sub(r"-([0-9]+)$", ".\\1", v)
                    try:
                        parts = Identifier.parse(v)
                        if isinstance(parts[0], str) and isinstance(parts[1], str) and parts[2] is None:
                            as_tmr_frame = "@" + space.name + "." + parts[0] + "." + parts[1]
                            as_ont_frame = "@ONT." + parts[0] + "." + parts[1]
                            if as_tmr_frame in frame_ids.values():
                                v = as_tmr_frame
                            else:
                                v = as_ont_frame
                    except:
                        v = v.replace("@", "@ONT.")

                    frame[key] += Frame(v)
            else:
                frame[key] += _properties[original_key]

        frame.token_index = index

        return frame

    def _ISA_type(self):
        return "INSTANCE-OF"

    def is_event(self):
        return self.isa("@ONT.EVENT")

    def is_object(self):
        return self.isa("@ONT.OBJECT")

    def add_parent(self, parent: Union[str, Identifier, 'Frame']) -> 'TMRFrame':
        if isinstance(parent, str):
            parent = Identifier(parent)
        self.get_slot(self._ISA_type()).add_value(parent)
        return self

    def remove_parent(self, parent: Union[str, Identifier, 'Frame']) -> 'TMRFrame':
        if isinstance(parent, str):
            parent = Identifier(parent)
        self.get_slot(self._ISA_type()).remove_value(parent)
        return self

    def tmr(self) -> TMR:
        network: Network = self._graph._network
        results = network.search(Frame.q(network).f("REFERS-TO-GRAPH", Literal(self._graph._namespace)))
        if len(results) != 1:
            raise Exception("TMR wrapper node not found.")

        return TMR(results[0])


class TMRGraph(Space):

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
