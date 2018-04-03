

def format_treenode_yale(treenode):

    output = dict()

    output["id"] = treenode.id
    output["parent"] = None if treenode.parent is None else treenode.parent.id
    output["name"] = treenode.name
    output["combination"] = treenode.type
    output["attributes"] = []
    output["children"] = list(map(lambda child: format_treenode_yale(child), treenode.children))

    if treenode.name == "root":
        return {
            "nodes": output
        }
    else:
        return output


def tmr_action_name(tmr):

    actions = {
        "TAKE": "GET",
        "HOLD": "HOLD",
        "RESTRAIN": "RELEASE"
    }

    request_actions = tmr.find_by_concept("REQUEST-ACTION")
    if len(request_actions) != 1:
        raise Exception("Bad action TMR (not exactly 1 REQUEST-ACTION).")

    request_action = request_actions[0]
    if "THEME" not in request_action:
        raise Exception("Bad action TMR (no THEME found).")
    if len(request_action["THEME"]) != 1:
        raise Exception("Bad action TMR (not exactly 1 REQUEST-ACTION.THEME).")

    theme = tmr[request_action["THEME"][0]]
    if "AGENT" not in theme or len(theme["AGENT"]) != 1:
        raise Exception("Bad action TMR (not exactly 1 REQUEST-ACTION.THEME.AGENT).")
    if "THEME" not in theme or len(theme["THEME"]) != 1:
        raise Exception("Bad action TMR (not exactly 1 REQUEST-ACTION.THEME.THEME).")

    agent = theme["AGENT"][0]
    action = actions[theme.concept]
    action_theme = tmr[theme["THEME"][0]].token

    return agent + " " + action + "(" + action_theme + ")"