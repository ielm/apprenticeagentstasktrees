from treenode import *

  
def settle_disputes(tree, othertree=None):
  if othertree is None:
    othertree = tree
  for question in traverse_tree(tree, True):
    for answer in traverse_tree(othertree, False):
      if answer.tmr is None or question.tmr is None:
        continue
      if question.tmr.has_same_main_event(answer.tmr):
        other = question.disputedWith
        
        mapping = get_children_mapping(answer, other, same_node)
        
        for i in range(len(mapping)):
          if not mapping[i] is None:
            mapping[i] = other.children[mapping[i]]
        for i in range(len(answer.children)):
          if not mapping[i] is None:
            other.removeChildNode(mapping[i])
        
        mapping = get_children_mapping(other, question, lambda x,y: x.id==y.id)
        for i in range(len(mapping)):
          if not mapping[i] is None:
            mapping[i] = question.children[mapping[i]]
        for i in range(len(other.children)):
          if not mapping[i] is None:
            question.removeChildNode(mapping[i])
        
        other.disputedWith = None
        question.disputedWith = None
        other.childrenStatus = [False]*len(other.children)
        question.childrenStatus = [False]*len(question.children)

def find_parallels(tree, othertree=None):
  if othertree is None:
    othertree = tree
  for child1 in traverse_tree(tree, False):
    for child2 in traverse_tree(othertree, False):
      if child1 is child2 or child1.tmr is None or child2.tmr is None or len(child1.children) != len(child2.children):
      # If two nodes have different numbers of children, that's probably because one of them is currently being added to.
      # This might need to change later?
        continue

      if child1.tmr.has_same_main_event(child2.tmr):
        mapping = get_children_mapping(child1, child2, same_node)
        update_children_relationships(child1, child2, mapping)

def get_nodes_mapping(alist, blist, comparison): #There's probably a standard function for this
  mapping = [None]*len(alist)
  revmapping = [None]*len(blist)
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

#TODO replace calls to this with calls to the other thing
def get_children_mapping(a, b, comparison):
  return get_nodes_mapping(a.children, b.children, comparison)

def same_node(node1, node2):
  return node1.name == node2.name

