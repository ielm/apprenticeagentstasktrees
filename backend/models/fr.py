from backend.models.frinstance import FRInstance
from backend.ontology import Ontology
from backend.heuristics.fr_heuristics import FRHeuristics


class FR(FRHeuristics, object):

    def __init__(self):
        self._instances = dict()
        self._indexes = dict()

    def __setitem__(self, key, value):
        self._instances[key] = value

    def __getitem__(self, key):
        return self._instances[key]

    def __iter__(self):
        return iter(self._instances)

    def __len__(self):
        return len(self._instances)

    def register(self, concept):
        fr_index = self.__next_index(concept)
        fr_name = concept + "-FR" + str(fr_index)
        fr_instance = FRInstance(fr_name, concept, fr_index)
        self._instances[fr_name] = fr_instance
        return fr_instance

    def search(self, concept=None):
        results = list(self._instances.values())

        if concept is not None:
            results = list(filter(lambda instance: instance.concept == concept, results))

        return results

    # Fills an existing FR Instance with properties found in an Instance object; the properties must be resolved
    # to existing FR Instances to be added.
    # fr_id: The id/name of an existing FR Instance (e.g., OBJECT-FR1).
    # instance: A Instance object whose properties will be merged into the FR Instance.
    # resolves: A map of TMR instance IDs (found in the Instance) to either None, {}, or a set of fr_ids.
    #           These are the FR Instance(s) that the ID is resolved to.  Multiple implies ambiguity.
    def populate(self, fr_id, instance, resolves):
        fr_instance = self[fr_id]

        for property in instance:
            # TODO: handle attributes
            # if relation:
            for value in instance[property]:
                if value in resolves and resolves[value] is not None:
                    fr_instance.remember(property, resolves[value])

    # Locates each mention of an Instance in the input Instance (including itself), and attempts to resolve those
    # instances to existing FR Instances.  It can use an existing set of resolves to assist, as well as an optional
    # input TMR (presumably containing the input Instance).  It can find no matches (None), or any number of matches
    # where more than one implies ambiguity.
    def resolve_instance(self, instance, resolves, tmr=None):
        # TODO: currently this resolves everything to None unless found in the input resolves object
        results = dict()
        results[instance.name] = None
        for property in instance:
            if property in Ontology.ontology and 'RELATION' in Ontology.ancestors(property):
                for value in instance[property]:
                    results[value] = None

        for id in results:
            if id in resolves:
                results[id] = resolves[id]

        heuristics = [
            self.resolve_human_and_robot_as_singletons,
            self.resolve_determined_objects,
            self.resolve_sets_with_identical_members,
        ]

        for heuristic in heuristics:
            if results[instance.name] is None:
                heuristic(instance, results, tmr=tmr)

        return results

    # All instances in the TMR will be resolved if possible, and then either added or updated into the FR.
    def learn_tmr(self, tmr):
        resolves = {}

        def _merge_resolves():
            for instance in tmr:
                # Resolve the instance given the current information
                iresolves = self.resolve_instance(tmr[instance], resolves, tmr=tmr)

                # Integrate the results into the current resolves (declaring ambiguities if needed)
                for id in iresolves:
                    if id not in resolves:
                        resolves[id] = iresolves[id]
                    elif iresolves[id] is not None and resolves[id] is not None:
                        resolves[id].update(iresolves[id])
                    elif iresolves[id] is not None:
                        resolves[id] = iresolves[id]

        keep_trying = True
        while keep_trying:
            current_resolves = dict(resolves)
            _merge_resolves()
            keep_trying = current_resolves != resolves

        for id in resolves:
            if resolves[id] is None and id in tmr:
                concept = tmr[id] if type(tmr[id]) == str else tmr[id].concept
                resolves[id] = {self.register(concept).name}

        for instance in tmr:
            for resolved in resolves[instance]:
                self.populate(resolved, tmr[instance], resolves)

    def __next_index(self, concept):
        if concept in self._indexes:
            index = self._indexes[concept] + 1
            self._indexes[concept] = index
            return index

        self._indexes[concept] = 1
        return 1

    def __str__(self):
        lines = ["Fact Repository"]
        for instance in self:
            lines.extend(list(map(lambda line: "  " + line, str(self[instance]).split("\n"))))
        return "\n".join(lines)