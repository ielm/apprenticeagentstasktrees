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
  
  entry = {
    "name" : event_name_to_concept_name(node.name),
    "parents" : [event["concept"].lower()],
    "localProperties" : [ {"filler" : "robot", "slot" : "agent", "facet" : "sem"} ],
    "overriddenFillers" : [ ],
    "totallyRemovedProperties" : [ ],
    "inheritedProperties" : [ ]
  }
  props = entry["localProperties"]

  for child in node.children:
    if len(child.children) > 0:
      add_concepts_from_tree(child)
      props.append( {"filler" : event_name_to_concept_name(child.name), "slot" : "has-event-as-part", "facet" : "sem"} )
  
  if "THEME" in event:
    props.append( {"filler" : node.tmr[event["THEME"]]["concept"].lower(), "slot" : "theme", "facet" : "sem"} )
    if "THEME-1" in event:
          props.append( {"filler" : node.tmr[event["THEME-1"]]["concept"].lower(), "slot" : "theme", "facet" : "sem"} )
  if "INSTRUMENT" in event:
    props.append( {"filler" : node.tmr[event["INSTRUMENT"]]["concept"].lower(), "slot" : "instrument", "facet" : "sem"} )
  
  #Apparently I need to have overridden fillers? idk
  
  global onto
  onto.insert_one(entry)
  assert(onto.find_one({"name":event_name_to_concept_name(node.name)}))