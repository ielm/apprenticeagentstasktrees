from backend.models.graph import Graph
from backend.ontology import Ontology
from backend.models.syntax import Syntax
from backend.models.tmrinstance import TMRInstance
from backend.utils.YaleUtils import tmr_action_name


class TMR(Graph):

    def __init__(self, tmr_dict):
        super().__init__()

        self.sentence = tmr_dict["sentence"]
        self.syntax = Syntax(tmr_dict["syntax"][0])

        result = tmr_dict["tmr"][0]["results"][0]["TMR"]
        for key in result:
            if key == key.upper():
                self[key] = TMRInstance(result[key], name=key)

    def __getitem__(self, key):
        if key == "HUMAN" or key == "ROBOT":
            return key

        return super().__getitem__(key)

    def is_action(self):
        event = self.find_main_event()
        if event is None:
            return False

        # 1) Is the event a REQUEST-ACTION, where the AGENT = HUMAN, and the BENEFICIARY = ROBOT
        if event.concept == "REQUEST-ACTION":
            if "AGENT" in event \
                    and "BENEFICIARY" in event \
                    and "HUMAN" in event["AGENT"] \
                    and "ROBOT" in event["BENEFICIARY"]:
                return True

        # 2) Is the event a PHYSICAL-EVENT, where the AGENT = HUMAN, and the TIME is present-tense
        if event.concept == "PHYSICAL-EVENT" or "PHYSICAL-EVENT" in Ontology.ancestors(event.concept):
            if "HUMAN" in list(map(lambda agent: agent if type(self[agent]) == str else self[agent].concept, event["AGENT"])):
                if event["TIME"] == ["FIND-ANCHOR-TIME"]:
                    return True

        return False

    # TODO: rename - we are really testing if this is an HTN composition
    def is_utterance(self):
        return not self.is_action()

    def get_name(self):
        event = self.find_main_event()
        if event is None:
            return ""

        if self.is_action():
            return tmr_action_name(self)

        output = event.concept

        def _name_theme(instance):
            name = instance.concept
            if ">" in instance["CARDINALITY"]:
                name += "s"
            if "SPATIAL-ORIENTATION" in instance:
                name = " ".join(instance["SPATIAL-ORIENTATION"]) + " " + name
            if "SIDE-TB" in instance:
                name = " ".join(instance["SIDE-TB"]) + " " + name
            return name

        node = event
        while "THEME" in node:

            # output += " " + " AND ".join(list(map(lambda theme: self[theme].concept, node["THEME"])))
            output += " " + " AND ".join(list(map(lambda theme: _name_theme(self[theme]), node["THEME"])))
            output = output.strip()

            # output += " " + self[node["THEME"]]["concept"]
            # if "CARDINALITY" in self[node["THEME"]] and self[node["THEME"]]["CARDINALITY"][0] == ">":
            #     output += "S"
            # if "THEME-1" in node:
            #     output += " AND " + self[node["THEME-1"]]["concept"]

            node = self[node["THEME"][0]]

        if "INSTRUMENT" in event:
            output += " WITH " + " AND ".join(list(map(lambda instrument: self[instrument].concept, event["INSTRUMENT"])))

        if "DESTINATION" in event:
            output += " TO " + " AND ".join(list(map(lambda destination: self[destination].concept, event["DESTINATION"])))

        return output

    def find_main_event(self):
        if self is None:
            return None

        event = None
        for instance in self.values():
            if instance.is_event():
                event = instance
                break

        while event is not None and "PURPOSE-OF" in event:
            event = self[event["PURPOSE-OF"][0]]

        return event

    def is_prefix(self):
        return not self.is_postfix()

    def is_postfix(self):
        for instance in self.values():
            if instance.is_event():
                if "TIME" in instance and instance["TIME"][0] == "<":
                    return True

        # For closing generic events, such as "Finished."
        for instance in self.values():
            if instance.concept == "ASPECT":
                if "END" in instance["PHASE"]:
                    if "EVENT" in instance["SCOPE"]:
                        return True

        return False

    def has_same_main_event(self, tmr):
        if tmr is None:
            return False

        event1 = self.find_main_event()
        event2 = tmr.find_main_event()

        if event1.concept != event2.concept:
            return False

        if "AGENT" in event1 \
                and "AGENT" in event2 \
                and len(set(event1["AGENT"]) - self.keys()) > 0 \
                and len(set(event2["AGENT"]) - tmr.keys()) > 0 \
                and len(self.get_concepts(event1["AGENT"]) & tmr.get_concepts(event2["AGENT"])) == 0:
            return False

        if ("THEME" in event1) != ("THEME" in event2):
            return False

        if "THEME" in event1 \
                and "THEME" in event2 \
                and len(self.get_concepts(event1["THEME"]) & tmr.get_concepts(event2["THEME"])) == 0:
            return False

        if "INSTRUMENT" in event1 \
                and "INSTRUMENT" in event2 \
                and len(self.get_concepts(event1["INSTRUMENT"]) & tmr.get_concepts(event2["INSTRUMENT"])) == 0:
            return False

        return True

    def find_themes(self):
        event = self.find_main_event()
        if event is None:
            return []

        def __find_themes(instance):
            themes = []

            if "THEME" in instance:
                for theme in instance["THEME"]:
                    theme_instance = self[theme]
                    themes.append(theme_instance)
                    themes.extend(__find_themes(theme_instance))

            return themes

        return list(map(lambda theme: theme.concept, __find_themes(event)))

    def about_part_of(self, tmr):
        if self is None or tmr is None:
            return False

        event1 = self.find_main_event()
        event2 = tmr.find_main_event()

        if event1 is None or event2 is None:
            return False

        if not ("THEME" in event1 and "THEME" in event2):
            return False

        themes1 = list(map(lambda theme: self[theme], event1["THEME"]))
        themes2 = list(map(lambda theme: tmr[theme], event2["THEME"]))

        for theme1 in themes1:
            for theme2 in themes2:
                if Ontology.contains(theme2.concept, "HAS-OBJECT-AS-PART", "SEM", theme1.concept):
                    return True
                if "CARDINALITY" in theme2 and ">" in theme2["CARDINALITY"] and theme1.concept == theme2.concept:
                    return True # one is the plural of the other

        return False

    # Here we verify that the event subtypes are broadly the same; concerning only with the immediate children
    # of EVENT in the ontology.
    # Every EVENT subtype in this TMR must also be present in the input TMR = if they are not the same (even a
    # subset), then we must consider these two events distinctly different enough that even a correlation in
    # HAS-OBJECT-AS-PART is not sufficient.
    def about_same_events(self, tmr):
        if self is None or tmr is None:
            return False

        event1 = self.find_main_event()
        event2 = tmr.find_main_event()

        if event1 is None or event2 is None:
            return False

        event_types = Ontology.ontology["EVENT"]["SUBCLASSES"]["VALUE"]
        event1_types = set(Ontology.ancestors(event1.concept, include_self=True)).intersection(set(event_types))
        event2_types = set(Ontology.ancestors(event2.concept, include_self=True)).intersection(set(event_types))

        return len(event1_types.intersection(event2_types)) == len(event1_types)

    def find_by_concept(self, concept):
        return list(filter(lambda instance: instance.concept == concept, self.values()))

    def find_objects(self):
        objects = []

        for instance in self.values():
            if instance.is_object():
                objects.append(instance.concept)

        return objects

    # Is TMR(1) about any of the THEMEs of any of the Actions(2).
    # "About" in this case will check THEME, INSTRUMENT and DESTINATION.
    def is_about(self, actions):
        about = []
        event = self.find_main_event()

        if "THEME" in event:
            about.extend(self.get_concepts(event["THEME"]))
        if "INSTRUMENT" in event:
            about.extend(self.get_concepts(event["INSTRUMENT"]))
        if "DESTINATION" in event:
            about.extend(self.get_concepts(event["DESTINATION"]))

        themes = []
        for action in actions:
            themes.extend(action.find_themes())

        return len(set(about).intersection(set(themes))) > 0

    def get_concepts(self, instance_keys):
        return set(map(lambda instance: self[instance].concept, instance_keys))