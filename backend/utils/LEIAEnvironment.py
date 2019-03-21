import os

MONGO_HOST = int(os.environ["MONGO_HOST"]) if "MONGO_HOST" in os.environ else "localhost"
MONGO_PORT = int(os.environ["MONGO_PORT"]) if "MONGO_PORT" in os.environ else 27017

ONTOLOGY_HOST = os.environ["ONTOLOGY_HOST"] if "ONTOLOGY_HOST" in os.environ else "localhost"
ONTOLOGY_PORT = int(os.environ["ONTOLOGY_PORT"]) if "ONTOLOGY_PORT" in os.environ else 5003
ONTOLOGY_DATABASE = os.environ["ONTOLOGY_DATABASE"] if "ONTOLOGY_DATABASE" in os.environ else "leia-ontology"
ONTOLOGY_COLLECTION = os.environ["ONTOLOGY_COLLECTION"] if "ONTOLOGY_COLLECTION" in os.environ else "robot-v.1.0.0"

networking = {
    "ontosem-host": os.environ["ONTOSEM_HOST"] if "ONTOSEM_HOST" in os.environ else "localhost",
    "ontosem-port": os.environ["ONTOSEM_PORT"] if "ONTOSEM_PORT" in os.environ else "5000",
}

def ontosem_service():
    return "http://" + networking["ontosem-host"] + ":" + networking["ontosem-port"]