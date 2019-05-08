from backend.utils.LEIAEnvironment import ontogen_service
from backend.models.tmr import TMR
from ontograph.Frame import Frame

import requests
import json


def ontogen_generate(tmr: TMR, meta: dict = None):
    if tmr is None:
        raise Exception("Cannot generate utterance without input TMR")
    if meta is None:
        meta = {}

    data = {'meta': meta, 'TMR': _tmr_frames(tmr)}

    response = requests.post(url=ontogen_service() + "/gen/api/generate", data=json.dumps(data))

    return response.content.decode("utf-8")


def _tmr_frames(tmr: TMR) -> dict:
    _tmr = {}
    for frame in tmr.space():
        _tmr[frame.id] = frame.dump()
        for slot in frame:
            for filler in slot:
                if type(filler) is Frame:
                    _tmr[filler.id] = filler.dump()
    return _tmr
