from multiset import Multiset
from itertools import chain, combinations
from functools import cmp_to_key

from maketree import *

def collect_leaves(node):
  leaves = Multiset()
  if len(node.children) == 0:
    leaves.add(node.name)
  else:
    for child in node.children:
      if len(child.children) == 0:
        leaves.add(child.name)
      else:
        leaves += collect_leaves(child)
  return leaves

powerset = lambda x: {frozenset(i) for i in chain.from_iterable(combinations(x, r) for r in range(len(x)+1))}
  
#Merges b into a. Could be changed.
def merge_tree(a, b):
  #Assumes same_node(a,b) is true
  if a.type == "leaf" and b.type == "leaf":
    return
  
  if (len(b.children) == 1 or b.type == "alternate") and (len(a.children) == 1 or a.type == "alternate"):
    for achild in b.children:
      for bchild in a.children:
        if same_node(a,b):
          merge_tree(achild, bchild)
          break #only break inner loop
      else:
        a.addChild(bchild)
        a.type = "alternate"

  else:# len(a.children) == len(b.children):
    #if a is sequential and b is sequential
    
    #this code should probably be part of thatthing, actually
    if len(a.children) == len(b.children):
      sequential=True
      for i in range(len(a.children)):
        if not same_node(a.children[i], b.children[i]):
          sequential=False
      if sequential:
        for i in range(len(a.children)):
          merge_tree(a.children[i], b.children[i])
        return
    a.type = "parallel"
    thatthing(a.children, b.children, a, b)

#IMPORTANT NOTE: NEW MERGETREE HEURISTICS MAY NOT PRESERVE ORDERING OF CHILDREN

#OH HEY THINGS WITH SUBSTRINGS CAN HAPPEN? to preserve ordering - BUT WHAT IF the thing without intermediates introduces new orderings........

#to change it to preserve order... collect_leaves would also return an adjacency matrix. would have to do permutations instead of combinations for power set. and a lot of shennanigans would be problematic

# The current problem is: Nodes that appear in the a tree but not the b tree are in the output twice

    
def thatthing(alist, blist, a, b):
  #print("START THATTHING")
  #assert(len(alist) > 0)
  #assert(len(blist) > 0)
  #print("alist: " + str(["%d: %s (%d children)" % (node.id, node.name, len(node.children)) for node in alist])) 
  #print("blist: " + str(["%d: %s (%d children)" % (node.id, node.name, len(node.children)) for node in blist])) 

  mapping = get_nodes_mapping(alist, blist, same_node)
  update_children_relationships(a,b,mapping)
  
  #print("mapping: "+ str(mapping))
  
  a_not_mapped = []
  b_not_mapped = blist.copy()
  
  for i in range(len(mapping)):
    if mapping[i] is None:
      a_not_mapped.append(alist[i])
    else:
      merge_tree(alist[i], blist[mapping[i]])
      b_not_mapped.remove(blist[mapping[i]])
  
  if not ( (len(a_not_mapped)==0) == (len(b_not_mapped)==0) ): # This is true unless one of the lists is a subset of the other. That really shouldn't happen.
    #print("Flagrant system error. problem = very yes")
    #print(str(a_not_mapped))
    #print(str(b_not_mapped))
    #print_tree(b_not_mapped[0])
    assert(False)
  if len(a_not_mapped) > 0:
    thisthing(a_not_mapped, b_not_mapped, a, b)
  
def thisthing(alist, blist, aparent, bparent):
  #print("START THISTHING")
  aleaves = dict()
  for child in alist:
    aleaves[child] = collect_leaves(child)    
    
  bleaves = dict()
  for child in blist:
    bleaves[child] = collect_leaves(child)
    
  while len(aleaves.keys()) + len(bleaves.keys()) > 0:
    amax = max(aleaves.keys(), key = lambda x: 0 if len(x.children)==0 else len(aleaves[x]) )
    bmax = max(bleaves.keys(), key = lambda x: 0 if len(x.children)==0 else len(bleaves[x]) )
    #assert(len(amax.children)+len(bmax.children) > 0)
    if len(aleaves[amax]) > len(bleaves[bmax]) or len(bmax.children) == 0:
      #print("amax has %d leaves" % len(aleaves[amax]))
      #childset = magically_get_set(amax, bleaves.keys()) # get a set of things from b whose leaves add up to amax
      
      candidates = set()
      for bchild in bleaves.keys():
        if bleaves[bchild] <= aleaves[amax]:
          candidates.add(bchild)
          
      childset = None
      for candidateset in powerset(candidates):
        union = Multiset()
        for thing in candidateset:
          union += bleaves[thing]
        if union == aleaves[amax]:
          childset = candidateset
          break
          
      for node in childset:
        del bleaves[node]
        bparent.removeChildNode(node)
      del aleaves[amax]
      aparent.addChildNode(amax)
            
      thatthing(amax.children, list(childset), amax, bparent)
      #amax is already a child of aparent; bparent doesn't really matter at this point.
      #aparent.addChildNode(amax)
      bparent.addChildNode(amax) #this is probably why the duplicate nodes
      #probably just prune the b tree to avoid complications?
      
    else:
      #print("bmax has %d leaves" % len(bleaves[bmax]))
      #assert(len(bmax.children) > 0)
      candidates = set()
      for achild in aleaves.keys():
        if aleaves[achild] <= bleaves[bmax]:
          candidates.add(achild)
          
      childset = None
      for candidateset in powerset(candidates):
        union = Multiset()
        for thing in candidateset:
          union += aleaves[thing]
        if union == bleaves[bmax]:
          childset = candidateset
          break
      
      for node in childset:
        del aleaves[node]
        aparent.removeChildNode(node)
      del bleaves[bmax]
      
      aparent.addChildNode(bmax)
      #bparent.addChildNode(bmax) #the node is in both trees now. yes, this is a problem. no, i can't think of anything better.
      
      thatthing(bmax.children, list(childset), bmax, aparent)
      
      #add bmax (or copies of it) as child of both aparent and bparent
      #also remove the things that are now children of bmax from aparent

