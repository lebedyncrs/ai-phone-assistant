from typing import TypedDict


class CallData(TypedDict):
    stream_id: str
    call_id: str
    body: dict
