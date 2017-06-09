import json
import copy
from flask import Flask
from flask import request
from flask import abort
from flask_cors import cross_origin
from mini_ontology import ontology

#TODO this currently just returns the first event it finds
def find_main_event(tmr):
  for item in tmr:
    if type(tmr[item]) is dict and "is-in-subtree" in tmr[item] and tmr[item]["is-in-subtree"] == "EVENT":
      return tmr[item]
  return None
#  raise RuntimeError("Cannot find main event: No events in given TMR: "+str(tmr))

#determines whether a given token is utterance or action
def is_utterance(token):
  return type(token) is dict and 'results' in token

def is_action(token):
  return not is_utterance(token)
  
#determines whether a given utterance is prefix or postfix
#TODO: phatic utterances? infix utterances?
def is_postfix(utterance):
  # Assumes there is only one TMR for each utterance
  tmr = utterance["results"][0]["TMR"]
  return find_main_event(tmr)["TIME"][0] == "<"
  
#formats an utterance into a node name
def get_name_from_tmr(tmr):
  event = find_main_event(tmr)
  output = event["concept"]
  if "THEME" in event:
    output += " "+tmr[event["THEME"]]["concept"]
    if "THEME-1" in event:
      output += " AND "+tmr[event["THEME-1"]]["concept"]
  if "INSTRUMENT" in event:
    output += " WITH "+tmr[event["INSTRUMENT"]]["concept"]
  return output
  
def same_main_event(tmr1, tmr2):
  event1 = find_main_event(tmr1)
  event2 = find_main_event(tmr2)
  if event1["concept"] != event2["concept"]:
    return False
  if "AGENT" in event1 and "AGENT" in event2 and tmr1[event1["AGENT"]]["concept"] != tmr2[event2["AGENT"]]["concept"]:
    return False
  if ("THEME" in event1) != ("THEME" in event2):
    return false
  if "THEME" in event1 and "THEME" in event2 and tmr1[event1["THEME"]]["concept"] != tmr2[event2["THEME"]]["concept"]:
    return False
  if "INSTRUMENT" in event1 and "INSTRUMENT" in event2 and tmr1[event1["INSTRUMENT"]]["concept"] != tmr2[event2["INSTRUMENT"]]["concept"]:
    return False
  return True
  
def same_node(node1, node2):
  if node1.tmr is None and node2.tmr is None:
    return node1.name == node2.name
  if node1.tmr is None or node2.tmr is None:
    return False
  return same_main_event(node1.tmr, node2.tmr)
  
def about_part_of(tmr1, tmr2):
  if tmr1 is None or tmr2 is None:
    return False
  event1 = find_main_event(tmr1)
  event2 = find_main_event(tmr2)
  if event1 is None or event2 is None:
    return False
  if not ("THEME" in event1 and "THEME" in event2):
    return False
  
  return tmr1[event1["THEME"]]["concept"] in ontology[tmr2[event2["THEME"]]["concept"]]["HAS-OBJECT-AS-PART"]["SEM"]
  
class TreeNode:
  """A class representing a node in the action hierarchy tree."""  
  id = 0
  
  def __init__(this):
    this.id = TreeNode.id
    TreeNode.id += 1
    this.children = []
    this.childrenStatus = [] # True if child is questioned, false otherwise
                             # leaving it like this because non-terminal children 
                             # could also be questioned
    this.parent = None # put a parent pointer here; root has None or whatever; recurse up the tree on markquestioned for hqd, add method for adding children
    this.relationships = []
    this.name = ""
    this.terminal = False
    this.questionedWith = None
    this.tmr = None
    this.type = "sequential" #Deprecated
  
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
    
  
  def markQuestioned(this, target, mark):
    if target in this.children:
      this.childrenStatus[this.children.index(target)] = mark
    else:
      raise RuntimeError("No such child")    
  
