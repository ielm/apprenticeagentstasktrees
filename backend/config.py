import os
networking = {
    "ontosem-host": os.environ["ONTOSEM_HOST"] if "ONTOSEM_HOST" in os.environ else "localhost",
    "ontosem-port": os.environ["ONTOSEM_PORT"] if "ONTOSEM_PORT" in os.environ else "5000",
}

def ontosem_service():
    return "http://" + networking["ontosem-host"] + ":" + networking["ontosem-port"]