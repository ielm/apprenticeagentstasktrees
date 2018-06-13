from backend.models.graph import Filler, Frame, Graph
from backend.heuristics.fr_heuristics import *
from backend.utils.AgentLogger import AgentLogger

import copy


class FR(Graph):

    def __init__(self, namespace, ontology):
        super().__init__(namespace)

        self.ontology = ontology

        self._logger = AgentLogger()
        self._indexes = dict()

        self.heuristics = [
            FRResolveHumanAndRobotAsSingletonsHeuristic,
            FRResolveDeterminedObjectsHeuristic,
            FRResolveSetsWithIdenticalMembersHeuristic
        ]

    def __setitem__(self, key, value):
        if not isinstance(value, FRInstance):
            raise TypeError("FR elements must be FRInstance objects.")
        super().__setitem__(key, value)

    def logger(self, logger=None):
        if not logger is None:
            self._logger = logger
        return self._logger

    def clear(self):
        super().clear()
        self._indexes = dict()

    def register(self, id, isa=None, generate_index=True):
        if generate_index:
            id = id + "." + str(self.__next_index(id))
        return super().register(id, isa=isa)

    def _frame_type(self):
        return FRInstance

    def search(self, concept=None, subtree=None, attributed_tmr_instance=None, context=None, has_fillers=None):
        results = list(self.values())

        if concept is not None:
            results = list(filter(lambda instance: instance.concept == concept, results))

        if subtree is not None:
            results = list(filter(lambda instance: instance.subtree == subtree, results))

        if attributed_tmr_instance is not None:
            results = list(filter(lambda instance: instance.is_attributed_to(attributed_tmr_instance), results))

        if context is not None:
            results = list(filter(lambda instance: instance.does_match_context(context), results))

        if has_fillers is not None:
            sets = dict((s.name, s) for s in self.search(concept="SET"))
            results = list(filter(lambda instance: instance.has_fillers(has_fillers, expand_sets=sets), results))

        return results

    # Fills an existing FR Instance with properties found in a Frame object; the properties must be resolved
    # to existing FR Instances to be added.
    # fr_id: The id/name of an existing FR Instance (e.g., OBJECT-FR1).
    # instance: A Instance object whose properties will be merged into the FR Instance.
    # resolves: A map of TMR instance IDs (found in the Instance) to either None, {}, or a set of fr_ids.
    #           These are the FR Instance(s) that the ID is resolved to.  Multiple implies ambiguity.
    def populate(self, fr_id, frame, resolves):
        fr_instance = self[fr_id]
        fr_instance.attribute_to(frame)

        for slot in frame:
            for filler in frame[slot]:
                value = filler.resolve()
                if isinstance(value, Frame):
                    value = value.name()
                if value in resolves and resolves[value] is not None:
                    value = resolves[value]
                    if isinstance(value, str):
                        fr_instance[slot] += value
                    elif isinstance(value, set):
                        ambiguous_fillers = []
                        for v in value:
                            filler = Filler(v)
                            fr_instance[slot] += filler
                            ambiguous_fillers.append(filler)
                        ids = set(map(lambda filler: filler._uuid, ambiguous_fillers))
                        for filler in ambiguous_fillers: filler._metadata = {"ambiguities": ids}

    def _resolve_log_wrapper(self, heuristic, instance, results, tmr=None):
        input_results = copy.deepcopy(results)
        heuristic(self).resolve(instance, results, tmr=tmr)

        if input_results != results:
            pruned = {k: v for k, v in results.items() if v is not None}
            self._logger.log("FR." + heuristic.__name__ + " -> " + str(pruned))

    # Take an input FR, a series of import heuristics, and an overriding series of resolution heuristics, and populates
    # this FR with all of the elements of the input FR.
    # 1) Import heuristics are of the form heuristic(other_fr, {id: Boolean}); they modify the second parameter to
    #    either include or exclude each instance in the input from being imported (if xyz-1 == False, it will not
    #    be imported).
    # 2) Resolve heuristics are the normal FR resolution heuristics; if none are provided, then no resolution occurs.
    #    That is, the normal heuristics in this FR are ignored during this operation - either none are used, or an
    #    overriding list must be provided.
    def import_fr(self, other_fr, import_heuristics=None, resolve_heuristics=None, update_context=None):
        if import_heuristics is None:
            import_heuristics = []
        if resolve_heuristics is None:
            resolve_heuristics = []
        if update_context is None:
            update_context = {}

        status = {k: True for k in other_fr.keys()}
        for heuristic in import_heuristics:
            heuristic(self).filter(other_fr, status)

        backup_heuristics = self.heuristics
        self.heuristics = resolve_heuristics

        filtered_graph = {k: other_fr[k] for k in filter(lambda k: status[k], other_fr.keys())}
        resolves = self.resolve_tmr(filtered_graph)
        self.heuristics = backup_heuristics

        for k in filtered_graph:
            if resolves[k] is None:
                resolves[k] = self.register(other_fr[k].concept()).name()

        for k in filtered_graph:
            resolved = resolves[k]
            if type(resolved) == set:
                if len(resolved) > 1:
                    raise Exception()
                else:
                    resolved = list(resolved)[0]
            self.populate(resolved, other_fr[k], resolves=resolves)

            # Merge contexts (needlessly complicated due to list types needing to be merged)
            context = copy.deepcopy(other_fr[k].context())
            for k in update_context:
                if k not in context:
                    context[k] = update_context[k]
                    continue

                if type(context[k]) == list and type(update_context[k]) != list:
                    update_context[k] = [update_context[k]]
                if type(context[k]) != list and type(update_context[k]) == list:
                    context[k] = [context[k]]
                if type(context[k]) == list:
                    context[k].extend(update_context[k])
                else:
                    context[k] = update_context[k]
            for k in context:
                self[resolved].context()[k] = context[k]

        return resolves

    # Locates each mention of an Instance in the input Frame (including itself), and attempts to resolve those
    # instances to existing FR Instances.  It can use an existing set of resolves to assist, as well as an optional
    # input TMR (presumably containing the input Instance).  It can find no matches (None), or any number of matches
    # where more than one implies ambiguity.
    def resolve_instance(self, frame, resolves, tmr=None):
        # TODO: currently this resolves everything to None unless found in the input resolves object
        results = dict()
        results[frame.name()] = None
        for slot in frame:
            if slot == "IS-A":
                continue

            try:
                pframe = self._network.lookup(slot, graph=self.ontology)
                if pframe is not None and pframe.isa(self.ontology + ".RELATION"):
                    for filler in frame[slot]:
                        results[filler._value] = None
            except Exception: pass

        for id in results:
            if id in resolves:
                results[id] = resolves[id]

        for heuristic in self.heuristics:
            if results[frame.name()] is None:
                self._resolve_log_wrapper(heuristic, frame, results, tmr=tmr)

        return results

    def resolve_tmr(self, tmr):
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

        return resolves

    # All instances in the TMR will be resolved if possible, and then either added or updated into the FR.
    def learn_tmr(self, tmr):
        resolves = self.resolve_tmr(tmr)

        for id in resolves:
            if resolves[id] is None and id in tmr:
                concept = tmr[id] if type(tmr[id]) == str else tmr[id].concept(full_path=False)
                resolves[id] = {self.register(concept, generate_index=True).name()}

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
        lines = [self._namespace]
        for instance in sorted(self):
            lines.extend(list(map(lambda line: "  " + line, str(self[instance]).split("\n"))))
        return "\n".join(lines)


class FRInstance(Frame):

    def __init__(self, name, isa=None):
        super().__init__(name, isa=isa)
        self._from = dict()
        self._context = dict()

    def context(self):
        return self._context

    def attribute_to(self, tmrinstance):
        self._from[tmrinstance._uuid] = tmrinstance