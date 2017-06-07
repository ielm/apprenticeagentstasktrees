import json
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
    if "THEME1" in event:
      output += " AND "+tmr[event["THEME1"]]["concept"]
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
    return True
  if node1.tmr is None or node2.tmr is None:
    return False
  return same_main_event(node1.tmr, node2.tmr)
  
def about_part_of(tmr1, tmr2):
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
    this.hasQuestionedDescendants = False
    this.questionedWith = None
    this.tmr = None
    this.type = "sequential" #Deprecated
  
  def addChildNode(this, child):
    this.children.append(child)
    child.parent = this
    for row in this.relationships:
      row.append(1)
    this.relationships.append( [-1]*len(this.relationships) + [0] )
  
  def addAction(this, action):
    if len(this.children) == 0:
      this.terminal = True
      this.type = "leaf"
    if not this.terminal:
      return False
    this.children.append(action)
    this.childrenStatus.append(False)
    for row in this.relationships:
      row.append(1)
    this.relationships.append( [-1]*len(this.relationships) + [0] )
    return True
  
  def markQuestioned(this, target, mark):
    for i in range(len(this.children)):
      if this.children[i] == target:
        this.childrenStatus[i] = mark;
        break    
    this.setQuestionedDescendants(mark)        

  def setQuestionedDescendants(this, hqd):
    if hqd:
      this.hasQuestionedDescendants = True
      if not this.parent is None:
        this.parent.setQuestionedDescendants(True)
    else: #check to make sure it doesn't have other questioned descendants
      for i in this.childrenStatus:
        if i == True:
          return
      this.hasQuestionedDescendants = False
      if not this.parent is None:
        this.parent.setQuestionedDescendants(False)

  
def disambiguate(node):
  # TODO find same-main-event nodes and parallelize their children if possible
  for question in traverse_tree(node, True):
    for answer in traverse_tree(node, False):
      if answer.tmr is None:
        continue
      if same_main_event(question.tmr, answer.tmr):
        # TODO ALLOW FOR PARALLEL
        other = question.questionedWith
        for action in answer.children:
          other.children.remove(action)
        for action in other.children:
          question.children.remove(action)
        other.questionedWith = None
        question.questionedWith = None
        other.childrenStatus = [False]*len(other.children)
        question.childrenStatus = [False]*len(question.children)
        other.setQuestionedDescendants(False)
        question.setQuestionedDescendants(False)
        

def traverse_tree(node, question_status):
  if node.terminal:
    if node.hasQuestionedDescendants == question_status:
      yield node
    return
  else:
    for child in node.children:
      yield from traverse_tree(child, question_status)
        