# def construct_tree(input, steps):
#   root = TreeNode()
#   current_parent = root
#   i=0
#   while i < len(input): # For each input token
#     output = dict()
#     steps.append(output)
#     if is_utterance(input[i]):
#       output["input"] = input[i]["sentence"]
#       tmr = input[i]["results"][0]["TMR"]
#       if find_main_event(tmr) is None: #phatic utterances etc. just get skipped for now
#         #if is_finality_statement(tmr):
#         #  if len(root.children) == 1:
#         #    root = root.children[0]
#         #else:
#         i+=1
#         steps.pop() # no output for this iteration
#         continue
#       elif is_postfix_OLD(input[i]):
#
#         closeable_branch = current_parent.children[-1]
#         while not (closeable_branch.tmr is None or same_main_event(closeable_branch.tmr, tmr)):
#           closeable_branch = closeable_branch.parent
#
#         if closeable_branch is not root:
#           if closeable_branch.tmr is None:
#             closeable_branch.setTmr(tmr)
#           current_parent = closeable_branch.parent
#
#         elif (not current_parent.children[-1].tmr is None) and about_part_of(current_parent.children[-1].tmr, tmr):
#           while about_part_of(current_parent.tmr, tmr) and not current_parent.parent is None:
#             current_parent = current_parent.parent
#
#           #Mark some of the preceding nodes as children of a new node
#           new = TreeNode(tmr)
#
#           j = 0
#           while j < len(current_parent.children) and not about_part_of(current_parent.children[j].tmr, tmr):
#             j +=1
#
#           if j < len(current_parent.children):
#             current_parent.disputedWith = new
#             new.disputedWith = current_parent
#
#           for child in current_parent.children[:j]:
#             new.addChildNode(copy.copy(child))
#             current_parent.markDisputed(child, True)
#             new.markDisputed(new.children[-1], True)
#
#           for child in current_parent.children[j:]:
#             new.addChildNode(child)
#             child.parent = new
#
#           #don't update relationships until done adding nodes to new
#           new.relationships = copy.deepcopy(current_parent.relationships)
#           current_parent.relationships = [ row[:j] for row in current_parent.relationships[:j] ]
#
#           assert(new.children[-1] is current_parent.children[-1])
#
#           for child in new.children[j:]:
#             current_parent.children.remove(child)
#             current_parent.childrenStatus.pop()
#
#           current_parent.addChildNode(new)
#           #And then add the rest of the nodes as disputed between this and its parent?
#           #... actually, what if this node is neither a sibling nor a child of current_parent but rather its parent?
#
#         elif i > 0 and is_action(input[i-1]): #If it was preceded by actions
#           if current_parent.children[-1].name == "": # if their node is unnamed (This code is redundant given the whole closeable_branch thing above, but I don't feel like refactoring it right now)
#             current_parent.children[-1].setTmr(tmr)
#           elif about_part_of(tmr, current_parent.children[-1].tmr):
#             #Insert this new node between the previous node and its children
#             new = TreeNode(tmr)
#             current_parent = current_parent.children[-1]
#
#             new.children = current_parent.children
#             current_parent.children = [new]
#             new.childrenStatus = current_parent.childrenStatus
#             current_parent.childrenStatus = [False]
#             new.relationships = current_parent.relationships
#             current_parent.relationships = [[0]]
#
#           else: # need to split actions between pre-utterance and post-utterance
#             new = TreeNode(tmr)
#             current_parent.addChildNode(new)
#             new.disputedWith = current_parent.children[-2]
#             current_parent.children[-2].disputedWith = new
#             for action in current_parent.children[-2].children:
#               current_parent.children[-2].markDisputed(action, True)
#               new.addChildNode(copy.copy(action)) #make a shallow copy of the node
#               new.markDisputed(new.children[-1], True)
#         else:
#           pass #... add more heuristics here
#       else: # Prefix
#         #Check to see if this is directly about part of something by going up the tree.
#         candidate = current_parent
#         while candidate.parent is not None and not about_part_of(tmr, candidate.tmr):
#           candidate = candidate.parent
#         if candidate.parent is not None:
#           current_parent = candidate
#         new = TreeNode(tmr)
#         current_parent.addChildNode(new)
#         if len(input) > i + 1 and not is_action(input[i+1]): # if no actions will be added; shouldn't go out of bounds because this is pre-utterance
#           current_parent = new
#           # go to next thing
#
#     else: # Action
#       output["input"] = []
#       if len(current_parent.children) == 0:
#         current_parent.addChildNode(TreeNode())
#       new = current_parent.children[-1]
#       if len(new.children) > 0: #if that already has children
#         new = TreeNode()
#         current_parent.addChildNode(new)
#       while i < len(input) and is_action(input[i]):
#         output["input"].append(input[i]["action"])
#         new.addAction(input[i])
#         update_knowledge_base_2(input[i])
#         i+=1
#       i-=1 # account for the main loop and the inner loop both incrementing it
#     settle_disputes(root)
#     find_parallels(root)
#     i+=1
#     list = []
#     tree_to_json_format(root, list)
#     if len(steps) > 1:
#       subtract_lists(list, steps[-2]["tree"]) #calculate delta
#     output["tree"] = list
#   return root
#
# #this might not be needed any more?
# def print_tree(tree, spaces=""):
#   if not type(tree) is TreeNode:
#     print(spaces+"Expected TreeNode, got something else? "+str(tree))
#     return
#   if len(tree.name) == 0:
#     print(spaces+"<unnamed node>");
#   else:
#     print(spaces+tree.name);
#   for child in tree.children:
#     print_tree(child, spaces + "  ")
#
# def tree_to_json_format(node, list):
#   output = dict()
#   #output["name"] = str(node.id) + ": " + ("?" if len(node.name)==0 else node.name)
#   output["name"] = node.name
#   output["type"] = node.type
#   output["id"] = node.id
#   output["children"] = []
#   output["relationships"] = node.relationships
#   index = len(list)
#   list.append(output)
#   #if not node.terminal:
#   for child in node.children:
#       output["children"].append(child.id)
#       tree_to_json_format(child, list)
  
