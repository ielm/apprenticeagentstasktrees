from ontograph.Frame import Frame
from ontograph.Query import SearchComparator
from typing import List


@DeprecationWarning
class Path(object):

    def __init__(self):
        self.steps = []

    def __str__(self):
        return "".join(self.steps)

    def __repr__(self):
        return str(self)

    def to(self, relation: str, recursive: bool=False, comparator: SearchComparator=None) -> 'Path':
        self.steps.append(PathStep(relation, recursive, comparator))
        return self

    def to_step(self, step: 'PathStep') -> 'Path':
        self.steps.append(step)
        return self

    def start(self, frame: Frame) -> List[Frame]:
        results = []

        current = [frame]

        step_queue = list(self.steps)
        while len(step_queue) > 0:
            step = step_queue[0]
            next = []
            for f in current:
                next.extend(self._follow(f, step))

            results_ids = set(map(lambda result: result.id, results))
            next_ids = set(map(lambda result: result.id, next))
            to_add_ids = next_ids.difference(results_ids)
            next = list(filter(lambda result: result.id in to_add_ids and result != frame, next))

            current = next
            results.extend(current)

            if not step.recursive:
                step_queue.pop(0)
            elif len(next) == 0:
                step_queue.pop(0)

        return results

    def _follow(self, frame: Frame, step: 'PathStep') -> List[Frame]:
        results = []

        fillers = list(frame[step.relation])
        if step.relation == "*":
            for slot in frame:
                fillers.extend(slot)

        for filler in fillers:
            if step.comparator is None or step.comparator.compare(filler):
                results.append(filler)
        return results

    def __eq__(self, other):
        if not isinstance(other, Path):
            return super().__eq__(other)
        return self.steps == other.steps


@DeprecationWarning
class PathStep(object):

    def __init__(self, relation: str, recursive: bool, comparator: SearchComparator):
        self.relation = relation
        self.recursive = recursive
        self.comparator = comparator

    def __str__(self):
        return "[" + self.relation + ("*" if self.recursive else "") + "]->" + ("q" if self.comparator is not None else "")

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if not isinstance(other, PathStep):
            return super().__eq__(other)
        return self.relation == other.relation and self.recursive == other.recursive and self.comparator == other.comparator