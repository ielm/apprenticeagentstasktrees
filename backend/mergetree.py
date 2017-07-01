from multiset import Multiset
from itertools import chain, combinations

from maketree import *

def collect_leaves(node):
  leaves = []#Multiset()
  if len(node.children) == 0:
    leaves.append(node.name)
  else:
    for child in node.children:
      if len(child.children) == 0:
        leaves.append(child.name)
      else:
        leaves += collect_leaves(child)
  return leaves
  
#Merges b into a. Could be changed to construct a third tree.
def merge_tree(a, b):
  #Assumes same_node(a,b) is true
  if a.type == "leaf" and b.type == "leaf":
    return
  
  if (len(b.children) == 1 or b.type == "alternate") and (len(a.children) == 1 or a.type == "alternate"):
    for bchild in b.children:
      for achild in a.children:
        if same_node(achild, bchild) and Multiset(collect_leaves(achild)) == Multiset(collect_leaves(bchild)):
          merge_tree(achild, bchild)
          break #only break inner loop
      else:
        a.addChildNode(achild)
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
    merge_children(a, b, a.children, b.children)

    
def merge_children(a, b, alist, blist):
  #print("Start child merge!")
  #print("a:")
  #print([node.name for node in alist])
  #print("b:")
  #print([node.name for node in blist])

  mapping = get_nodes_mapping(alist, blist, same_node)
  update_children_relationships(a,b,mapping)
  
  mappingdict = dict()
  for i in range(len(mapping)):
    if mapping[i] is not None:
      mappingdict[alist[i]] = blist[mapping[i]]
      mappingdict[blist[mapping[i]]] = alist[i]
  
  a_not_mapped = []
  b_not_mapped = blist.copy()
  
  for i in range(len(mapping)):
    if mapping[i] is None:
      a_not_mapped.append(alist[i])
    else:
      merge_tree(alist[i], blist[mapping[i]])
      b_not_mapped.remove(blist[mapping[i]])
    
  aleaves = dict()
  for child in a_not_mapped:
    aleaves[child] = collect_leaves(child)    
    
  bleaves = dict()
  for child in b_not_mapped:
    bleaves[child] = collect_leaves(child)
    
  while len(a_not_mapped) + len(b_not_mapped) > 0:
    #print("Iteration of while loop!")
    #print("a not mapped:")
    #print([node.name for node in a_not_mapped])
    #print("b not mapped:")
    #print([node.name for node in b_not_mapped])
    
    amax = max(a_not_mapped, key = lambda x: 0 if len(x.children)==0 else len(aleaves[x]) )
    bmax = max(b_not_mapped, key = lambda x: 0 if len(x.children)==0 else len(bleaves[x]) )
    
    maxnode = bmax
    other = a
    otherleaves = aleaves
    if len(aleaves[amax]) > len(bleaves[bmax]) or len(bmax.children) == 0:
      maxnode = amax
      other = b
      otherleaves = bleaves
    
    #Let X be the unmerged child with the most leaves (wlog say it is from A)
    #then do a dynamic programming thing:
    S = [(Multiset( (aleaves if maxnode is amax else bleaves) [maxnode]),[])]
    for child in (b_not_mapped if maxnode is amax else a_not_mapped):
      #Dynamic programming to find a subset of leaves.
      #This was a fun line of code to write.
      S.append( min( [S[-1]] + [(s[0]-set(otherleaves[child]),s[1]+[child]) for s in S if s[0] >= set(otherleaves[child])], key = lambda x: len(x[0]) ) )
      #pair of (smallest possible subset of X's leaves after subtracting some things in the range b1...bi, set of those things)
      if len(S[-1][0]) == 0:
        break
    else:
      raise RuntimeError("Cannot merge trees: no child set found corresponding to node "+maxnode.name+"; unmapped nodes remaining: %d\n" % len(S[-1][0]) + str(S)+"; candidates are: "+str([node.name for node in (b_not_mapped if maxnode is amax else a_not_mapped)]))
      
    mappedset = S[-1][1]
    
    merge_children(maxnode, other, maxnode.children, mappedset)
    
    pos = 0
    while not other.children[pos] in mappedset:
      pos += 1
    
    end = -1
    while not other.children[end] in mappedset:
      end -= 1
    
    other.childrenStatus.insert(pos, False)
    other.relationships.insert(pos, [2] * len(other.children))
    for row in other.relationships:
      row.insert(pos, 2)
    other.children.insert(pos, maxnode)
    
    for i in range(len(other.children)):
      if i == pos:
        other.relationships[i][i] = 0
        continue
      
      parallel = False
      for node in mappedset:
        if other.relationships[i][other.children.index(node)] == 0:
          parallel = True
          break
      if parallel:
        print("A node was parallel with a child: "+other.children[i].name)
        other.relationships[i][pos] = 0
        other.relationships[pos][i] = 0
      
      #Get the thing that it is mapped to in the opposite tree
      #If this one's relationship to pos is opposite that one's relationship to the original location of end,
      #or if that is parallel to something in mappedset,
      #then parallelize.
      
      elif other.children[i] in mappingdict and ( (i > pos) != (maxnode.parent.children.index(mappingdict[other.children[i]]) > maxnode.parent.children.index(maxnode)) ):
        other.relationships[i][pos] = 0
        other.relationships[pos][i] = 0
        
      elif i < pos:
        other.relationships[i][pos] = 1
        other.relationships[pos][i] = -1
      elif i > end + len(other.children):
        other.relationships[i][pos] = -1
        other.relationships[pos][i] = 1
      else:
        print("A node was interleaved: "+other.children[i].name)
        other.relationships[i][pos] = 0
        other.relationships[pos][i] = 0
        
    if maxnode is amax:
      a_not_mapped.remove(amax)
      for child in mappedset:
        b_not_mapped.remove(child)
        b.removeChildNode(child)
    else:
      b_not_mapped.remove(bmax)
      for child in mappedset:
        a_not_mapped.remove(child)
        a.removeChildNode(child)
  #print("Finished a merge")