from backend.models.graph import Frame, Graph, Identifier, Network
from backend.models.query import FrameQuery
from typing import List, Union


class View(object):

    # query: A FrameQuery as a starting point for included frames in the view.
    # paths: A set of instructions for paths to follow from the included frames; anything on the paths is also included.
    # filter: A set of relations (type only) to exclude.
    # include: A set of IDs to include.
    # exclude: A set of IDs to exclude.
    def __init__(self, network: Network, graph: Union[Graph, str], query: FrameQuery=None, paths=None, filter=None, include=None, exclude=None):
        self.network = network
        self.namespace = graph if isinstance(graph, str) else graph._namespace

        self.query = query
        self.paths = paths
        self.filter = filter

    def view(self) -> 'ViewGraph':
        graph = self.network[self.namespace]
        namespace = self.namespace

        view = ViewGraph(namespace)
        frames = list(map(lambda frame: frame.deep_copy(view), graph._storage.values() if self.query is None else graph.search(self.query)))
        excluded = set(map(lambda frame: frame._identifier.render(), graph._storage.values())).difference(set(map(lambda frame: frame._identifier.render(), frames)))

        for f in excluded:
            for frame in frames:
                to_remove = []
                for s in frame._storage.values():
                    s -= Identifier.parse(f)
                    if len(s) == 0:
                        to_remove.append(s._name)
                for s in to_remove:
                    del frame._storage[s]

        view.set_frames(frames)

        return view

    def __eq__(self, other):
        if not isinstance(other, View):
            return super().__eq__(other)
        return self.network == other.network and self.namespace == other.namespace and self.query == other.query and self.paths == other.paths and self.filter == other.filter


class ViewGraph(Graph):

    def __init__(self, namespace: str):
        super().__init__(namespace)

    def set_frames(self, frames: List[Frame]):
        for frame in frames:
            self[frame._identifier] = frame