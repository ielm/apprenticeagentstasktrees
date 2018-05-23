

class FRHeuristics(object):

    # If the input instance is of type HUMAN or ROBOT, match it to the first existing FR instance of that type.
    # If the resolves mentions a generic (non-instanced) HUMAN or ROBOT, do the same.
    @staticmethod
    def resolve_human_and_robot_as_singletons(fr, instance, resolves, tmr=None):
        if instance.concept == "HUMAN" or instance.concept == "ROBOT":
            fr_instances = fr.search(concept=instance.concept)
            if len(fr_instances) > 0:
                resolves[instance.name] = {fr_instances[0].name}

        if "HUMAN" in resolves:
            fr_instances = fr.search(concept="HUMAN")
            if len(fr_instances) > 0:
                resolves["HUMAN"] = {fr_instances[0].name}

        if "ROBOT" in resolves:
            fr_instances = fr.search(concept="ROBOT")
            if len(fr_instances) > 0:
                resolves["ROBOT"] = {fr_instances[0].name}

    # If the input is an object, and its syntactic dependencies contain a determined article ("the"), look for the
    # most recent fr instance of that type, and resolve it.  Most recent can be tracked by highest ID number.
    @staticmethod
    def resolve_determined_objects(fr, instance, resolves, tmr=None):
        if instance.subtree != "OBJECT":
            return

        if tmr is None:
            return

        dependencies = tmr.syntax.find_dependencies(types=["ART"], governors=instance.token_index)
        articles = list(map(lambda dependency: tmr.syntax.index[str(dependency[2])], dependencies))
        tokens = list(map(lambda article: article["lemma"], articles))

        if "THE" not in tokens:
            return

        fr_instances = fr.search(concept=instance.concept)

        if len(fr_instances) == 0:
            return

        match = max(fr_instances, key=lambda instance: instance.index)
        resolves[instance.name] = {match.name}

    # If the input instance is of type SET, and there is another set in the FR with the same (exact) members,
    # resolve them to each other.
    @staticmethod
    def resolve_sets_with_identical_members(fr, instance, resolves, tmr=None):
        if instance.concept != "SET":
            return

        instance_members = instance["MEMBER-TYPE"]

        # Convert any HUMAN and ROBOT mentions to their singleton FR representations
        def convert(filler):
            if filler == "HUMAN":
                return "HUMAN-" + fr.namespace + "1"
            if filler == "ROBOT":
                return "ROBOT-" + fr.namespace + "1"
            return filler
        instance_members = map(lambda filler: convert(filler), instance_members)

        fr_instances = fr.search(concept="SET")
        for fr_instance in fr_instances:
            fr_instance_members = map(lambda filler: filler.value, fr_instance["MEMBER-TYPE"])
            if set(fr_instance_members) == set(instance_members):
                resolves[instance.name] = {fr_instance.name}