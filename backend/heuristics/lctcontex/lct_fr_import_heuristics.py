from backend.heuristics.fr_heuristics import FRImportHeuristic


# ------ FR Import Heuristics -------

# An import heuristic that filters out request action frames; these are not needed to be moved to long term memory.
class FRImportDoNotImportRequestActions(FRImportHeuristic):

    def filter(self, import_fr, status):
        for instance in import_fr:
            if import_fr[instance].concept == "REQUEST-ACTION":
                status[instance] = False