from dataclasses import dataclass


@dataclass(frozen=True)
class Alert:
    org_id: str
    service_name: str
    endpoint_id: str
    type: str
    severity: str
    message: str
    current_value: float
    threshold: float
