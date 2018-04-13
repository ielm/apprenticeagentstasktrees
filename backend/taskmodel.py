from backend.heuristics.postfix_heuristics import PostfixHeuristics
from backend.heuristics.prefix_heuristics import PrefixHeuristics
from backend.heuristics.resolution_heuristics import ResolutionHeuristics
from backend.models.tmr import TMR
from backend.treenode import TreeNode
from backend.models.fr import FR


class TaskModel(PrefixHeuristics, PostfixHeuristics, ResolutionHeuristics, object):

    def __init__(self):
        self.root = TreeNode()
        self.active_node = self.root
        self.fr = FR()

    def learn(self, instructions):

        for instruction_set in instructions:
            if len(instruction_set) == 0:
                raise Exception("Instructions generated an empty set.")

            # Currently, assume all inputs have exactly one TMR.
            tmrs = list(map(lambda instruction: TMR(instruction), instruction_set))

            if tmrs[0].is_utterance():
                self.handle_utterance(tmrs[0])
            else:
                self.handle_actions(tmrs)

            for tmr in tmrs:
                self.fr.learn_tmr(tmr)

        heuristics = [
            self.settle_disputes,
            self.find_parallels,
        ]

        for heuristic in heuristics:
            heuristic()

        # settle_disputes(self.root)
        # find_parallels(self.root)

        return self.root

    def handle_utterance(self, tmr):

        if tmr.is_postfix():
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
                self.active_node.finish()
                self.active_node = candidate
                break

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
                self.active_node.finish()
                self.active_node = candidate
                break

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