# from backend.heuristics.fr_heuristics import FRResolutionHeuristic
from backend.contexts.context import ContextBasedFRResolutionHeuristic


# ------ FR Resolution Heuristics -------

# FR resolution method used to connect an instance that is undetermined ("a chair" rather than "the chair") to an
# existing FR instance by looking for instances that are the "themes of learning" (in other words, what is currently
# being learned).
# Example: We will build a chair.  I need a screwdriver to assemble [a chair].
#   The 2nd instance of "a chair" would typically not be connected to the first, due to the lack of a determiner.
#   However, as the first usage of "a chair" kicked off a theme of learning (that is still active), we are more
#   flexible with resolution.
# To do this:
#   1) The instance to resolve must be an OBJECT
#   2) The instance to resolve must be undetermined ("a chair")
#   3) The instance must be the THEME of an EVENT that also has a PURPOSE, which must be another EVENT
#   4) If so, then any corresponding concept match in the FR is a valid resolution
#      Note, this last match is a little broad, but is ok in that this resolution heuristic operates in short-term
#      memory only.
class FRResolveUndeterminedThemesOfLearning(ContextBasedFRResolutionHeuristic):

    def resolve(self, instance, resolves, tmr=None):
        if instance.subtree != "OBJECT":
            return

        if tmr is None:
            return

        dependencies = tmr.syntax.find_dependencies(types=["ART"], governors=instance.token_index)
        articles = list(map(lambda dependency: tmr.syntax.index[str(dependency[2])], dependencies))
        tokens = list(map(lambda article: article["lemma"], articles))

        if "A" not in tokens:
            return

        if "THEME-OF" not in instance:
            return

        theme_ofs = map(lambda theme_of: tmr[theme_of], instance["THEME-OF"])

        for theme_of in theme_ofs:
            if "PURPOSE-OF" in theme_of:
                purpose_ofs = map(lambda purpose_of: tmr[purpose_of], theme_of["PURPOSE-OF"])
                purpose_ofs = filter(lambda purpose_of: purpose_of.subtree == "EVENT", purpose_ofs)
                if len(list(purpose_ofs)) > 0:
                    results = self.fr.search(concept=instance.concept)
                    resolves[instance.name] = set(map(lambda result: result.name, results))
                    return True


# FR resolution method for identifying that an undetermined ("a chair") object that is the THEME of a
# resolved EVENT that is currently being learned, is the same THEME as other similar types of THEMEs found
# in the resolved EVENT, if the TMR is postfix.
# Example: First, we will build a front leg of the chair.  We have assembled [a front leg].
# To match, the following must be true:
#   1) The TMR must be in postfix ("we have")
#   2) The instance must be an OBJECT
#   3) The instance must be undetermined ("a chair")
#   4) The instance must be a THEME-OF an EVENT in the TMR
#   5) That EVENT must be found (roughly resolved) in the FR by concept match, AND as LCT.learning
#   6) For each THEME of the matching FR EVENT, any that are the same concept as the instance are resolved matches
class FRResolveUnderterminedThemesOfLearningInPostfix(ContextBasedFRResolutionHeuristic):

    def resolve(self, instance, resolves, tmr=None):
        if instance.subtree != "OBJECT":
            return

        if tmr is None:
            return

        if tmr.is_prefix():
            return

        dependencies = tmr.syntax.find_dependencies(types=["ART"], governors=instance.token_index)
        articles = list(map(lambda dependency: tmr.syntax.index[str(dependency[2])], dependencies))
        tokens = list(map(lambda article: article["lemma"], articles))

        if "A" not in tokens:
            return

        if "THEME-OF" not in instance:
            return

        theme_ofs = map(lambda theme_of: tmr[theme_of], instance["THEME-OF"])

        matches = set()

        from backend.contexts.LCTContext import LCTContext

        for theme_of in theme_ofs:
            results = self.fr.search(concept=theme_of.concept, context={LCTContext.LEARNING: True})
            for result in results:
                for theme in result["THEME"]:
                    if self.fr[theme.value].concept == instance.concept:
                        matches.add(theme.value)

        if len(matches) > 0:
            resolves[instance.name] = matches
            return True


# FR resolution method for resolving EVENTs against currently learning FR events.
# Example: First, we will build a front leg of the chair.  We [have assembled] a front leg.
# To be a match, the following must be true:
#   1) The instance must be an EVENT
#   2) A candidate in the FR must be the same concept as the instance
#   3) A candidate in the FR must be LTC.learning
#   4) A candidate in the FR must have at least one *resolved* match for each case-role filler specified by
#      the instance.  (Currently, this includes only AGENT and THEME).  That is, if "AGENT" is defined in the
#      instance, that filler must a) be resolved, and b) be equal to one of the AGENT fillers in the candidate.
class FRResolveLearningEvents(ContextBasedFRResolutionHeuristic):

    def resolve(self, instance, resolves, tmr=None):
        if instance.subtree != "EVENT":
            return

        if tmr is None:
            return

        matches = set()

        from backend.contexts.LCTContext import LCTContext

        for candidate in self.fr.search(concept=instance.concept, context={LCTContext.LEARNING: True}):
            case_roles = ["AGENT", "THEME"]

            passed = True
            for case_role in case_roles:
                if case_role in instance:
                    for filler in instance[case_role]:
                        if resolves[filler] is None:
                            passed = False
                            break

                        if len(resolves[filler].intersection(set(map(lambda f: f.value, candidate[case_role])))) == 0:
                            passed = False
                            break

            if passed:
                matches.add(candidate.name)

        if len(matches) > 0:
            resolves[instance.name] = matches
            return True