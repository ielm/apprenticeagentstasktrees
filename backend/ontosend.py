#ontosend.py

import pymongo

import treenode
from tmrutils import *

onto = pymongo.MongoClient().after.inventory

def event_name_to_concept_name(name):
  return name.lower().replace(" ","-")

def add_concepts_from_tree(node):
  event = find_main_event(node.tmr)
  if event is None:
    for child in node.children:
      if len(child.children) > 0:
        add_concepts_from_tree(child)
    return
    
  name=event_name_to_concept_name(node.name)
  global onto
  record = onto.find_one({"name":name})
  
  if record is None:
  
    entry = {
      "name" : name,
      "parents" : [event["concept"].lower()],
      "localProperties" : [ {"filler" : "robot", "slot" : "agent", "facet" : "sem"} ],
      "overriddenFillers" : [ ],
      "totallyRemovedProperties" : [ ],
      "inheritedProperties" : [ ]
    }
    props = entry["localProperties"]
    overr = entry["overriddenFillers"]

    parent = onto.find_one({"name":event["concept"].lower()})
    
    for child in node.children:
      if len(child.children) > 0:
        add_concepts_from_tree(child)
        props.append( {"filler" : event_name_to_concept_name(child.name), "slot" : "has-event-as-part", "facet" : "sem"} )
    
    if "THEME" in event:
      props.append( {"filler" : node.tmr[event["THEME"]]["concept"].lower(), "slot" : "theme", "facet" : "sem"} )
      if "THEME-1" in event:
        props.append( {"filler" : node.tmr[event["THEME-1"]]["concept"].lower(), "slot" : "theme", "facet" : "sem"} )
        
      found_ancestor = False
      ancestor = parent
      while not found_ancestor:
        for property in ancestor["localProperties"]:
          if property["slot"] == "theme" and property["facet"] == "sem":
            overr.append(property)
            found_ancestor = True
        ancestor = onto.find_one({"name":ancestor["parents"][0]}) # TODO support multiple inheritance
          
    if "INSTRUMENT" in event:
      props.append( {"filler" : node.tmr[event["INSTRUMENT"]]["concept"].lower(), "slot" : "instrument", "facet" : "sem"} )
      
      found_ancestor = False
      ancestor = parent
      while not found_ancestor:
        for property in ancestor["localProperties"]:
          if property["slot"] == "instrument" and property["facet"] == "sem":
            overr.append(property)
            found_ancestor = True
        ancestor = onto.find_one({"name":ancestor["parents"][0]}) # TODO support multiple inheritance
    
    #TODO add the overridden fillers
    #These should be case roles that are ancestors of this thing's case role (e.g. ARTIFACT for CHAIR)

    onto.insert_one(entry)
    assert(onto.find_one({"name":name}))
    
  else:
    for child in node.children:
      if len(child.children) > 0:
        add_concepts_from_tree(child)
        onto.update_one({"name":name},{"$push":{"localProperties":{"facet":"sem","slot":"has-event-as-part","filler":event_name_to_concept_name(child.name)}}})
        
        
# TODO remove duplicate event-as-parts
