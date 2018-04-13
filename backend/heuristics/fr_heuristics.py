

class FRHeuristics(object):

    # If the input instance is of type HUMAN or ROBOT, match it to the first existing FR instance of that type.
    # If the resolves mentions a generic (non-instanced) HUMAN or ROBOT, do the same.
    def resolve_human_and_robot_as_singletons(self, instance, resolves, tmr=None):
        if instance.concept == "HUMAN" or instance.concept == "ROBOT":
            fr_instances = self.search(concept=instance.concept)
            if len(fr_instances) > 0:
                resolves[instance.name] = {fr_instances[0].name}

        if "HUMAN" in resolves:
            fr_instances = self.search(concept="HUMAN")
            if len(fr_instances) > 0:
                resolves["HUMAN"] = {fr_instances[0].name}

        if "ROBOT" in resolves:
            fr_instances = self.search(concept="ROBOT")
            if len(fr_instances) > 0:
                resolves["ROBOT"] = {fr_instances[0].name}
