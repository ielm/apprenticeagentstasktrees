#ontosend.py

import pymongo
from datetime import datetime

import treenode
from tmrutils import *

onto = pymongo.MongoClient().after.inventory

def event_name_to_concept_name(name):
  return name.lower().replace(" ","-")

log=open("acftfile","w")

def add_concepts_from_tree(node, timestamp = None):
  log.write("acft called; node: "+node.name+"; time: "+str(timestamp))
  log.flush()
  if timestamp is None:
    timestamp = datetime.utcnow().isoformat(sep=" ")

  event = find_main_event(node.tmr)
  if event is None:
    for child in node.children:
      add_concepts_from_tree(child, timestamp)
    return
    
  name=event_name_to_concept_name(node.name)
  global onto
  record = onto.find_one({"name":name},{"localProperties":True})
  
  if record is None:
  
    entry = {
      "name" : name,
      "parents" : [event["concept"].lower()],
      "localProperties" : [ {"filler" : "robot", "slot" : "agent", "facet" : "sem"} ],
      "overriddenFillers" : [ ],
      "totallyRemovedProperties" : [ ],
      "timestamp":timestamp
    }
    props = entry["localProperties"]
    overr = entry["overriddenFillers"]

    parent = onto.find_one({"name":event["concept"].lower()})
    
    parts=[]
    for child in node.children:
      add_concepts_from_tree(child, timestamp)
      parts.append(event_name_to_concept_name(child.name))
    if len(parts) > 0:
      props.append( {"filler" : parts, "slot" : "has-event-as-part", "facet" : "sem"} )
    
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
    

    onto.insert_one(entry)
    
  else:

    change = False

    newparts=[]
    for child in node.children:
      add_concepts_from_tree(child, timestamp)
      newparts.append(event_name_to_concept_name(child.name))
  
    if not newparts:
      return
  
    for property in record["localProperties"]:
      if property["slot"] == "has-event-as-part" and type(property["filler"]) is list:
        oldparts = property["filler"]
        i=0
        j=0
        match = True
        mergedparts = []
        while match:
          match = False
          if oldparts[i] == newparts[j]:
            mergedparts.append(oldparts[i])
            i += 1
            j += 1
            match = True
          else:
            change = True
            for sequence in onto.aggregate( [{"$match":{"name":oldparts[i]}}, {"$unwind":"$localProperties"}, {"$match":{"localProperties.slot":"has-event-as-part"}}, {"$project":{"_id":0,"parts":"$localProperties.filler"}}]):
              if sequence["parts"] == newparts[j:j+len(sequence["parts"])]:
                mergedparts.append(oldparts[i])
                j += len(sequence["parts"])
                i += 1
                match = True
                break
            if not match:
              for sequence in onto.aggregate( [{"$match":{"name":newparts[j]}}, {"$unwind":"$localProperties"}, {"$match":{"localProperties.slot":"has-event-as-part"}}, {"$project":{"_id":0,"parts":"$localProperties.filler"}}]):
                if sequence["parts"] == oldparts[i:i+len(sequence["parts"])]:
                  mergedparts.append(newparts[j])
                  i += len(sequence["parts"])
                  j += 1
                  match = True
                  break
          if i == len(oldparts) or j == len(newparts):
            match = (i == len(oldparts) and j == len(newparts))
            break
          
        if match and change:
          # remove the sequence that is being overwritten
          onto.update_one({"name":name}, {"$pull":{"localProperties":{"filler":oldparts}}})
          newparts = mergedparts

    if change:
      onto.update_one({"name":name},{"$push":{"localProperties":{"facet":"sem","slot":"has-event-as-part","filler":newparts}}, "$set":{"timestamp":timestamp}})
#
