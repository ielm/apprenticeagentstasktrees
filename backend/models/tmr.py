from collections.abc import Mapping

from mini_ontology import contains
from models.instance import Instance


class TMR(Mapping):

    def __init__(self, tmr_dict):
        self.sentence = tmr_dict["sentence"]

        self._storage = dict()

        result = tmr_dict["results"][0]["TMR"]
        for key in result:
            if key == key.upper():
                self[key] = Instance(result[key], name=key)

    def __setitem__(self, key, value):
        self._storage[key] = value

    def __getitem__(self, key):
        if key == "HUMAN" or key == "ROBOT":
            return key

        return self._storage[key]

    def __iter__(self):
        return iter(self._storage)

    def __len__(self):
        return len(self._storage)

    def is_utterance(self):
        name = self.get_name()
        if str.startswith(name, "REQUEST-ACTION TAKE") \
                or str.startswith(name, "REQUEST-ACTION HOLD") \
                or str.startswith(name, "REQUEST-ACTION RESTRAIN"):
            return False
        return True

    def is_action(self):
        return not self.is_utterance()

    def get_name(self):
        event = self.find_main_event()
        if event is None:
            return ""

        output = event.concept

        node = event
        while "THEME" in node:

            output += " " + " AND ".join(list(map(lambda theme: self[theme].concept, node["THEME"])))
            output = output.strip()

            # output += " " + self[node["THEME"]]["concept"]
            # if "CARDINALITY" in self[node["THEME"]] and self[node["THEME"]]["CARDINALITY"][0] == ">":
            #     output += "S"
            # if "THEME-1" in node:
            #     output += " AND " + self[node["THEME-1"]]["concept"]

            node = self[node["THEME"][0]]

        if "INSTRUMENT" in event:
            output += " WITH " + " AND ".join(list(map(lambda instrument: self[instrument].concept, event["INSTRUMENT"])))

        return output

    def find_main_event(self):
        if self is None:
            return None

        for instance in self.values():
            if instance.is_event():
                return instance

        return None

    def is_postfix(self):
        for instance in self.values():
            if instance.is_event():
                if instance["TIME"][0] == "<":
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

        # concept1 = self[event1["THEME"]]["concept"]
        # concept2 = tmr[event2["THEME"]]["concept"]
        themes1 = list(map(lambda theme: self[theme], event1["THEME"]))
        themes2 = list(map(lambda theme: tmr[theme], event2["THEME"]))

        for theme1 in themes1:
            for theme2 in themes2:
                if contains(theme2.concept, "HAS-OBJECT-AS-PART", "SEM", theme1.concept):
                    return True
                if "CARDINALITY" in theme2 and ">" in theme2["CARDINALITY"] and theme1.concept == theme2.concept:
                    return True # one is the plural of the other

        return False

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