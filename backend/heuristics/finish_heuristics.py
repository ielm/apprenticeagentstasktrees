from backend.models.tmr import TMR


class FinishHeuristics(object):

    def handle_finish_unmatched_hold_and_release_actions(self):
        # If a node is marked as finished, but contains one or more HOLD actions, and no matching RELEASE actions,
        # we add RELEASE actions (in reverse order) to the end of the action set.

        if not self.terminal:
            return

        holds = []
        for child in self.children:
            # Find each HOLD (by the ROBOT), and mark its THEME
            for hold in child.tmr.find_by_concept("HOLD"):
                if "ROBOT" in hold["AGENT"]:
                    holds.extend(list(map(lambda theme: {"concept": child.tmr[theme].concept, "token": child.tmr[theme].token}, hold["THEME"])))

        for child in self.children:
            # Find each RELEASE (by the ROBOT)
            # Remove the last instance of the THEME from holds (remove in reverse order)
            # Mark "removed" with the "satisfied" property
            for release in child.tmr.find_by_concept("RESTRAIN"):
                for scopeof in release["SCOPE-OF"]:
                    scope = child.tmr[scopeof]
                    if scope.concept == "ASPECT" and "END" in scope["PHASE"]:
                        for theme in list(map(lambda theme: child.tmr[theme].concept, release["THEME"])):
                            holds.reverse()
                            for hold in holds:
                                if hold["concept"] == theme:
                                    hold["satisfied"] = True
                                    break

        for hold in holds:
            # All remaining HOLD actions must now have a corresponding RELEASE action added
            # A remaining HOLD is not "satisfied"

            if "satisfied" in hold and hold["satisfied"]:
                continue

            tmr = {
                "sentence": "(implied) Release the " + hold["token"] + ".",
                "results": [{
                    "TMR": {
                        hold["concept"] + "-1": {
                            "THEME-OF": "RESTRAIN-1",
                            "concept": hold["concept"],
                            "is-in-subtree": "OBJECT",
                            "token": hold["token"],
                        },
                        "RESTRAIN-1": {
                            "AGENT": "ROBOT",
                            "SCOPE-OF": "ASPECT-1",
                            "THEME": hold["concept"] + "-1",
                            "THEME-OF": "REQUEST-ACTION-1",
                            "token": "Release",
                            "concept": "RESTRAIN",
                        },
                        "ASPECT-1": {
                            "PHASE": "END",
                            "SCOPE": "RESTRAIN-1",
                            "concept": "ASPECT",
                            "token": "Release",
                        },
                        "REQUEST-ACTION-1": {
                            "AGENT": "HUMAN",
                            "BENEFICIARY": "ROBOT",
                            "THEME": "RESTRAIN-1",
                            "TIME": [
                                "FIND-ANCHOR-TIME"
                            ],
                            "concept": "REQUEST-ACTION",
                            "is-in-subtree": "EVENT",
                            "token": "Release",
                        }
                    }
                }]
            }

            self.addAction(TMR(tmr))