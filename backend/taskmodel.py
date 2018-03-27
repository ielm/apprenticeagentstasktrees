from tmrutils import about_part_of
from tmrutils import find_main_event
from tmrutils import is_postfix
from tmrutils import is_utterance
from tmrutils import same_main_event
from treenode import TreeNode


class TaskModel:

    def __init__(self):
        self.root = TreeNode()
        self.active_node = self.root

    def learn(self, instructions):

        for instruction_set in instructions:
            if len(instruction_set) == 0:
                raise Exception("Instructions generated an empty set.")

            if is_utterance(instruction_set[0]):
                self.handle_utterance(instruction_set[0])
            else:
                self.handle_actions(instruction_set)

            # TODO: settle_disputes(root)
            # TODO: find_parallels(root)

        return self.root

    def handle_utterance(self, utterance):
        # Currently, assume all inputs have exactly one TMR.
        tmr = utterance["results"][0]["TMR"]

        # Skip phatic utterances for now.
        if find_main_event(tmr) is None:
            return

        if is_postfix(tmr):
            self.handle_postfix_utterance(tmr)
        else:
            self.handle_prefix_utterance(tmr)

    def handle_prefix_utterance(self, tmr):
        # A prefix utterance necessarily starts a new EVENT node.
        # Wherever the current active node is, we consider that (and its ancestry up to the root) looking for any
        # event where the theme of this (input) event is a part (HAS-OBJECT-AS-PART) of the inspected event.
        # If we find a match, we can add this new input event under the match - otherwise, we assume that it belongs
        # under the current active node (or its closest non-terminal ancestor).

        candidate = self.active_node

        while candidate.parent is not None and not about_part_of(tmr, candidate.tmr):
            candidate = candidate.parent

        # If a HAS-OBJECT-AS-PART match was found, use that; otherwise, active_node is unchanged.
        if candidate.parent is not None:
            self.active_node = candidate

        # If the active_node is a terminal, select its parent (the parent is necessarily the closest non-terminal
        # ancestor, so it can be selected by default).
        if self.active_node.terminal:
            self.active_node = self.active_node.parent

        event = TreeNode(tmr)
        self.active_node.addChildNode(event)
        self.active_node = event

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

        # 1) Check to see if this utterance was already mentioned in prefix (and do bail out if so).
        if self.handle_postfix_utterance_already_mentioned(tmr):
            if self.active_node.parent is not None:
                self.active_node = self.active_node.parent
            return

        # 2) Check for a presumed event (an event node with no TMR) and assign this TMR if found.
        if self.handle_postfix_utterance_presumed_event(tmr):
            if self.active_node.parent is not None:
                self.active_node = self.active_node.parent
            return

        # 3a) Check if this utterance must be injected between utterances in the ancestry.
        # TODO

        # 3b) Check if this utterance must be injected between the active_node and its actions.
        # TODO

        # 3c) Check if this utterance should be a disputed sibling of the active_node (disputing its actions).
        # TODO

    def handle_postfix_utterance_already_mentioned(self, tmr):
        candidate = self.active_node
        if same_main_event(candidate.tmr, tmr):
            return True

        while candidate.parent is not None:
            candidate = candidate.parent
            if same_main_event(candidate.tmr, tmr):
                self.active_node = candidate
                return True

        return False

    def handle_postfix_utterance_presumed_event(self, tmr):
        candidate = self.active_node
        if candidate.tmr is None and candidate.terminal:
            candidate.setTmr(tmr)
            return True

        while candidate.parent is not None:
            candidate = candidate.parent
            if candidate.tmr is None and candidate.terminal:
                candidate.setTmr(tmr)
                self.active_node = candidate
                return True

        return False

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