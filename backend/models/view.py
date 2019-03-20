# from backend.agent import Agent
# from backend.models.path import Path
# from ontograph.Frame import Facet, Frame, Slot
# from ontograph.Query import Query
# from ontograph.Space import Space
# from typing import Any, List, Iterable, Union
#
#
# class Network(object): pass
# class Graph(object): pass
#
#
# class View(object):
#
#     def __init__(self, agent: Agent, space: Union[Space, str], query: Query=None, follow: Union[List[Path], Path]=None, filter=None, include=None, exclude=None):
#         self.agent = agent
#         self.space = space if isinstance(space, str) else space.name
#
#         self.query = query
#
#         if follow is not None and not isinstance(follow, list):
#             follow = [follow]
#
#         self.follow = follow
#         self.filter = filter
#
#     def view(self) -> 'ViewGraph':
#         frames = list(Space(self.space)) if self.query is None else self.query.start(Space(self.space))
#
#         if self.follow is not None:
#             followed_results = []
#             for path in self.follow:
#                 for frame in frames:
#                     followed_results.extend(path.start(frame))
#             frames.extend(followed_results)
#
#         excluded = set(map(lambda frame: frame.id, Space(self.space))).difference(set(map(lambda frame: frame.id, frames)))
#
#         view = ViewGraph(self.space, excluded)
#         view.set_frames(frames)
#
#         return view
#
#     def __eq__(self, other):
#         if not isinstance(other, View):
#             return super().__eq__(other)
#         return self.agent == other.agent and self.space == other.space and self.query == other.query and self.follow == other.follow and self.filter == other.filter
#
#
# class ViewGraph(Space):
#
#     def __init__(self, namespace: str, excluded: set):
#         super().__init__(namespace)
#         self.frames = None
#         self.excluded = excluded
#
#     def set_frames(self, frames: List[Frame]):
#         self.frames = frames
#
#     def __iter__(self) -> Iterable[Frame]:
#         if self.frames is None:
#             for frame in super().__iter__():
#                 yield ViewFrame(frame.id, self.excluded)
#
#
#         for frame in self.frames:
#             yield ViewFrame(frame, self.excluded)
#
#
# class ViewFrame(Frame):
#
#     def __init__(self, frame: Frame, excluded: set):
#         super().__init__(frame.id, declare=False)
#         self.excluded = excluded
#
#     def slots(self):
#         return list(filter(lambda slot: len(slot) > 0, map(lambda slot: ViewSlot(slot, self.excluded), super().slots())))
#
#
# class ViewSlot(Slot):
#
#     def __init__(self, slot: Slot, excluded: set):
#         super().__init__(slot.frame, slot.property, as_inverse=slot.as_inverse, include_inherited=slot.include_inherited)
#         self.excluded = excluded
#
#     def facets(self):
#         return list(map(lambda facet: ViewFacet(facet, self.excluded), super().facets()))
#
#     def list(self):
#         for filler in super().list():
#             if not isinstance(filler, Frame) or filler.id not in self.excluded:
#                 yield filler
#
#
# class ViewFacet(Facet):
#
#     def __init__(self, facet: Facet, excluded: set):
#         super().__init__(facet.frame, facet.property, facet.type, as_inverse=facet.as_inverse, include_inherited=facet.include_inherited)
#         self.excluded = excluded
#
#     def list(self) -> Iterable[Any]:
#         for filler in super().list():
#             if not isinstance(filler, Frame) or filler.id not in self.excluded:
#                 yield filler