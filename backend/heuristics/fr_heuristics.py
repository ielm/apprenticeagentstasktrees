from backend.models.graph import Frame


class FRResolutionHeuristic(object):

    def __init__(self, fr):
        self.fr = fr

    def resolve(self, instance, resolves, tmr=None):
        raise Exception("FRResolutionHeuristic.resolve must be implemented in subclasses.")


class FRImportHeuristic(object):

    def __init__(self, fr):
        self.fr = fr

    def filter(self, import_fr, status):
        raise Exception("FRImportHeuristic.filter must be implemented in subclasses.")


# If the input instance is of type HUMAN or ROBOT, match it to the first existing FR instance of that type.
# If the resolves mentions a generic (non-instanced) HUMAN or ROBOT, do the same.
class FRResolveHumanAndRobotAsSingletonsHeuristic(FRResolutionHeuristic):

    def resolve(self, instance, resolves, tmr=None):
        if instance[instance._ISA_type()] == self.fr.ontology["HUMAN"] or instance[instance._ISA_type()] == self.fr.ontology["ROBOT"]:
            fr_instances = self.fr.search(query=Frame.q(self.fr._network).isa(instance.concept()))
            if len(fr_instances) > 0:
                resolves[instance._identifier.render(graph=False)] = {fr_instances[0].name()}

        if "HUMAN" in resolves:
            fr_instances = self.fr.search(Frame.q(self.fr._network).isa(self.fr.ontology["HUMAN"]))
            if len(fr_instances) > 0:
                resolves["HUMAN"] = {fr_instances[0].name()}

        if "ONT.HUMAN" in resolves:
            fr_instances = self.fr.search(Frame.q(self.fr._network).isa(self.fr.ontology["HUMAN"]))
            if len(fr_instances) > 0:
                resolves["ONT.HUMAN"] = {fr_instances[0].name()}

        if "ROBOT" in resolves:
            fr_instances = self.fr.search(Frame.q(self.fr._network).isa(self.fr.ontology["ROBOT"]))
            if len(fr_instances) > 0:
                resolves["ROBOT"] = {fr_instances[0].name()}

        if "ONT.ROBOT" in resolves:
            fr_instances = self.fr.search(Frame.q(self.fr._network).isa(self.fr.ontology["ROBOT"]))
            if len(fr_instances) > 0:
                resolves["ONT.ROBOT"] = {fr_instances[0].name()}


# If the input is an object, and its syntactic dependencies contain a determined article ("the"), look for the
# most recent fr instance of that type, and resolve it.  Most recent can be tracked by highest ID number.
class FRResolveDeterminedObjectsHeuristic(FRResolutionHeuristic):

    def resolve(self, instance, resolves, tmr=None):
        if not instance ^ self.fr.ontology["OBJECT"]:
            return

        if tmr is None:
            return

        dependencies = tmr.syntax.find_dependencies(types=["ART"], governors=instance.token_index)
        articles = list(map(lambda dependency: tmr.syntax.index[str(dependency[2])], dependencies))
        tokens = list(map(lambda article: article["lemma"], articles))

        if "THE" not in tokens:
            return

        fr_instances = self.fr.search(query=Frame.q(self.fr._network).isa(instance.concept()))

        if len(fr_instances) == 0:
            return

        match = max(fr_instances, key=lambda instance: instance._identifier.instance)
        resolves[instance._identifier.render(graph=False)] = {match.name()}


# If the input instance is of type SET, and there is another set in the FR with the same (exact) members,
# resolve them to each other.
class FRResolveSetsWithIdenticalMembersHeuristic(FRResolutionHeuristic):

    def resolve(self, instance, resolves, tmr=None):
        if not instance ^ self.fr.ontology["SET"]:
            return

        instance_members = instance["MEMBER-TYPE"]
        instance_members = list(map(lambda filler: filler._value, instance_members))

        # Convert any HUMAN and ROBOT mentions to their singleton FR representations
        def convert(filler):
            if filler == "HUMAN" or filler == "ONT.HUMAN":
                return self.fr._namespace + ".HUMAN.1"
            if filler == "ROBOT" or filler == "ONT.ROBOT":
                return self.fr._namespace + ".ROBOT.1"
            return filler.render()
        instance_members = list(map(lambda filler: convert(filler), instance_members))

        resolved_instance_members = set()
        for instance_member in instance_members:
            if instance_member in resolves:
                if resolves[instance_member] is not None:
                    resolved_instance_members = resolved_instance_members.union(resolves[instance_member])

        fr_instances = self.fr.search(Frame.q(self.fr._network).isa(self.fr.ontology["SET"]))
        for fr_instance in fr_instances:
            fr_instance_members = list(map(lambda filler: filler.resolve().name(), fr_instance["MEMBER-TYPE"]))
            if set(fr_instance_members) == set(instance_members):
                resolves[instance._identifier.render(graph=False)] = {fr_instance.name()}
            if set(fr_instance_members) == set(resolved_instance_members):
                resolves[instance._identifier.render(graph=False)] = {fr_instance.name()}