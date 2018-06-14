from backend.models.frinstance import FRInstanceX as FRInstance
from backend.models.graph import UnknownFrameError


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
        if instance["IS-A"] == "HUMAN" or instance["IS-A"] == "ROBOT":
            fr_instances = self.fr.search(concept=instance.concept)
            if len(fr_instances) > 0:
                resolves[instance.name] = {fr_instances[0].name}

        if "HUMAN" in resolves:
            fr_instances = self.fr.search(concept="HUMAN")
            if len(fr_instances) > 0:
                resolves["HUMAN"] = {fr_instances[0].name}

        if "ROBOT" in resolves:
            fr_instances = self.fr.search(concept="ROBOT")
            if len(fr_instances) > 0:
                resolves["ROBOT"] = {fr_instances[0].name}


# If the input is an object, and its syntactic dependencies contain a determined article ("the"), look for the
# most recent fr instance of that type, and resolve it.  Most recent can be tracked by highest ID number.
class FRResolveDeterminedObjectsHeuristic(FRResolutionHeuristic):

    def resolve(self, instance, resolves, tmr=None):
        if instance ^ "OBJECT":
            return

        if tmr is None:
            return

        dependencies = tmr.syntax.find_dependencies(types=["ART"], governors=instance.token_index)
        articles = list(map(lambda dependency: tmr.syntax.index[str(dependency[2])], dependencies))
        tokens = list(map(lambda article: article["lemma"], articles))

        if "THE" not in tokens:
            return

        fr_instances = self.fr.search(concept=instance.concept)

        if len(fr_instances) == 0:
            return

        match = max(fr_instances, key=lambda instance: instance.index)
        resolves[instance.name] = {match.name}


# If the input instance is of type SET, and there is another set in the FR with the same (exact) members,
# resolve them to each other.
class FRResolveSetsWithIdenticalMembersHeuristic(FRResolutionHeuristic):

    def resolve(self, instance, resolves, tmr=None):
        if instance ^ "SET":
            return

        instance_members = instance["MEMBER-TYPE"]
        instance_members = list(map(lambda filler: filler.value if type(filler) == FRInstance.FRFiller else filler, instance_members))

        # Convert any HUMAN and ROBOT mentions to their singleton FR representations
        def convert(filler):
            if filler == "HUMAN":
                return "HUMAN-" + self.fr.namespace + "1"
            if filler == "ROBOT":
                return "ROBOT-" + self.fr.namespace + "1"
            return filler
        instance_members = list(map(lambda filler: convert(filler), instance_members))

        resolved_instance_members = set()
        for instance_member in instance_members:
            if instance_member in resolves:
                if resolves[instance_member] is not None:
                    resolved_instance_members = resolved_instance_members.union(resolves[instance_member])

        fr_instances = self.fr.search(concept="SET")
        for fr_instance in fr_instances:
            fr_instance_members = list(map(lambda filler: filler.value, fr_instance["MEMBER-TYPE"]))
            if set(fr_instance_members) == set(instance_members):
                resolves[instance.name] = {fr_instance.name}
            if set(fr_instance_members) == set(resolved_instance_members):
                resolves[instance.name] = {fr_instance.name}