import csv
from datetime import datetime
from itertools import cycle
from typing import Iterator, Optional

from core.driver_base import InstrumentDriver
from core.measurement import Measurement

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


class ReplayDriver(InstrumentDriver):

    PARAMETERS = {
        "loop": {"type": "enum", "options": [True, False]},
    }

    OUTPUTS = {
        "capacitance": {"unit": "pF"},
        "loss": {"unit": ""},
    }

    def __init__(self, visa_library: str=""):
        self.csv_path: Optional[str] = None
        self.loop = False
        self.rows: Optional[list[dict]] = None
        self._row_iter: Optional[Iterator[dict]] = None

    def connect(self, resource_address: str) -> None:
        self.csv_path = resource_address
        with open(self.csv_path, newline="") as f:
            self.rows = list(csv.DictReader(f))
        if self.rows is None:
            raise RuntimeError("Failed to load CSV rows.")
        self._row_iter = iter(self.rows)

    def identify(self) -> str:
        return f"IRIS-REPLAY,AH2700A-RECORDED,{self.csv_path},1.0"

    def configure(self, params: dict) -> None:
        unknown = set(params) - set(self.PARAMETERS)
        if unknown:
            raise ValueError(f"Unknown parameter(s): {unknown}")
        if "loop" in params:
            self.loop = params["loop"]
            if self.loop:
                if self.rows is None:
                    raise RuntimeError("Not connected. Call connect() first.")
                self._row_iter = cycle(self.rows)

    def measure(self) -> list[Measurement]:
        if self._row_iter is None:
            raise RuntimeError("Not connected. Call connect() first.")
        try:
            row = next(self._row_iter)
        except StopIteration:
            raise RuntimeError(
                "Replay data exhausted. Set configure({'loop': True}) to "
                "cycle, or reconnect() to restart from the beginning."
            )

        timestamp = datetime.strptime(row["Timestamp"], TIMESTAMP_FORMAT)

        return [
            Measurement(
                quantity="capacitance",
                value=float(row["Cp (pF)"]),
                unit="pF",
                timestamp=timestamp,
                instrument_id=self.csv_path,
                extra={
                    "frequency_hz": float(row["Frequency (Hz)"]),
                    "temperature_c": float(row["Temperature (\u00b0C)"]),
                    "humidity_pct": float(row["Humidity (%)"]),
                },
            ),
            Measurement(
                quantity="loss",
                value=float(row["Loss"]),
                unit="",
                timestamp=timestamp,
                instrument_id=self.csv_path,
            ),
        ]

    def disconnect(self) -> None:
        self._row_iter = None