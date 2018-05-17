

class QueryHeuristics(object):

    def _deep_copy_node(self, node):
        import copy
        result = copy.deepcopy(node) # TODO: not sufficient; all of the links need to be updated
        return result

    # If the TMR refers to any node with a matching main event type, and main event theme, and its anchor time
    # is considered ">", then assume this matching node should be ordered to the front of its siblings.
    def query_move_order_up(self, tmr):
        q_event = tmr.find_main_event()
        if ">" not in q_event["TIME"]:
            return None

        q_type = q_event.concept
        q_themes = set(map(lambda theme: tmr[theme].concept, q_event["THEME"]))

        copy = self._deep_copy_node(self.root)

        def _recurse(node):
            if node.tmr is not None:
                n_event = node.tmr.find_main_event()
                n_type = n_event.concept
                n_themes = set(map(lambda theme: node.tmr[theme].concept, n_event["THEME"]))

                if q_type == n_type and len(q_themes.intersection(n_themes)) > 0:
                    return node

            for child in node.children:
                match = _recurse(child)
                if match is not None:
                    return match

            return None

        match = _recurse(copy)

        if match is None:
            return None

        parent = match.parent
        parent.children.remove(match)
        parent.children.insert(0, match)
        return copy