def disambiguate(tree, othertree=None):
  if othertree is None:
    othertree = tree
  for question in traverse_tree(tree, True):
    for answer in traverse_tree(othertree, False):
      if answer.tmr is None or question.tmr is None:
        continue
      if same_main_event(question.tmr, answer.tmr):
        #NOTE: this assumes that the questioned children are not interdependent
        other = question.questionedWith
        
        mapping = get_children_mapping(answer, other, same_node)
        
        #DEBUG
        somefile = open("somefile", "w")
        for child in answer.children:
          somefile.write(child.name+"\n")
        somefile.write(str(mapping)+"\n")
        for child in other.children:
          somefile.write(child.name+"\n")
        somefile.close()
        #GUBED
        
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
        
        other.questionedWith = None
        question.questionedWith = None
        other.childrenStatus = [False]*len(other.children)
        question.childrenStatus = [False]*len(question.children)
                
  for child1 in traverse_tree(tree, False):
    for child2 in traverse_tree(othertree, False):
      if child1 is child2:
        continue
      if child1.tmr is None or child2.tmr is None:
        continue
      if same_main_event(child1.tmr, child2.tmr):
        mapping = get_children_mapping(child1, child2, same_node)
        update_children_relationships(child1, child2, mapping)
        

def traverse_tree(node, question_status=None):
  if question_status is None or (True in node.childrenStatus) == question_status:
    yield node
  if not node.terminal:
    for child in node.children:
      yield from traverse_tree(child, question_status)
        
def construct_tree(input, steps):
  root = TreeNode()
  current = root
  i=0
  while i < len(input): # For each input token
    output = dict()
    steps.append(output)
    if is_utterance(input[i]):
      output["input"] = input[i]["sentence"]
      tmr = input[i]["results"][0]["TMR"]
      if find_main_event(tmr) is None: #phatic utterances etc. just get skipped for now
        i+=1
        steps.pop() # no output for this iteration
        continue
      elif is_postfix(input[i]):
        if (not current.children[-1].tmr is None) and about_part_of(current.children[-1].tmr, tmr):
          while about_part_of(current.tmr, tmr) and not current.parent is None:
            current = current.parent
          
          #Mark some of the preceding nodes as children of a new node
          new = TreeNode()
          new.name = get_name_from_tmr(tmr)
          new.tmr = tmr
          
          j = -2
          while j > -len(current.children) and about_part_of(current.children[j].tmr, tmr):
            j -= 1
          
          j += 1 #to make future things simpler          
          
          if j > -len(current.children) + 1:
            current.questionedWith = new
            new.questionedWith = current
          
          for child in current.children[:j]:
            new.addChildNode(copy.copy(child))
            current.markQuestioned(child, True)
            new.markQuestioned(new.children[-1], True)
            
          for child in current.children[j:]:
            new.addChildNode(child)
            child.parent = new
                    
          #don't update relationships until done adding nodes to new
          new.relationships = copy.deepcopy(current.relationships)
          current.relationships = [ row[:j] for row in current.relationships[:j] ]
          
          assert(new.children[-1] is current.children[-1])
          
          for child in new.children[j:]:
            current.children.remove(child)
            current.childrenStatus.pop()
                    
          current.addChildNode(new)
          #And then add the rest of the nodes as questioned between this and its parent?
          #... actually, what if this node is neither a sibling nor a child of current but rather its parent?
            
        elif i > 0 and is_action(input[i-1]): #If it was preceded by actions
          if current.children[-1].name == "": # if their node is unnamed,
            current.children[-1].name = get_name_from_tmr(tmr)#mark that node with this utterance
            current.children[-1].tmr = tmr
          else: # need to split actions between pre-utterance and post-utterance
            new = TreeNode()
            current.addChildNode(new)
            new.name = get_name_from_tmr(tmr)
            new.tmr = tmr
            new.questionedWith = current.children[-2]
            current.children[-2].questionedWith = new
            for action in current.children[-2].children:
              current.children[-2].markQuestioned(action, True)
              new.addChildNode(copy.copy(action)) #make a shallow copy of the node
              new.markQuestioned(new.children[-1], True)
        else:
          pass #... add more heuristics here
      else: # Prefix
        new = TreeNode()
        current.addChildNode(new)
        new.name = get_name_from_tmr(tmr)
        new.tmr = tmr
        if not is_action(input[i+1]): # if no actions will be added; shouldn't go out of bounds because this is pre-utterance
          current = new
          # go to next thing
        
    else: # Action
      output["input"] = []      
      new = current.children[-1]
      if len(new.children) > 0: #if that already has children
        new = TreeNode()
        current.addChildNode(new)
      while i < len(input) and is_action(input[i]):
        output["input"].append(input[i]["action"])
        new.addAction(input[i])
        i+=1
      i-=1 # account for the main loop and the inner loop both incrementing it
    disambiguate(root)
    i+=1
    list = []
    tree_to_json_format(root, list)
    if len(steps) > 1:
      subtract_lists(list, steps[-2]["tree"]) #calculate delta
    output["tree"] = list
  return root
  
