from backend.models.graph import Frame, Graph
from backend.ontology import Ontology
from backend.models.syntax import Syntax
# from backend.models.tmrinstance import TMRInstance
from backend.utils.YaleUtils import tmr_action_name

from functools import reduce
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

    def __init__(self, tmr_dict, ontology, namespace=None):
        if ontology is None:
            raise Exception("TMRs must have an anchoring ontology provided.")
        if namespace is None:
            namespace = "TMR#" + str(uuid4())

        super().__init__(namespace)

        self.ontology = ontology
        self.sentence = tmr_dict["sentence"]
        self.syntax = Syntax(tmr_dict["syntax"][0])

        result = tmr_dict["tmr"][0]["results"][0]["TMR"]
        for key in result:
            if key == key.upper():
                inst_dict = result[key]
                # subtree = inst_dict["is-in-subtree"] if "is-in-subtree" in inst_dict else None

                # self[key] = TMRInstance(properties=inst_dict, name=key, concept=inst_dict["concept"], subtree=subtree, index=inst_dict["sent-word-ind"][1])
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

    @DeprecationWarning
    def is_action(self):
        event = self.find_main_event()
        if event is None:
            return False

        # 1) Is the event a REQUEST-ACTION, where the AGENT = HUMAN, and the BENEFICIARY = ROBOT
        if event ^ self.ontology + ".REQUEST-ACTION" \
                and event["AGENT"] ^ self.ontology + ".HUMAN" \
                and event["BENEFICIARY"] ^ self.ontology + ".ROBOT":
            return True

        # if event.concept == "REQUEST-ACTION":
        #     if "AGENT" in event \
        #             and "BENEFICIARY" in event \
        #             and "HUMAN" in event["AGENT"] \
        #             and "ROBOT" in event["BENEFICIARY"]:
        #         return True

        # 2) Is the event a PHYSICAL-EVENT, where the AGENT = HUMAN, and the TIME is present-tense
        if event ^ self.ontology + ".PHYSICAL-EVENT" \
                and event["AGENT"] ^ self.ontology + ".HUMAN" \
                and event["TIME"] == ["FIND-ANCHOR-TIME"]:
            return True

        # if event.concept == "PHYSICAL-EVENT" or "PHYSICAL-EVENT" in Ontology.ancestors(event.concept):
        #     if "HUMAN" in list(map(lambda agent: agent if type(self[agent]) == str else self[agent].concept, event["AGENT"])):
        #         if event["TIME"] == ["FIND-ANCHOR-TIME"]:
        #             return True

        return False

    @DeprecationWarning
    def is_utterance(self):
        return not self.is_action()

    # def get_name(self):
    #     event = self.find_main_event()
    #     if event is None:
    #         return ""
    #
    #     if self.is_action():
    #         return tmr_action_name(self)
    #
    #     output = event.concept
    #
    #     def _name_theme(instance):
    #         name = instance.concept
    #         if ">" in instance["CARDINALITY"]:
    #             name += "s"
    #         if "SPATIAL-ORIENTATION" in instance:
    #             name = " ".join(instance["SPATIAL-ORIENTATION"]) + " " + name
    #         if "SIDE-TB" in instance:
    #             name = " ".join(instance["SIDE-TB"]) + " " + name
    #         return name
    #
    #     node = event
    #     while "THEME" in node:
    #
    #         # output += " " + " AND ".join(list(map(lambda theme: self[theme].concept, node["THEME"])))
    #         output += " " + " AND ".join(list(map(lambda theme: _name_theme(self[theme]), node["THEME"])))
    #         output = output.strip()
    #
    #         # output += " " + self[node["THEME"]]["concept"]
    #         # if "CARDINALITY" in self[node["THEME"]] and self[node["THEME"]]["CARDINALITY"][0] == ">":
    #         #     output += "S"
    #         # if "THEME-1" in node:
    #         #     output += " AND " + self[node["THEME-1"]]["concept"]
    #
    #         node = self[node["THEME"][0]]
    #
    #     if "INSTRUMENT" in event:
    #         output += " WITH " + " AND ".join(list(map(lambda instrument: self[instrument].concept, event["INSTRUMENT"])))
    #
    #     if "DESTINATION" in event:
    #         output += " TO " + " AND ".join(list(map(lambda destination: self[destination].concept, event["DESTINATION"])))
    #
    #     return output

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
                # if instance["TIME"].compare([">", "FIND-ANCHOR-TIME"], intersection=False):
                #     return True
                # if "TIME" in instance and instance["TIME"][0] == ">":
                #     return True

        return False

    def is_postfix(self):
        for instance in self.values():
            if instance.is_event():
                if instance["TIME"] == "<" and instance["TIME"] == "FIND-ANCHOR-TIME":
                    return True
                # if "TIME" in instance and instance["TIME"][0] == "<":
                #     return True

        # For closing generic events, such as "Finished."
        for instance in self.values():
            if instance.isa(self.ontology + ".ASPECT"):
                if instance["PHASE"] == "END" and instance["SCOPE"] ^ self.ontology + ".EVENT":
                    return True

        # for instance in self.values():
            # if instance.concept == "ASPECT":
            #     if "END" in instance["PHASE"]:
            #         if "EVENT" in instance["SCOPE"]:
            #             return True

        return False

    @DeprecationWarning
    def has_same_main_event(self, tmr):
        if tmr is None:
            return False

        event1 = self.find_main_event()
        event2 = tmr.find_main_event()

        if event1 is None or event2 is None:
            return False

        if event1["IS-A"] != event2["IS-A"]:
            return False

        caseroles = ["AGENT", "THEME", "INSTRUMENT"]
        for caserole in caseroles:
            if caserole in event1 and caserole in event2:
                # This tests to see if the present frames in the case role of each of the input EVENTs share an
                # exact same immediate ancestor (not full hierarchy search).
                # Ex: [HUMAN/EVENT]-1 == HUMAN-2; HUMAN-1 != ANIMAL-1

                fillers1 = list(map(lambda filler: filler.resolve(), event1[caserole]))
                fillers2 = list(map(lambda filler: filler.resolve(), event2[caserole]))

                concepts1 = list(map(lambda filler: filler["IS-A"], fillers1))
                concepts2 = list(map(lambda filler: filler["IS-A"], fillers2))

                concepts1 = list(reduce(lambda x, y: x + y, concepts1))
                concepts2 = list(reduce(lambda x, y: x + y, concepts2))

                concepts1 = set(map(lambda concept: concept._value, concepts1))
                concepts2 = set(map(lambda concept: concept._value, concepts2))

                if len(concepts1 & concepts2) == 0:
                    return False

        # if "AGENT" in event1 and "AGENT" in event2:
        #     if event1["AGENT"] ^ event2["AGENT"]:
        #         return True

        return True

        # if event1.concept != event2.concept:
        #     return False
        #
        # if "AGENT" in event1 \
        #         and "AGENT" in event2 \
        #         and len(set(event1["AGENT"]) - self.keys()) > 0 \
        #         and len(set(event2["AGENT"]) - tmr.keys()) > 0 \
        #         and len(self.get_concepts(event1["AGENT"]) & tmr.get_concepts(event2["AGENT"])) == 0:
        #     return False
        #
        # if ("THEME" in event1) != ("THEME" in event2):
        #     return False
        #
        # if "THEME" in event1 \
        #         and "THEME" in event2 \
        #         and len(self.get_concepts(event1["THEME"]) & tmr.get_concepts(event2["THEME"])) == 0:
        #     return False
        #
        # if "INSTRUMENT" in event1 \
        #         and "INSTRUMENT" in event2 \
        #         and len(self.get_concepts(event1["INSTRUMENT"]) & tmr.get_concepts(event2["INSTRUMENT"])) == 0:
        #     return False
        #
        # return True

    @DeprecationWarning
    # Ultimately, this could be replaced by a generic recursive querying capability
    def find_themes(self):
        event = self.find_main_event()
        if event is None:
            return []

        def __find_themes(instance):
            themes = []

            for theme in instance["THEME"]:
                theme = theme.resolve()
                themes.append(theme)
                themes.extend(__find_themes(theme))

            # if "THEME" in instance:
            #     for theme in instance["THEME"]:
            #         theme_instance = self[theme]
            #         themes.append(theme_instance)
            #         themes.extend(__find_themes(theme_instance))

            return themes

        themes = list(map(lambda theme: list(theme["IS-A"]._storage), __find_themes(event)))
        if len(themes) == 0:
            return themes

        themes = list(reduce(lambda x, y: x + y, themes))
        themes = set(map(lambda filler: filler._value, themes))

        return themes
        # return list(map(lambda theme: theme.concept, __find_themes(event)))

    # def about_part_of(self, tmr):
    #     if self is None or tmr is None:
    #         return False
    #
    #     event1 = self.find_main_event()
    #     event2 = tmr.find_main_event()
    #
    #     if event1 is None or event2 is None:
    #         return False
    #
    #     if not ("THEME" in event1 and "THEME" in event2):
    #         return False
    #
    #     themes1 = list(map(lambda theme: self[theme], event1["THEME"]))
    #     themes2 = list(map(lambda theme: tmr[theme], event2["THEME"]))
    #
    #     for theme1 in themes1:
    #         for theme2 in themes2:
    #             if Ontology.contains(theme2.concept, "HAS-OBJECT-AS-PART", "SEM", theme1.concept):
    #                 return True
    #             if "CARDINALITY" in theme2 and ">" in theme2["CARDINALITY"] and theme1.concept == theme2.concept:
    #                 return True # one is the plural of the other
    #
    #     return False

    # Here we verify that the event subtypes are broadly the same; concerning only with the immediate children
    # of EVENT in the ontology.
    # Every EVENT subtype in this TMR must also be present in the input TMR = if they are not the same (even a
    # subset), then we must consider these two events distinctly different enough that even a correlation in
    # HAS-OBJECT-AS-PART is not sufficient.
    # def about_same_events(self, tmr):
    #     if self is None or tmr is None:
    #         return False
    #
    #     event1 = self.find_main_event()
    #     event2 = tmr.find_main_event()
    #
    #     if event1 is None or event2 is None:
    #         return False
    #
    #     event_types = Ontology.ontology["EVENT"]["SUBCLASSES"]["VALUE"]
    #     event1_types = set(Ontology.ancestors(event1.concept, include_self=True)).intersection(set(event_types))
    #     event2_types = set(Ontology.ancestors(event2.concept, include_self=True)).intersection(set(event_types))
    #
    #     return len(event1_types.intersection(event2_types)) == len(event1_types)

    # NOTE: Ultimately, replace with a generic querying capability
    def find_by_concept(self, concept):
        instances = list(filter(lambda instance: instance.isa(concept), self.values()))
        return instances
        # return list(filter(lambda instance: instance.concept == concept, self.values()))

    # def find_objects(self):
    #     objects = []
    #
    #     for instance in self.values():
    #         if instance.is_object():
    #             objects.append(instance.concept)
    #
    #     return objects

    # Is TMR(1) about any of the THEMEs of any of the Actions(2).
    # "About" in this case will check THEME, INSTRUMENT and DESTINATION.
    # def is_about(self, actions):
    #     about = []
    #     event = self.find_main_event()
    #
    #     if "THEME" in event:
    #         about.extend(self.get_concepts(event["THEME"]))
    #     if "INSTRUMENT" in event:
    #         about.extend(self.get_concepts(event["INSTRUMENT"]))
    #     if "DESTINATION" in event:
    #         about.extend(self.get_concepts(event["DESTINATION"]))
    #
    #     themes = []
    #     for action in actions:
    #         themes.extend(action.find_themes())
    #
    #     return len(set(about).intersection(set(themes))) > 0

    # def get_concepts(self, instance_keys):
    #     return set(map(lambda instance: self[instance].concept, instance_keys))


class TMRInstance(Frame):

    def __init__(self, name, properties=None, isa=None, index=None):
        super().__init__(name, isa=isa)

        # self.concept = concept
        # self.name = name if name is not None else self.concept + "-X"
        # self.subtree = subtree

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

        # super().__init__(name, concept, uuid=uuid, properties=_properties, subtree=subtree)
        # super().__init__(name, isa=concept)

        self.token_index = index

    def is_event(self):
        return self.isa(self._graph.ontology + ".EVENT")

    def is_object(self):
        return self.isa(self._graph.ontology + ".OBJECT")