from mini_ontology import ontology

#this currently just returns the first event it finds
def find_main_event(tmr):
  if tmr is None:
    return None
  for item in tmr:
    if type(tmr[item]) is dict and "is-in-subtree" in tmr[item] and tmr[item]["is-in-subtree"] == "EVENT":
      return tmr[item]
  return None
#  raise RuntimeError("Cannot find main event: No events in given TMR: "+str(tmr))

#formats an utterance into a node name
def get_name_from_tmr(tmr):
  event = find_main_event(tmr)
  output = event["concept"]
  if "THEME" in event:
    output += " "+tmr[event["THEME"]]["concept"]
    if "CARDINALITY" in tmr[event["THEME"]] and tmr[event["THEME"]]["CARDINALITY"][0] == ">":
      output += "S"
    if "THEME-1" in event:
      output += " AND "+tmr[event["THEME-1"]]["concept"]
  if "INSTRUMENT" in event:
    output += " WITH "+tmr[event["INSTRUMENT"]]["concept"]
  return output

#determines whether a given token is utterance or action
def is_utterance(token):
  return type(token) is dict and 'results' in token and 'sentence' in token

def is_action(token):
  return not is_utterance(token)
  
#determines whether a given utterance is prefix or postfix
#TODO: phatic utterances? infix utterances?
def is_postfix(utterance):
  # Assumes there is only one TMR for each utterance
  tmr = utterance["results"][0]["TMR"]
  return find_main_event(tmr)["TIME"][0] == "<"
  
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
#  if node1.tmr is None and node2.tmr is None:
    return node1.name == node2.name
#  if node1.tmr is None or node2.tmr is None:
#    return False
#  return same_main_event(node1.tmr, node2.tmr)
  
def is_finality_statement(tmr):
  for item in tmr:
    if type(tmr[item]) is dict and "concept" in tmr[item] and tmr[item]["concept"] == "ALL":
      return True
  return False

def about_part_of(tmr1, tmr2):
  if tmr1 is None or tmr2 is None:
    return False
  event1 = find_main_event(tmr1)
  event2 = find_main_event(tmr2)
  if event1 is None or event2 is None:
    return False
  if not ("THEME" in event1 and "THEME" in event2):
    return False
    
  concept1 = tmr1[event1["THEME"]]["concept"]
  concept2 = tmr2[event2["THEME"]]["concept"]
  
  return concept1 in ontology[concept2]["HAS-OBJECT-AS-PART"]["SEM"] or (
      "CARDINALITY" in tmr2[event2["THEME"]] and concept1==concept2 and tmr2[event2["THEME"]]["CARDINALITY"][0]=='>' # one is the plural of the other
  )
      
  #TODO make this prioritize DEFAULT over SEM
  
def subtract_lists(list1, list2):
  for node in list2:
    if node in list1:
      list1.remove(node)


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
