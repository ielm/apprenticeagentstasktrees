from tmrutils import get_name_from_tmr
from tmrutils import same_node

def traverse_tree(node, question_status=None):
  if question_status is None or (True in node.childrenStatus) == question_status:
    yield node
  if not node.terminal:
    for child in node.children:
      yield from traverse_tree(child, question_status)

def update_children_relationships(a,b,mapping):
  for i in range(len(a.relationships)):
    for j in range(len(a.relationships[i])):
      if mapping[i] is None or mapping[j] is None:
        #raise RuntimeError("Attempting to update relationships on incomplete mapping")
        continue
      #print("a.children:
      assert same_node(a.children[i],b.children[mapping[i]])
      assert same_node(a.children[j],b.children[mapping[j]])
      # Set it to 0 if they are different, keep as-is if they are the same. In other words, multiply by (a==b)
      #if a.relationships[i][j] != b.relationships[mapping[i]][mapping[j]]:
        #print("parallelizing %s and %s based on mapping" % (a.children[i].name, a.children[j].name))
        #print("a children:")
        #print([c.name for c in a.children])
        #print("a relationships:")
        #print(a.relationships)
        #print("b children:")
        #print([c.name for c in b.children])
        #print("b relationships:")
        #print(b.relationships)
        #print("\n")
      a.relationships[i][j] *= (a.relationships[i][j] == b.relationships[mapping[i]][mapping[j]])
      b.relationships[mapping[i]][mapping[j]] = a.relationships[i][j]

class TreeNode:
  """A class representing a node in the action hierarchy tree."""  
  id = 0
  
  def __init__(this, tmr = None):
    this.id = TreeNode.id
    TreeNode.id += 1
    this.children = []
    this.childrenStatus = [] # True if child is disputed, false otherwise
    this.parent = None
    this.relationships = []
    this.terminal = False
    this.disputedWith = None
    this.type = "sequential" #Deprecated
    this.setTmr(tmr)
    
  def setTmr(this, tmr):
    this.name = "" if tmr is None else get_name_from_tmr(tmr)
    this.tmr = tmr

  def addChildNode(this, child):
    this.children.append(child)
    this.childrenStatus.append(False)
    child.parent = this
    for row in this.relationships:
      row.append(1)
    this.relationships.append( [-1]*len(this.relationships) + [0] )
    
  def removeChildNode(this, child):
    index = this.children.index(child)
    this.children.pop(index)
    this.childrenStatus.pop(index)
    this.relationships.pop(index)
    for row in this.relationships:
      row.pop(index)
    assert(len(this.children) == len(this.relationships))
  
  def addAction(this, action):
    if len(this.children) == 0:
      this.terminal = True
      #this.type = "leaf"
    if not this.terminal:
      return False
    actionNode = TreeNode()
    actionNode.type = "leaf"
    actionNode.name = action["action"]
    this.addChildNode(actionNode)
    return True    
  
  def markDisputed(this, target, mark):
    if target in this.children:
      this.childrenStatus[this.children.index(target)] = mark
    else:
      raise RuntimeError("No such child")