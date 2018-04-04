

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
