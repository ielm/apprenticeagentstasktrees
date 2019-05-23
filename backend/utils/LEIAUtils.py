from backend.utils.LEIAEnvironment import ontogen_service
from backend.models.tmr import TMR
from ontograph.Frame import Frame

import requests
import json


def ontogen_generate(tmr: TMR, meta: dict = None):
    # input = tmr + meta to json
    if tmr is None:
        raise Exception("Cannot generate utterance without input TMR")
    if meta is None:
        meta = {}

    _tmr = {}
    for frame in tmr.space():
        _tmr[frame.id] = frame.dump()

    data = {'meta': meta, 'TMR': _tmr}

    response = requests.post(url=ontogen_service() + "/gen/api/generate", data=json.dumps(data))
    if response.status_code != 200:
        raise Exception

    return response.content.decode("utf-8")
