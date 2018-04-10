from backend.treenode import traverse_tree, update_children_relationships


# Heuristics to be run after each iteration of learn is complete.
class ResolutionHeuristics(object):

    # Finds any disputed children in the tree, and then attempts to find evidence either elsewhere in the tree
    # (where othertree == None) or in another provided tree that will sort the disputed children between potential
    # parents.
    def settle_disputes(self, othertree=None):
        if othertree is None:
            othertree = self.root
        for question in traverse_tree(self.root, True):
            for answer in traverse_tree(othertree, False):
                if answer.tmr is None or question.tmr is None:
                    continue
                if question.tmr.has_same_main_event(answer.tmr):
                    other = question.disputedWith

                    mapping = self.__get_children_mapping(answer, other, self.__same_node)

                    for i in range(len(mapping)):
                        if not mapping[i] is None:
                            mapping[i] = other.children[mapping[i]]
                    for i in range(len(answer.children)):
                        if not mapping[i] is None:
                            other.removeChildNode(mapping[i])

                    mapping = self.__get_children_mapping(other, question, lambda x, y: x.id == y.id)
                    for i in range(len(mapping)):
                        if not mapping[i] is None:
                            mapping[i] = question.children[mapping[i]]
                    for i in range(len(other.children)):
                        if not mapping[i] is None:
                            question.removeChildNode(mapping[i])

                    other.disputedWith = None
                    question.disputedWith = None
                    other.childrenStatus = [False] * len(other.children)
                    question.childrenStatus = [False] * len(question.children)

    # Finds any children in the tree that can be marked as occurring in any order, based on evidence either
    # elsewhere in the tree (where othertree == None) or in another provided tree.
    def find_parallels(self, othertree=None):
        if othertree is None:
            othertree = self.root
        for child1 in traverse_tree(self.root, False):
            for child2 in traverse_tree(othertree, False):
                if child1 is child2 or child1.tmr is None or child2.tmr is None or len(child1.children) != len(
                        child2.children):
                    # If two nodes have different numbers of children, that's probably because one of them is currently being added to.
                    # This might need to change later?
                    continue

                if child1.tmr.has_same_main_event(child2.tmr):
                    mapping = self.__get_children_mapping(child1, child2, self.__same_node)
                    update_children_relationships(child1, child2, mapping)

    def __get_children_mapping(self, a, b, comparison):
        return self.__get_nodes_mapping(a.children, b.children, comparison)

    # TODO: What exactly is this doing?
    def __get_nodes_mapping(self, alist, blist, comparison):  # There's probably a standard function for this
        mapping = [None] * len(alist)
        revmapping = [None] * len(blist)
        for i in range(len(alist)):
            j = 0
            while not (revmapping[j] is None and comparison(alist[i], blist[j])):
                j += 1
                if j >= len(blist):
                    break
                # raise RuntimeError("Cannot merge trees!")
                # TODO in the future, this will trigger some kind of alternatives situation
            else:
                mapping[i] = j
                revmapping[j] = i
                assert comparison(alist[i], blist[j])
        return mapping

    def __same_node(self, node1, node2):
        return node1.name == node2.name