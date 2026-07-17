from datetime import datetime
from typing import Optional

from core.driver_base import InstrumentDriver
from core.measurement import Measurement
from protocols.scpi_protocol import SCPIProtocol

class AH2700ADriver(InstrumentDriver):

    PARAMETERS={
        "frequency": {"type": "float", "unit": "Hz", "min": 50, "max": 20000, "clamp": True},
        "voltage": {"type": "float", "unit": "V", "min": -100, "max": 100},
        "average_count": {"type": "enum", "options": [4,7]},
        "units": {"type": "enum", "options": ["PF"]}
    }

    OUTPUTS={
        "capacitance":{"unit": "pF"},
        "loss": {"unit": ""}
    }

    def __init__(self, visa_library: str=""):
        self.protocol=SCPIProtocol(visa_library=visa_library)
        self.resource_address: Optional[str]

    def connect(self, resource_address:str) -> None:
        self.protocol.open(resource_address)
        self.resource_address=resource_address
        self.protocol.query("*CLS")

    def identify(self) -> str:
        return self.protocol.query("*IDN?")
    
    def configure(self, params: dict) -> None:
        unknown=set(params)-set(self.PARAMETERS)
        if unknown:
            raise ValueError(f"Unknown parameter(s): {unknown}")
        
        self.protocol.query("FUNC:IMP CPD")

        if "frequency" in params:
            freq=params["frequency"]
            spec=self.PARAMETERS["frequency"]
            if spec.get("clamp"):
                freq=max(spec["min"], min(spec["max"], freq))
            self.protocol.query(f"FREQ {freq}")
        
        if "voltage" in params:
            self.protocol.query(f"VOLT {params['voltage']}")

        if "average_count" in params:
            self.protocol.query(f"VOLT {params['average_count']}")

        if "units" in params:
            self.protocol.query(f"UNITS {params['units']}")

        self.protocol.query("CONTINOUS ON")

    def measure(self) -> list[Measurement]:
        raw=self.protocol.query("FETCH")
        cap_str, loss_str=raw.split(",")
        now=datetime.now()

        return[
            Measurement(
                quantity="capacitance",
                value=float(cap_str),
                unit="pF",
                timestamp=now,
                instrument_id=self.resource_address
            ),
            Measurement(
                quantity="loss",
                value=float(loss_str),
                unit="",
                timestamp=now,
                instrument_id=self.resource_address
            )
        ]
    
    def disconnect(self) -> None:
        self.protocol.close()
