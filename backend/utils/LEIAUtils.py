from LEIAEnvironment import ontogen_service
from backend.models.tmr import TMR
from ontograph.Frame import Frame

import requests
import json


def ontogen_generate(tmr, meta: dict = None):
    # input = tmr + meta to json
    if tmr is None:
        raise Exception("Cannot generate utterance without input TMR")
    if meta is None:
        meta = {}

    data = {'meta': meta, 'TMR': tmr}

    response = requests.post(url=ontogen_service() + "/gen/api/generate", data=json.dumps(data))

    return response
