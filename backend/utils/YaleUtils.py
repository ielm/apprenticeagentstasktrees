

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
