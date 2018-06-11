from backend.models.frinstance import FRInstance


def comparator(fr, instance1, instance2, slot, compare_concepts=False, match_full=False):
    fillers1 = list(map(lambda filler: filler.value, instance1[slot]))
    fillers2 = list(map(lambda filler: filler.value, instance2[slot]))

    if compare_concepts:
        fillers1 = list(map(lambda filler: fr[filler].concept, fillers1))
        fillers2 = list(map(lambda filler: fr[filler].concept, fillers2))

    if match_full:
        return set(fillers1) == set(fillers2)
    else:
        return len(set(fillers1).intersection(set(fillers2))) > 0


def format_pretty_htn(fr, fr_instance, lines=None, indent=0):
    lines = lines if lines is not None else []

    indent_buffer = "   ".join(["" for i in range(0, indent + 1)])

    line = indent_buffer + format_pretty_name(fr, fr_instance)
    lines.append(line)

    for precondition in fr_instance["PRECONDITION"]:
        precondition = fr[precondition.value]
        lines.append(indent_buffer + indent_buffer + "*PRECONDITION " + format_pretty_name(fr, precondition))

    for subevent in fr_instance["HAS-EVENT-AS-PART"]:
        subevent = fr[subevent.value]
        format_pretty_htn(fr, subevent, lines=lines, indent=indent + 1)

    return "\n".join(lines)


def format_pretty_name(fr, fr_instance):
    name = fr_instance.concept

    if fr_instance.subtree == "EVENT":

        agents = " and ".join(map(lambda agent: agent.concept, expand_sets(fr, fr_instance["AGENT"])))
        themes = " and ".join(map(lambda theme: theme.concept, expand_sets(fr, fr_instance["THEME"])))

        name += " " + themes + " (" + agents + ")"

        name = ("+" if "*LCT.current" in fr_instance.context() and fr_instance.context()["*LCT.current"] else "") + name

    return name


def expand_sets(fr, fr_instances):
    results = []
    for fr_instance in fr_instances:
        if type(fr_instance) == str:
            fr_instance = fr[fr_instance]
        if type(fr_instance) == FRInstance.FRFiller:
            fr_instance = fr[fr_instance.value]

        if fr_instance.concept != "SET":
            results.append(fr_instance)
        else:
            results.extend(map(lambda member: fr[member.value], fr_instance["MEMBER-TYPE"]))

    return results