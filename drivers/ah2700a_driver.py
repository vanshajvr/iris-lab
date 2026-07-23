import random
from datetime import datetime
from typing import Optional

from core.driver_base import InstrumentDriver
from core.measurement import Measurement
from core.registry import register_driver
from protocols.scpi_protocol import SCPIProtocol

@register_driver("ANDEEEN-HAGERLING")
class AH2700ADriver(InstrumentDriver):

    PARAMETERS={
        "frequency": {"type": "float", "unit": "Hz", "min": 50, "max": 20000, "clamp": True},
        "voltage": {"type": "float", "unit": "V", "min": -100, "max": 100},
        "average_count": {"type": "enum", "options": [4,7]},
        "loss_mode": {
            "type": "enum", 
            "options": [
                (1, "Conductance (nS)"),
                (2, "Dissipation Factor (tan delta)"),
                (3, "Series Resistance (kOhm)"),
                (4, "Parallel Resistance (GOhm)"),
                (5, "Loss Vector magnitude (jpF)")
            ]
        }
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

        if "loss_mode" in params:
            self.protocol.query(f"UNITS {params['loss_mode']}")

        self.protocol.query("CONTINOUS ON")

    def measure(self) -> list[Measurement]:
        raw=self.protocol.query("FETCH")
        cap_str, loss_str=raw.split(",")
        cap_value = float(cap_str)
        loss_value = float(loss_str)

        if "@sim" in self.protocol.visa_library:
            cap_value+=random.gauss(0,0.00003)
            loss_value+=random.gauss(0,0.0000005)

        now=datetime.now()

        return[
            Measurement(
                quantity="capacitance",
                value=cap_value,
                unit="pF",
                timestamp=now,
                instrument_id=self.resource_address
            ),
            Measurement(
                quantity="loss",
                value=loss_value,
                unit="",
                timestamp=now,
                instrument_id=self.resource_address
            )
        ]
    
    def disconnect(self) -> None:
        self.protocol.close()
