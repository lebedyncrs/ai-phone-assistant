from dataclasses import dataclass


@dataclass
class CallInfo:
    from_number: str | None
    to_number: str | None
    forwarded_from: str | None = None
