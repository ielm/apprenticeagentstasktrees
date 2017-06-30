# knowledgebase.py"""

instruments = dict()
affordances = dict()
 
import tmrutils
 
class RelationalConcept:
  def __init__(this):
    this.count = 0
    this.relationships = dict()

def add_instrument_relationship(action, instrument):
  global instruments, affordances
  
  if not action in instruments:
    instruments[action] = RelationalConcept()
  instruments[action].count += 1
  if not instrument in instruments[action].relationships:
    instruments[action].relationships[instrument] = 1
  else:
    instruments[action].relationships[instrument] += 1
  
  if not instrument in affordances:
    affordances[instrument] = RelationalConcept()
  affordances[instrument].count += 1
  if not action in affordances[instrument].relationships:
    affordances[instrument].relationships[action] = 1
  else:
    affordances[instrument].relationships[action] += 1
  
  
def update_knowledge_base(tmr):

  action = tmrutils.find_main_event(tmr)
  if "INSTRUMENT" in action:
    instrument = tmr[action["INSTRUMENT"]]["concept"]
    add_instrument_relationship(action["concept"], instrument)
  
  
def update_knowledge_base_2(input):
  if "results" in input:
    update_knowledge_base(input["results"][0]["TMR"])