import os

ONTOLOGY_HOST = int(os.environ["ONTOLOGY_HOST"]) if "ONTOLOGY_HOST" in os.environ else "localhost"
ONTOLOGY_PORT = int(os.environ["ONTOLOGY_PORT"]) if "ONTOLOGY_PORT" in os.environ else 5003
