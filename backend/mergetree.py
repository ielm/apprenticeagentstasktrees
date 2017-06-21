from maketree import *

#Merges b into a. Could be changed.
def merge_tree(a, b):
  #Assumes same_node(a,b) is true
  if a.type == "leaf" and b.type == "leaf":
    return
  
  if len(a.children) == 1 and len(b.children) == 1:
    # Trying to merge two one-child nodes will cause an error if the nodes are different,
    # so handle that case separately
    if same_node(a.children[0], b.children[0]):
      merge_tree(a.children[0], b.children[0])
      return
    else:
      a.type = "alternate"
      a.addChildNode(b.children[0])
  elif len(a.children) == len(b.children):
    #if a is sequential and b is sequential
    sequential=True
    for i in range(len(a.children)):
      if not same_node(a.children[i], b.children[i]):
        sequential=False
    if sequential:
      for i in range(len(a.children)):
        merge_tree(a.children[i], b.children[i])
    else:
      a.type = "parallel"
      mapping = get_children_mapping(a,b, same_node)
      #TODO IMPORTANT Changes to get_children_mapping may cause this to not work any more.
      update_children_relationships(a,b,mapping)
      for i in range(len(a.children)):
        merge_tree(a.children[i], b.children[mapping[i]])
  elif (len(b.children) == 1 or b.type == "alternate") and (len(a.children) == 1 or a.type == "alternate"):
    a.type = "alternate"
    for achild in b.children:
      for bchild in a.children:
        if same_node(a,b):
          merge_tree(achild, bchild)
          break #only break inner loop
      else:
        a.addChild(bchild)
  else:
    raise RuntimeError("Cannot merge trees!") # again, will trigger alternatives situation eventually
