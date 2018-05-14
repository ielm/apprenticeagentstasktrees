import json
import requests

from backend.config import ontosem_service


def format_treenode_yale(treenode):

    # 1) Turn the treenode into the correct structure (per node) for the expected Yale formatted output.
    def _format(treenode):
        output = dict()

        output["id"] = treenode.id
        output["parent"] = None if treenode.parent is None else treenode.parent.id
        output["name"] = treenode.name
        output["combination"] = "Sequential"
        output["attributes"] = []
        output["children"] = list(map(lambda child: _format(child), filter_treenode_children(treenode)))
        output["order"] = treenode.parent.order_of_action(treenode.name) if treenode.parent is not None else None

        return output

    output = _format(treenode)

    # 2) Any nodes with an identical order need to be grouped (a grouping node is injected; this allows for
    #    marking of parallel actions.
    def _group(output):
        grouped_children = []
        current_order = 0
        current_group = []
        for child in output["children"]:
            order = child["order"] if child["order"] is not None else current_order + 1

            if order > current_order:
                current_order = order
                if len(current_group) > 0:
                    grouped_children.append(make_grouped_node(current_group, output["name"], output["id"]))
                current_group = []

            current_group.append(child)

        if len(current_group) > 0:
            grouped_children.append(make_grouped_node(current_group, output["name"], output["id"]))

        for child in output["children"]:
            _group(child)

        output["children"] = grouped_children
        return output

    output = _group(output)

    # 3) Remove any unneeded fields (e.g. "order").
    def _clean(output):
        del output["order"]
        for child in output["children"]:
            _clean(child)

        return output

    output = _clean(output)

    if output["name"] == "":
        output["name"] = "Start"
        return {
            "nodes": output
        }
    else:
        return output


def make_grouped_node(group, parent_name, parent_id):
    if len(group) == 1:
        return group[0]

    output = dict()

    from backend.treenode import TreeNode
    output["id"] = TreeNode.id
    TreeNode.id += 1

    output["parent"] = parent_id
    output["name"] = "Parallelized Subtasks of " + parent_name
    output["combination"] = "Sequential"
    output["attributes"] = []
    output["children"] = group
    output["order"] = None

    for child in group:
        child["parent"] = output["id"]
        child["combination"] = "Parallel"

    return output


# Return only children of the treenode that should be part of the results to the Yale Robot
def filter_treenode_children(treenode):
    return list(filter(lambda child: filter_treenode(child), treenode.children))


# True if the treenode should be returned as part of the results to the Yale Robot
def filter_treenode(treenode):

    # Don't return any "RELEASE" actions (RESTRAIN.AGENT = ROBOT)
    for restrain in treenode.tmr.find_by_concept("RESTRAIN"):
        if "ROBOT" in restrain["AGENT"]:
            return False

    return True


def tmr_action_name(tmr):

    actions = {
        "TAKE": "GET",
        "HOLD": "HOLD",
        "RESTRAIN": "RELEASE",
        "FASTEN": "FASTEN"
    }

    event = tmr.find_main_event()
    request_actions = tmr.find_by_concept("REQUEST-ACTION")
    if len(request_actions) == 1:
        request_action = request_actions[0]

        if "THEME" not in request_action:
            raise Exception("Bad action TMR (no THEME found).")
        if len(request_action["THEME"]) != 1:
            raise Exception("Bad action TMR (not exactly 1 REQUEST-ACTION.THEME).")

        event = tmr[request_action["THEME"][0]]

    if "AGENT" not in event or len(event["AGENT"]) != 1:
        raise Exception("Bad action TMR (not exactly 1 REQUEST-ACTION.THEME.AGENT).")
    if "THEME" not in event or len(event["THEME"]) != 1:
        raise Exception("Bad action TMR (not exactly 1 REQUEST-ACTION.THEME.THEME).")

    agent = tmr[event["AGENT"][0]]
    agent = agent if type(agent) == str else agent.concept

    action = actions[event.concept] if event.concept in actions else event.concept
    action_theme = tmr[event["THEME"][0]].token

    return agent + " " + action + "(" + action_theme + ")"


def input_to_tmrs(input):
    tmrs = []

    for i in range(len(input)):
        if input[i][0] == "a":
            tmrs.append(action_to_tmr(input[i][1]))
        elif input[i][0] == "u":
            tmrs.append(analyze(input[i][1]))
        else:
            raise Exception("Unknown input type '" + input[i][0] + "'.")

    return tmrs


def action_to_tmr(action):
    actions = {
        "get-screwdriver": "Get a screwdriver.",
        "get-bracket-foot": "Get a foot bracket.",
        "get-bracket-front": "Get a front bracket.",
        "get-bracket-back-right": "Get the back bracket on the right side.",
        "get-bracket-back-left": "Get the back bracket on the left side.",
        "get-dowel": "Get a dowel.",
        "hold-dowel": "Hold the dowel.",
        "release-dowel": "Release the dowel.",
        "get-seat": "Get the seat.",
        "hold-seat": "Hold the seat.",
        "get-back": "Get the back.",
        "hold-back": "Hold the back.",
    }

    if action in actions:
        return analyze(actions[action])

    raise Exception("Unknown action '" + action + "'.")


def analyze(utterance):
    response = requests.post(url=ontosem_service() + "/analyze", data={"text":utterance})
    return json.loads(response.text)[0]