from backend.models.graph import Filler, Frame, Graph, Identifier, Literal
from backend.models.query import FrameQuery
from backend.heuristics.fr_heuristics import *
from backend.utils.AgentLogger import AgentLogger

import copy


class FR(Graph):

    def __init__(self, namespace, ontology):
        super().__init__(namespace)

        self.ontology = ontology

        self._logger = AgentLogger()

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
        return super().register(id, isa=isa, generate_index=generate_index)

    def _frame_type(self):
        return FRInstance

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
                if isinstance(filler._value, Literal):
                    fr_instance[slot] += Literal(filler._value)
                    continue

                identifier = filler._value

                if isinstance(identifier, Frame):
                    identifier = identifier._identifier
                if isinstance(identifier, str):
                    identifier = Identifier.parse(identifier)

                value = None
                for key in resolves:
                    if Identifier.parse(key) == identifier:
                        value = resolves[key]

                if value is None:
                    continue

                if slot == "MEMBER-TYPE":
                    slot = "ELEMENTS"

                if isinstance(value, str):
                    fr_instance[slot] += value
                elif isinstance(value, set):
                    ambiguous_fillers = []
                    for v in value:
                        filler = Filler(v)
                        fr_instance[slot] += filler
                        ambiguous_fillers.append(filler)
                    ids = set(map(lambda filler: filler._uuid, ambiguous_fillers))
                    for f in ambiguous_fillers: f._metadata = {"ambiguities": ids}

    def _resolve_log_wrapper(self, heuristic, instance, results, tmr: TMR=None):
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
    def import_fr(self, other_fr, import_heuristics=None, resolve_heuristics=None):
        if import_heuristics is None:
            import_heuristics = []
        if resolve_heuristics is None:
            resolve_heuristics = []

        status = {k: True for k in other_fr.keys()}
        for heuristic in import_heuristics:
            heuristic(self).filter(other_fr, status)

        backup_heuristics = self.heuristics
        self.heuristics = resolve_heuristics

        filtered_graph = {k: other_fr[k] for k in filter(lambda k: status[k], other_fr.keys())}
        filtered_graph = {Identifier.parse(k).render(): filtered_graph[k] for k in filtered_graph}

        class FilteredTMR(object):
            def __init__(self, filtered_graph: dict):
                self.filtered_graph = filtered_graph

            def graph(self, network):
                return self.filtered_graph

        resolves = self.resolve_tmr(FilteredTMR(filtered_graph))
        self.heuristics = backup_heuristics

        for k in filtered_graph:
            if resolves[k] is None:
                resolves[k] = self.register(other_fr[k].concept(full_path=False), isa=other_fr[k].concept()).name()

        for k in filtered_graph:
            resolved = resolves[k]
            if type(resolved) == set:
                if len(resolved) > 1:
                    raise Exception()
                else:
                    resolved = list(resolved)[0]
            self.populate(resolved, other_fr[k], resolves=resolves)

        return resolves

    # Locates each mention of an Instance in the input Frame (including itself), and attempts to resolve those
    # instances to existing FR Instances.  It can use an existing set of resolves to assist, as well as an optional
    # input TMR (presumably containing the input Instance).  It can find no matches (None), or any number of matches
    # where more than one implies ambiguity.
    def resolve_instance(self, frame, resolves, tmr: TMR=None):
        # TODO: currently this resolves everything to None unless found in the input resolves object
        results = dict()
        results[frame._identifier.render()] = None
        for slot in frame:
            if slot == frame._ISA_type():
                continue

            try:
                pframe = self._network.lookup(slot, graph=self.ontology)
                if pframe is not None and pframe.isa(self.ontology["RELATION"]):
                    for filler in frame[slot]:
                        results[filler._value.render()] = None
            except Exception: pass

        for id in results:
            if id in resolves:
                results[id] = resolves[id]

        for heuristic in self.heuristics:
            if results[frame._identifier.render()] is None:
                self._resolve_log_wrapper(heuristic, frame, results, tmr=tmr)

        return results

    def resolve_tmr(self, tmr_frame: TMR):
        tmr = tmr_frame.graph(self._network)

        resolves = {}

        def _merge_resolves():
            for instance in tmr:
                # Resolve the instance given the current information
                iresolves = self.resolve_instance(tmr[instance], resolves, tmr=tmr_frame)

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
    def learn_tmr(self, tmr_frame: TMR):
        tmr = tmr_frame.graph(self._network)

        resolves = self.resolve_tmr(tmr_frame)

        for id in resolves:
            if resolves[id] is None and id in tmr:
                concept = tmr[id] if type(tmr[id]) == str else tmr[id].concept(full_path=False)
                resolves[id] = {self.register(concept, isa=self.ontology[concept], generate_index=True).name()}
            elif resolves[id] is None and id in self.ontology: # Make singletons
                resolves[id] = {self.register(self.ontology[id]._identifier.name, isa=self.ontology[id], generate_index=True).name()}

        for instance in tmr:
            for resolved in resolves[tmr[instance]._identifier.render()]:
                self.populate(resolved, tmr[instance], resolves)

    def __str__(self):
        lines = [self._namespace]
        for instance in sorted(self):
            lines.extend(list(map(lambda line: "  " + line, str(self[instance]).split("\n"))))
        return "\n".join(lines)


class FRInstance(Frame):

    ATTRIBUTED_TO = "*FR.attributed_to"

    def __init__(self, name, isa=None):
        super().__init__(name, isa=isa)

    def _ISA_type(self):
        return "INSTANCE-OF"

    def attribute_to(self, tmrinstance):
        self[FRInstance.ATTRIBUTED_TO] += tmrinstance

    def is_attributed_to(self, tmrinstance):
        return tmrinstance in self[FRInstance.ATTRIBUTED_TO]

    def lemmas(self):
        lemmas = []
        if len(self[FRInstance.ATTRIBUTED_TO]) == 0:
            return list(map(lambda p: p.name, self.parents()))

        for tmr_instance in self[FRInstance.ATTRIBUTED_TO]:
            tmr_instance = tmr_instance.resolve()
            tmr: TMR = tmr_instance.tmr()
            lemma = " ".join(map(lambda ti: tmr.syntax().index[str(ti)]["lemma"], tmr_instance.token_index))
            lemmas.append(lemma)
        return lemmas