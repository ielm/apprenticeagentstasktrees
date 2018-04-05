from backend.treenode import TreeNode


class PostfixHeuristics(object):

    def handle_postfix_utterance_already_mentioned(self, tmr):
        # Postfix Heuristic 1
        # Check to see if this utterance was already mentioned in prefix (and bail out if so).

        # pre) Is this a generic closing utterance (e.g., "Finished.")
        if tmr.find_main_event() is None:
            for aspect in tmr.find_by_concept("ASPECT"):
                if "EVENT" in aspect["SCOPE"] and "END" in aspect["PHASE"]:
                    candidate = self.active_node
                    if candidate.type == "leaf":
                        candidate = candidate.parent
                    return candidate

        # a) Is the main event the same?
        candidate = self.active_node
        if candidate.tmr is not None and candidate.tmr.has_same_main_event(tmr):
            return candidate.parent

        while candidate.parent is not None:
            candidate = candidate.parent
            if candidate.tmr is not None and candidate.tmr.has_same_main_event(tmr):
                return candidate.parent

        # b) Is the theme of the main event the same?  (This option was added to handle the BUILD/ASSEMBLE issue)
        candidate = self.active_node
        if candidate.tmr is not None and len(set(candidate.tmr.find_themes()).intersection(set(tmr.find_themes()))) > 0:
            return candidate.parent

        while candidate.parent is not None:
            candidate = candidate.parent
            if candidate.tmr is not None and len(set(candidate.tmr.find_themes()).intersection(set(tmr.find_themes()))) > 0:
                return candidate.parent

        # c) Is this a generic event scoped by an ASPECT with PHASE = END?  ("We are done.")
        candidate = self.active_node
        event = tmr.find_main_event()
        if event.concept == "EVENT":
            for aspect in event["SCOPE-OF"]:
                if "END" in tmr[aspect]["PHASE"]:
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

        if self.active_node.tmr is not None and not self.active_node.tmr.about_part_of(tmr):
            return None

        candidate = self.active_node
        while candidate.parent != self.root and candidate.parent is not None and candidate.parent.tmr.about_part_of(tmr):
            candidate = candidate.parent

        if candidate.parent != self.root and candidate.parent is not None:
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

        if tmr.about_part_of(self.active_node.tmr):
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

        if not tmr.about_part_of(self.active_node.tmr):
            event = TreeNode(tmr)

            self.active_node.parent.addChildNode(event)
            self.active_node.disputeWith(event)

            return event.parent

        return None