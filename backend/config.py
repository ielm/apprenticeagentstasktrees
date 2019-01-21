import os
networking = {
    "ontosem-host": os.environ["ONTOSEM_HOST"] if "ONTOSEM_HOST" in os.environ else "localhost",
    "ontosem-port": os.environ["ONTOSEM_PORT"] if "ONTOSEM_PORT" in os.environ else "5000",
    "yale-robot-host": os.environ["YALE_ROBOT_HOST"] if "YALE_ROBOT_HOST" in os.environ else "localhost",
    "yale-robot-port": os.environ["YALE_ROBOT_PORT"] if "YALE_ROBOT_PORT" in os.environ else "7777",
}

def ontosem_service():
    return "http://" + networking["ontosem-host"] + ":" + networking["ontosem-port"]

def yale_robot_service():
    return "http://" + networking["yale-robot-host"] + ":" + networking["yale-robot-port"]