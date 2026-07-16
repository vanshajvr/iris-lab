from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class Measurement:
    quantity: str
    value: float
    unit: str
    timestamp: datetime
    instrument_id: Optional[str]=None
    uncertainty: Optional[str]=None
    extra: dict= field(default_factory=dict)

    def as_row(self) -> dict:
        row={
            "timestamp": self.timestamp.isoformat(),
            "instrument_id": self.instrument_id,
            "quantity": self.quantity,
            "value": self.value,
            "unit": self.unit,
            "uncertainty": self.uncertainty
        }
        row.update(self.extra)
        return row