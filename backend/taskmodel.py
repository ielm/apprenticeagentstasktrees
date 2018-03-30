from tmrutils import about_part_of
from tmrutils import find_main_event
from tmrutils import find_objects
from tmrutils import find_themes
from tmrutils import is_about
from tmrutils import is_postfix
from tmrutils import is_utterance
from tmrutils import same_main_event
from treenode import TreeNode

import maketree


class TaskModel:

    def __init__(self):
        self.root = TreeNode()
        self.active_node = self.root

    def learn(self, instructions):

        for instruction_set in instructions:
            if len(instruction_set) == 0:
                raise Exception("Instructions generated an empty set.")

            # Currently, assume all inputs have exactly one TMR.
            tmrs = list(map(lambda instruction: instruction["results"][0]["TMR"], instruction_set))

            if is_utterance(tmrs[0]):
                self.handle_utterance(tmrs[0])
            else:
                self.handle_actions(tmrs)

        maketree.settle_disputes(self.root)
        maketree.find_parallels(self.root)

        return self.root

    def handle_utterance(self, tmr):

        if is_postfix(tmr):
            self.handle_postfix_utterance(tmr)
        else:
            self.handle_prefix_utterance(tmr)

    def handle_prefix_utterance(self, tmr):
        # A prefix utterance necessarily starts a new EVENT node.
        # The utterance may refer to a previous event - in which case we want to find and "copy" it.
        # Otherwise, we search the ancestry for any nodes that are related via HAS-OBJECT-AS-PART, looking for the
        # right level to either add a child, or in some cases inject the new node between an event and its actions.

        heuristics = [
            self.handle_prefix_utterance_with_no_event,
            self.handle_prefix_utterance_about_existing_event,
            self.handle_prefix_utterance_fallback_behavior,
        ]

        for heuristic in heuristics:
            candidate = heuristic(tmr)
            if candidate is not None:
                self.active_node = candidate
                break

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

    def handle_postfix_utterance(self, tmr):
        # A postfix utterance should be matched to one of three distinct states:
        # 1) The utterance was mentioned in prefix along the current ancestry.  This postfix does nothing, and can
        #    be discarded (the node already exists from the prefix).
        # 2) The utterance was *presumed* due to input action instructions that could not be added to the active_node
        #    at the time (as that node already had children).  When that happens, an event node is created with no
        #    TMR, for actions to be applied to.  The postfix utterance is now "closing" that node, so the TMR can
        #    be applied there.  (Again, this node must be on the current ancestry path).
        # 3) The utterance is entirely new - we must determine where it fits:
        #    a) If the active_node's theme is part of this TMR's theme (via HAS-OBJECT-AS-PART), we follow the
        #       ancestry until that is not true.  At that point, we inject this new node - we take all children
        #       at that level that are part of this theme, and move them under the new node; any remaining children
        #       become siblings of the new node.
        #    b) If the last instruction(s) were action(s) and this TMR's theme is part of the active_node's theme
        #       via (HAS-OBJECT-AS-PART) then we have mis-assigned the actions to active_node; we instead inject
        #       this tmr in between (make it a child of active_node, and move the actions to it).
        #    c) If the last instruction(s) were action(s), but this TMR's theme is not part of the active_node's theme
        #       then we have a dispute - add this node as a child of active_node's parent, and share all the actions
        #       in active node with this node (and mark them all as disputed).  It is currently unclear which actions
        #       belong to which node.

        heuristics = [
            self.handle_postfix_utterance_already_mentioned,
            self.handle_postfix_utterance_presumed_event,
            self.handle_postfix_utterance_between_events,
            self.handle_postfix_utterance_before_actions,
            self.handle_postfix_utterance_causes_disputes,
        ]

        for heuristic in heuristics:
            candidate = heuristic(tmr)
            if candidate is not None:
                self.active_node = candidate
                break

    def handle_postfix_utterance_already_mentioned(self, tmr):
        # Postfix Heuristic 1
        # Check to see if this utterance was already mentioned in prefix (and bail out if so).

        # a) Is the main event the same?
        candidate = self.active_node
        if same_main_event(candidate.tmr, tmr):
            return candidate.parent

        while candidate.parent is not None:
            candidate = candidate.parent
            if same_main_event(candidate.tmr, tmr):
                return candidate.parent

        # b) Is the theme of the main event the same?  (This option was added to handle the BUILD/ASSEMBLE issue)
        candidate = self.active_node
        if len(set(find_themes(candidate.tmr)).intersection(set(find_themes(tmr)))) > 0:
            return candidate.parent

        while candidate.parent is not None:
            candidate = candidate.parent
            if len(set(find_themes(candidate.tmr)).intersection(set(find_themes(tmr)))) > 0:
                return candidate.parent

        return None

    def handle_postfix_utterance_presumed_event(self, tmr):
        # Postfix Heuristic 2
        # Check for a presumed event (an event node with no TMR) and assign this TMR if found.

        candidate = self.active_node
        if candidate.tmr is None and candidate.terminal:
            candidate.setTmr(tmr)
            return candidate.parent

        while candidate.parent is not None:
            candidate = candidate.parent
            if candidate.tmr is None and candidate is not self.root:
                candidate.setTmr(tmr)
                return candidate.parent

        return None

    def handle_postfix_utterance_between_events(self, tmr):
        # Postfix Heuristic 3a
        # Check if this utterance must be injected between utterances in the ancestry.

        if not about_part_of(self.active_node.tmr, tmr):
            return None

        candidate = self.active_node
        while candidate.parent != self.root and about_part_of(candidate.parent.tmr, tmr):
            candidate = candidate.parent

        if candidate.parent != self.root:
            parent = candidate.parent
            parent.removeChildNode(candidate)

            event = TreeNode(tmr)
            parent.addChildNode(event)
            event.addChildNode(candidate)

            return event.parent
        else:
            self.root.removeChildNode(candidate)

            event = TreeNode(tmr)
            self.root.addChildNode(event)
            event.addChildNode(candidate)

            return event.parent

        return None

    def handle_postfix_utterance_before_actions(self, tmr):
        # Postfix Heuristic 3b
        # Check if this utterance must be injected between the active_node and its actions.

        if not self.active_node.terminal or len(self.active_node.children) == 0:
            return None

        if about_part_of(tmr, self.active_node.tmr):
            event = TreeNode(tmr)

            actions = list(self.active_node.children)
            for action in actions:
                self.active_node.removeChildNode(action)
                event.addChildNode(action)

            self.active_node.addChildNode(event)
            return event.parent

        return None

    def handle_postfix_utterance_causes_disputes(self, tmr):
        # Postfix Heuristic 3c
        # Check if this utterance should be a disputed sibling of the active_node (disputing its actions).

        if not self.active_node.terminal or len(self.active_node.children) == 0:
            return None

        if not about_part_of(tmr, self.active_node.tmr):
            event = TreeNode(tmr)

            self.active_node.parent.addChildNode(event)
            self.active_node.disputeWith(event)

            return event.parent

        return None

    def handle_actions(self, actions):
        # All actions must be added at once - further, an EVENT node cannot have a mix of EVENT and ACTION children.
        # To find the correct node to add to:
        # 1) If the active_node has no children, we can add directly there.  An utterance has created this node,
        #    and the next instruction(s) are actions, so they belong to that utterance.
        # 2) If the active_node has children, but they are all actions, again, we can add directly there.  In
        #    principle the Instructions shouldn't generate back to back sets of actions (they should be one set)
        #    but we handle this here anyway. (This supports additive instructions later).
        # 3) If the active_node has children, but they are all events, we make a new event (with an unknown TMR)
        #    and add it to the active_node (and it becomes the active_node).  We can then add the actions to it.
        #    The newly created event node is a placeholder for a potential postfix utterance (or similar.

        if len(self.active_node.children) == 0:
            pass  # leave the active_node alone (it is empty)
        elif self.active_node.terminal:
            pass  # leave the active_node alone (it has only actions in it)
        else:
            event = TreeNode()
            self.active_node.addChildNode(event)
            self.active_node = event

        for action in actions:
            self.active_node.addAction(action)