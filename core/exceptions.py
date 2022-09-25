from dataclasses import dataclass


@dataclass
class StatePayloadMeta:
    user: str
    broker: str  # "aws.lambda"
    workflow: str  # "calculus.sum"
    wait_until: int  # timestamp


@dataclass
class StatePayload:
    guid: str
    parameters: dict
    meta: StatePayloadMeta