def get_children_mapping(a,b, comparison): #There's probably a standard function for this
  mapping = [None]*len(a.children)
  revmapping = [None]*len(b.children)
  for i in range(len(a.children)):
    j = 0
    while not (revmapping[j] is None and comparison(a.children[i], b.children[j])):
      j += 1
      if j >= len(b.children):
          break
        # raise RuntimeError("Cannot merge trees!")
        # TODO in the future, this will trigger some kind of alternatives situation
    else:
      mapping[i] = j
      revmapping[j] = i
  return mapping

def update_children_relationships(a,b,mapping):
  for i in range(len(a.relationships)):
    for j in range(len(a.relationships[i])):
      if mapping[i] is None or mapping[j] is None:
        raise RuntimeError("Attempting to update relationships on incomplete mapping")
      # Set it to 0 if they are different, keep as-is if they are the same. In other words, multiply by (a==b)
      a.relationships[i][j] *= (a.relationships[i][j] == b.relationships[mapping[i]][mapping[j]])
      b.relationships[mapping[i]][mapping[j]] = a.relationships[i][j]
     
#Merges b into a. Could be changed.
def merge_tree(a, b):
  # TODO replace children.append with addChild
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
      a.children.append(b.children[0])
  if len(a.children) == len(b.children):
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
    for child in b.children:
      a.children.append(child)
  else:
    raise RuntimeError("Cannot merge trees!") # again, will trigger alternatives situation eventually

# TODO this might not be needed any more?
def print_tree(tree, spaces=""):
  if not type(tree) is TreeNode:
    print(spaces+"Expected TreeNode, got something else? "+str(tree))
    return
  if len(tree.name) == 0:
    print(spaces+"<unnamed node>");
  else:
    print(spaces+tree.name);
  for child in tree.children:
    print_tree(child, spaces + "  ")

def subtract_lists(list1, list2):
  for node in list2:
    if node in list1:
      list1.remove(node)

def tree_to_json_format(node, list):
  output = dict()
  output["name"] = node.name
  output["type"] = node.type
  output["id"] = node.id
  output["children"] = []
  output["relationships"] = node.relationships
  index = len(list)
  list.append(output)
  #if not node.terminal:
  for child in node.children:
      output["children"].append(child.id)
      tree_to_json_format(child, list)
  
app = Flask(__name__)

current_tree = None

@app.route('/alpha/maketree', methods=['POST'])
@cross_origin()
def start():
  if not request.json:
    abort(400)
  steps = []
  new_tree = construct_tree(request.json, steps)
  global current_tree
  if current_tree is None:
    current_tree = new_tree
  else:
    disambiguate(current_tree, new_tree)
    #merge_tree(current_tree, new_tree)
  list = []
  tree_to_json_format(current_tree, list)
  return json.dumps(list)

if __name__ == '__main__':
  app.run(debug=True, port=5000)
