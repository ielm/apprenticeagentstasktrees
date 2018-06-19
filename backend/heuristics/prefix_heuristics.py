from backend.treenode import TreeNode


class PrefixHeuristics(object):

    def handle_prefix_utterance_with_no_event(self, tmr):
        # Prefix Heuristic 1
        # If there is no event, consider first the active_node's children, and then the nearest ancestor to the
        # active_node whose THEME is any OBJECT in this utterance to be a sibling, and add this utterance as a "copy".
        # This handles things such as "Now, another leg."

        if tmr.find_main_event() is not None:
            return None

        objects = tmr.find_objects()

        if len(objects) == 0:
            return None  # What does a TMR with no event or object mean?

        # a) First, look to see if any children are a match
        for child in self.active_node.children:
            if len(set.intersection(set(child.tmr.find_themes()), set(objects))) > 0:
                event = TreeNode(child.tmr)
                event.setOriginalTMR(tmr)
                self.active_node.addChildNode(event)
                return event

        # b) Now find the nearest matching ancestor
        candidate = self.active_node

        while candidate.parent is not None:
            if len(set.intersection(set(candidate.tmr.find_themes()), set(objects))) > 0:
                event = TreeNode(candidate.tmr)
                event.setOriginalTMR(tmr)
                candidate.parent.addChildNode(event)
                return event
            else:
                candidate = candidate.parent

        return None

    def handle_prefix_utterance_destination_is_known(self, tmr):
        # Prefix Heuristic 2
        # Find the nearest ancestor whose THEME is the same type (hierarchically) as the DESTINATION of the input
        # TMR.  This handles cases such as:
        # "Now, we affix the verticals."  THEME = verticals
        #    "Now we must affix the back to the vertical pieces."  DESTINATION = verticals

        def _compare_theme_to_destination(tmr_with_theme, tmr_with_destination):
            if tmr_with_theme is None or tmr_with_destination is None:
                return False

            themes = tmr_with_theme.find_main_event()["THEME"]
            destinations = tmr_with_destination.find_main_event()["DESTINATION"]

            themes = set(map(lambda theme: tmr_with_theme[theme].concept, themes))
            destinations = set(map(lambda destination: tmr_with_destination[destination].concept, destinations))

            return len(themes.intersection(destinations)) > 0

        candidate = self.active_node

        # while candidate.parent is not None and not candidate.theme = tmr.destination:
        while candidate is not None and not _compare_theme_to_destination(candidate.tmr, tmr):
            candidate = candidate.parent

        if candidate is None:
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

    def handle_prefix_utterance_about_existing_event(self, tmr):
        # Prefix Heuristic 3
        # Find the nearest ancestor (starting with active_node) where the THEME of this tmr is a part of the THEME
        # of the ancestor tmr (using HAS-OBJECT-AS-PART).  If one is found, add the new node in one of two ways:
        # 1) The active node is non-terminal = add the node as a child.
        # 2) The active node is a terminal = inject the node between the active node and its actions.

        candidate = self.active_node

        # We include tmr.about_same_events(candidate.tmr) here to solve the problem with demo sentence
        # "I need a screwdriver..." and later "We build a front leg...".  Simply testing the
        # HAS-OBJECT-AS-PART is no good, because SCREWDRIVER HAS-OBJECT-AS-PART ARTIFACT-PART, and ARTIFACT-LEG
        # IS-A ARTIFACT-PART, so this would see the front leg as part of the screwdriver.
        while candidate.parent is not None and not (tmr.about_same_events(candidate.tmr) and tmr.about_part_of(candidate.tmr)):
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
        # Prefix Heuristic 4
        # If the previous heuristics could not be matched, assume that the active node must be the parent.  Add the
        # new node in one of three ways:
        # 1) The active node is terminal, and the new node is about the active node's children = inject the node.
        # 2) The active node is a terminal = add the node to the parent.
        # 3) The active node is non-terminal = add the node as a child.

        event = TreeNode(tmr)

        if self.active_node.terminal and tmr.is_about(list(map(lambda child: child.tmr, self.active_node.children))):
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