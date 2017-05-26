import json

#TODO this currently just returns the first event it finds
def find_main_event(tmr):
  for item in tmr:
    if type(tmr[item]) is dict and "is-in-subtree" in tmr[item] and tmr[item]["is-in-subtree"] == "EVENT":
      return tmr[item]
  return False
#  raise RuntimeError("Cannot find main event: No events in given TMR: "+str(tmr))

def has_no_events(utterance):
  return find_main_event(utterance["results"][0]["TMR"]) is False

#determines whether a given token is utterance or action
def is_utterance(token):
  return type(token) is dict and 'results' in token

def is_action(token):
  #return False
  return not is_utterance(token)
  
#determines whether a given utterance is prefix or postfix
#TODO: phatic utterances? infix utterances?
#TODO: Currently, just checks for the presence of any past-tense event
#   in the entire TMR. This is... suboptimal.
#   Is there a way to determine the "main" verb of a TMR?
def is_postfix(utterance):
  # Assumes there is only one TMR for each utterance
  tmr = utterance["results"][0]["TMR"]
  return find_main_event(tmr)["TIME"][0] == "<"
  
#formats an utterance into a node name
def get_name_from_utterance(utterance):
  return utterance["sentence"]
  
def same_main_event(tmr1, tmr2):
  event1 = find_main_event(tmr1)
  event2 = find_main_event(tmr2)
  if event1["concept"] != event2["concept"]:
    return False
  if "AGENT" in event1:
    if not "AGENT" in event2:
      return False
    if tmr1[event1["AGENT"]]["concept"] != tmr2[event2["AGENT"]]["concept"]:
      return False
  if "THEME" in event1:
    if not "THEME" in event2:
      return False
    if tmr1[event1["THEME"]]["concept"] != tmr2[event2["THEME"]]["concept"]:
      return False
  if "INSTRUMENT" in event1:
    if not "INSTRUMENT" in event2:
      return False
    if tmr1[event1["INSTRUMENT"]]["concept"] != tmr2[event2["INSTRUMENT"]]["concept"]:
      return False
  # TODO if one is missing an agent or theme or instrument, that doesn't discount them from being the same
  return True
  

class TreeNode:
  """A class representing a node in the action hierarchy tree."""
  
  def __init__(this):
    this.children = []
    this.childrenStatus = [] # True if child is questioned, false otherwise
                             # leaving it like this because non-terminal children 
                             # could also be questioned
    this.parent = None # put a parent pointer here; root has None or whatever; recurse up the tree on markquestioned for hqd, add method for adding children
    this.name = ""
    this.terminal = False
    this.hasQuestionedDescendants = False
    this.questionedWith = None
    this.tmr = None
  
  def addChildNode(this, child):
    this.children.append(child)
    child.parent = this
  
  def addAction(this, action):
    if len(this.children) == 0:
      this.terminal = True
    if not this.terminal:
      return False
    this.children.append(action)
    this.childrenStatus.append(False)
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
  for question in traverse_tree(node, True):
    for answer in traverse_tree(node, False):
      if answer.tmr is None:
        continue
      if same_main_event(question.tmr, answer.tmr):
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
        
def construct_tree(input):
  root = TreeNode()
  current = root
  i=0
  while i < len(input): # For each input token
    if is_utterance(input[i]):
      if has_no_events(input[i]): #phatic utterances etc. just get skipped for now
        i+=1
        continue
      elif is_postfix(input[i]):
        if i > 0 and is_action(input[i-1]): #If it was preceded by actions
          if current.children[-1].name == "": # if their node is unnamed,
            current.children[-1].name = get_name_from_utterance(input[i])#mark that node with this utterance
            current.children[-1].tmr = input[i]["results"][0]["TMR"]
          else: # need to split actions between pre-utterance and post-utterance
            new = TreeNode()
            current.addChildNode(new)
            new.name = get_name_from_utterance(input[i])
            new.tmr = input[i]["results"][0]["TMR"]
            for action in current.children[-2].children:
              new.addAction(action)
              new.markQuestioned(action, True)
              current.children[-2].markQuestioned(action, True)
              new.questionedWith = current.children[-2]
              current.children[-2].questionedWith = new
        else:
          pass #There will be things to do here later...
      else: # Prefix
        new = TreeNode()
        current.addChildNode(new)
        new.name = get_name_from_utterance(input[i])
        new.tmr = input[i]["results"][0]["TMR"]
        while i+1 < len(input) and is_action(input[i+1]):
          new.addAction(input[i+1])
          i+=1
        if not new.terminal: # if no actions were addee
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
  return root
    


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
  
def gettestdata():
  infile = open("test1.json", "r")
  testdata = json.load(infile)
  return testdata
  
def start():
  testdata = gettestdata()
  tree = construct_tree(testdata)
  print_tree(tree)
  return tree