def construct_tree(input, steps):
  root = TreeNode()
  current = root
  i=0
  while i < len(input): # For each input token
    if is_utterance(input[i]):
      tmr = input[i]["results"][0]["TMR"]
      if find_main_event(tmr) is None: #phatic utterances etc. just get skipped for now
        i+=1
        continue
      elif is_postfix(input[i]):
        afile = open("afile", "w")
        afile.write(str(current.children[-1].tmr))
        afile.close()
        if (not current.children[-1].tmr is None) and about_part_of(current.children[-1].tmr, tmr):
          new = TreeNode()
          current.addChildNode(new)
          new.name = get_name_from_tmr(tmr)
          new.tmr = tmr
          
          current.children[-2].parent = new.id
          new.children.append(current.children[-2])
          
          j = -3
          while about_part_of(current.children[j].tmr, tmr):
            current.children[j].parent = new.id
            new.children.append(current.children[j])
            j -= 1
            
          #new.relationships = [ row[j+1:] for row in current.relationships[j+1:] ]
          #current.relationships = [ row[:j+1] for row in current.relationships[:j+1] ]
            
          for child in new.children:
            current.children.remove(child)
            
        elif i > 0 and is_action(input[i-1]): #If it was preceded by actions
          if current.children[-1].name == "": # if their node is unnamed,
            current.children[-1].name = get_name_from_tmr(tmr)#mark that node with this utterance
            current.children[-1].tmr = tmr
          else: # need to split actions between pre-utterance and post-utterance
            new = TreeNode()
            current.addChildNode(new)
            new.name = get_name_from_tmr(tmr)
            new.tmr = tmr
            for action in current.children[-2].children:
              new.addAction(action)
              new.markQuestioned(action, True)
              current.children[-2].markQuestioned(action, True)
              new.questionedWith = current.children[-2]
              current.children[-2].questionedWith = new
        else:
          pass #... add more heuristics here
      else: # Prefix
        new = TreeNode()
        current.addChildNode(new)
        new.name = get_name_from_tmr(tmr)
        new.tmr = tmr
        while i+1 < len(input) and is_action(input[i+1]):
          new.addAction(input[i+1])
          i+=1
        if not new.terminal: # if no actions were added
          current = new
          # go to next thing
        
    else: # Action
      new = TreeNode()
      current.addChildNode(new)
      while i < len(input) and is_action(input[i]):
        new.addAction(input[i])
        i+=1
      i-=1 # account for the main loop and the inner loop both incrementing it
    disambiguate(root)
    i+=1
    list = []
    tree_to_json_format(root, list)
    steps.append(list)
  return root
  
def get_children_mapping(a,b):
  mapping = [-1]*len(a.children)
  revmapping = [-1]*len(b.children)
  for i in range(len(a.children)):
    j = 0
    while revmapping[j] != -1 or not same_node(a.children[i], b.children[j]):
      j += 1
      if j >= len(b.children):
        raise RuntimeError("Cannot merge trees!")
        # TODO in the future, this will trigger some kind of alternatives situation
    mapping[i] = j
    revmapping[j] = i
  return mapping

def update_children_relationships(a,b,mapping):
  debugfile = open("debugfile"+a.name, "w")
  debugfile.write(str(mapping))
  debugfile.write(str(a.relationships))
  debugfile.write(str(b.relationships))
  for i in range(len(a.relationships)):
    for j in range(len(a.relationships[i])):
      # Set it to 0 if they are different, keep as-is if they are the same. In other words, multiply by (a==b)
      a.relationships[i][j] *= (a.relationships[i][j] == b.relationships[mapping[i]][mapping[j]])
     
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
      mapping = get_children_mapping(a,b)
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
  if tree.terminal:
    print(spaces+"  (%d actions)" % (len(tree.children)))
    for i in range(len(tree.children)):
      if type(tree.children[i]) is TreeNode:
        print(spaces + "  Branch in node marked terminal?")
        print_tree(tree.children[i], spaces+"  ")
      else:
        print(spaces+"  ACTION:"+tree.children[i]['action']+(" (questioned)" if tree.childrenStatus[i] else "") )
  else:
    for child in tree.children:
      print_tree(child, spaces + "  ")

def tree_to_json_format(node, list):
  output = dict()
  output["name"] = node.name
  output["type"] = node.type
  output["id"] = node.id
  output["children"] = []
  #output["relationships"] = node.relationships
  index = len(list)
  list.append(output)
  if not node.terminal:
    for child in node.children:
      output["children"].append(list[tree_to_json_format(child, list)]["id"])
      list[output["children"][-1]]["parent"] = list[index]["id"]
  return index
  
app = Flask(__name__)

#current_tree = None

@app.route('/alpha/maketree', methods=['POST'])
@cross_origin()
def start():
  if not request.json:
    abort(400)
  steps = []
  current_tree = construct_tree(request.json, steps)
  #global current_tree
  #if current_tree is None:
  #  current_tree = new_tree
  #else:
  #  merge_tree(current_tree, new_tree)
  #list = []
  #tree_to_json_format(current_tree, list)
  return json.dumps(steps)

if __name__ == '__main__':
  app.run(debug=True, port=5000)
