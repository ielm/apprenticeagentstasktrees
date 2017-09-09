from multiset import Multiset

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
        a.addChildNode(bchild)
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
  #alist must be a subset of a.children
  #blist must be a subset of b.children

  #print("Start child merge!")
  #print("a:")
  #print([node.name for node in alist])
  #print("b:")
  #print([node.name for node in blist])

  #mapping = get_nodes_mapping(alist, blist, same_node)
  mapping = get_children_mapping(a, b, same_node)
  for i in range(len(mapping)): #hacky workaround...
    if a.children[i] not in alist:
      mapping[i] = None
    if mapping[i] is not None and b.children[mapping[i]] not in blist:
      mapping[i] = None
  update_children_relationships(a,b,mapping)
  
  mappingdict = dict()
  for i in range(len(mapping)):
    if mapping[i] is not None:
      mappingdict[a.children[i]] = b.children[mapping[i]]
      mappingdict[b.children[mapping[i]]] = a.children[i]
  
  a_not_mapped = []
  b_not_mapped = blist.copy()
  
  for i in range(len(mapping)):
    if mapping[i] is None:
      if a.children[i] in alist:
        a_not_mapped.append(a.children[i])
    else:
      merge_tree(a.children[i], b.children[mapping[i]])
      b_not_mapped.remove(b.children[mapping[i]])
    
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

    #Dynamic programming to find a subset of leaves.
    S = [(Multiset( (aleaves if maxnode is amax else bleaves) [maxnode]),[])]
    for child in (b_not_mapped if maxnode is amax else a_not_mapped):
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
    end += len(other.children)
    
    if maxnode is bmax:
      #Insert it into the a tree.
      
      a.childrenStatus.insert(pos, False)
      a.relationships.insert(pos, [2] * len(a.children))
      for row in a.relationships:
        row.insert(pos, 2)
      a.children.insert(pos, maxnode)
      
      for i in range(len(a.children)):
        if i == pos:
          a.relationships[i][i] = 0
          continue
          
        if a.children[i] in mappedset:
          #these are about to get removed from a
          #accidentally making them parallel to things could have bad consequences
          continue
      
        parallel = False
        for node in mappedset:
          if a.relationships[i][a.children.index(node)] == 0:
            parallel = True
            break
        if parallel:
          #print("parallelizing %s and %s because first was parallel with child of bmax" % (a.children[i].name, a.children[pos].name))
          a.relationships[i][pos] = 0
          a.relationships[pos][i] = 0
        
        elif a.children[i] in mappingdict and ( (i > pos) != (b.children.index(mappingdict[a.children[i]]) > b.children.index(maxnode)) ):
          #print("parallelizing %s and %s because first was mapped to thing on wrong side of bmax" % (a.children[i].name, a.children[pos].name))
          a.relationships[i][pos] = 0
          a.relationships[pos][i] = 0
          
        elif i < pos:
          a.relationships[i][pos] = 1
          a.relationships[pos][i] = -1
        elif i > end:
          a.relationships[i][pos] = -1
          a.relationships[pos][i] = 1
        else:
          #print("parallelizing %s and %s by default" % (a.children[i].name, a.children[pos].name))
          a.relationships[i][pos] = 0
          a.relationships[pos][i] = 0

      b_not_mapped.remove(bmax)
      for child in mappedset:
        a_not_mapped.remove(child)
        a.removeChildNode(child)

    else:
      #max node is already in the a tree, just update a few relationships
      start = pos
      pos = a.children.index(maxnode)
      #Oh. I have to do things with mappings.
      
      for i in range(len(mapping)):
        if mapping[i] is not None:
          #print("start: %d, end: %d, pos: %d, name: %s" % (start, end, pos, a.children[i].name))
          if (mapping[i] > start and i < pos) or (mapping[i] < end and i > pos):
            #print("parallelizing %s and %s because first was mapped to thing on wrong side of amax" % (a.children[i].name, a.children[pos].name))
            a.relationships[i][pos] = 0
            a.relationships[pos][i] = 0
          else:
            parallel = False
            for node in mappedset:
              if b.relationships[mapping[i]][b.children.index(node)] == 0:
                parallel = True
                break
            if parallel:
              #print("parallelizing %s and %s because first was parallel with child of amax" % (a.children[i].name, a.children[pos].name))
              a.relationships[i][pos] = 0
              a.relationships[pos][i] = 0      
      
      a_not_mapped.remove(amax)
      for child in mappedset:
        b_not_mapped.remove(child)
        b.removeChildNode(child)
    

  #print("Finished a merge")