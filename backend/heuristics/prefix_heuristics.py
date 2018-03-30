from tmrutils import find_main_event, find_objects, find_themes, about_part_of, is_about
from treenode import TreeNode


class PrefixHeuristics(object):

    def handle_prefix_utterance_with_no_event(self, tmr):
        # Prefix Heuristic 1
        # If there is no event, consider first the active_node's children, and then the nearest ancestor to the
        # active_node whose THEME is any OBJECT in this utterance to be a sibling, and add this utterance as a "copy".
        # This handles things such as "Now, another leg."

        if find_main_event(tmr) is not None:
            return None

        objects = find_objects(tmr)

        if len(objects) == 0:
            return None  # What does a TMR with no event or object mean?

        # a) First, look to see if any children are a match
        for child in self.active_node.children:
            if len(set.intersection(set(find_themes(child.tmr)), set(objects))) > 0:
                event = TreeNode(child.tmr)
                event.setOriginalTMR(tmr)
                self.active_node.addChildNode(event)
                return event

        # b) Now find the nearest matching ancestor
        candidate = self.active_node

        while candidate.parent is not None:
            if len(set.intersection(set(find_themes(candidate.tmr)), set(objects))) > 0:
                event = TreeNode(candidate.tmr)
                event.setOriginalTMR(tmr)
                candidate.parent.addChildNode(event)
                return event
            else:
                candidate = candidate.parent

        return None

    def handle_prefix_utterance_about_existing_event(self, tmr):
        # Prefix Heuristic 2
        # Find the nearest ancestor (starting with active_node) where the THEME of this tmr is a part of the THEME
        # of the ancestor tmr (using HAS-OBJECT-AS-PART).  If one is found, add the new node in one of two ways:
        # 1) The active node is non-terminal = add the node as a child.
        # 2) The active node is a terminal = inject the node between the active node and its actions.

        candidate = self.active_node

        while candidate.parent is not None and not about_part_of(tmr, candidate.tmr):
            candidate = candidate.parent

        if candidate.parent is None:
            return None

        event = TreeNode(tmr)

        if not candidate.terminal:
            candidate.addChildNode(event)
            return event
        else:
            actions = list(candidate.children)
            for action in actions:
                candidate.removeChildNode(action)
                event.addChildNode(action)

            candidate.addChildNode(event)
            return event

    def handle_prefix_utterance_fallback_behavior(self, tmr):
        # Prefix Heuristic 3
        # If the previous heuristics could not be matched, assume that the active node must be the parent.  Add the
        # new node in one of three ways:
        # 1) The active node is terminal, and the new node is about the active node's children = inject the node.
        # 2) The active node is a terminal = add the node to the parent.
        # 3) The active node is non-terminal = add the node as a child.

        event = TreeNode(tmr)

        if self.active_node.terminal and is_about(tmr, list(map(lambda child: child.tmr, self.active_node.children))):
            actions = list(self.active_node.children)
            for action in actions:
                self.active_node.removeChildNode(action)
                event.addChildNode(action)

            self.active_node.addChildNode(event)
            return event
        elif self.active_node.terminal:
            self.active_node.parent.addChildNode(event)
            return event
        else:
            self.active_node.addChildNode(event)
            return event