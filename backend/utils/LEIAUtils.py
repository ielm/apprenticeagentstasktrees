from LEIAEnvironment import ontogen_service
from backend.models.tmr import TMR
from ontograph.Frame import Frame

import requests


def ontogen_generate(self, tmr: TMR = None, meta: dict = None):
    # input = tmr + meta to json
    if tmr is None:
        raise Exception("Cannot generate utterance without input TMR")
    if meta is None:
        meta = {}

    response = requests.post(url=ontogen_service() + "/gen/api/generate", data={"meta": meta, "TMR": tmr.frame.dump()})

    return response
