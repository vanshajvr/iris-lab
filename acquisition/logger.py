import csv
import os
from datetime import datetime
from typing import Optional

from core.measurement import Measurement

DATA_DIR="data"

class MeasurementLogger:

    def __init__(self, prefix: str="measurement"):
        os.makedirs(DATA_DIR, exist_ok=True)
        timestamp=datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path=os.path.join(DATA_DIR, f"{prefix}_{timestamp}.csv")
        self._file=open(self.path, "w", newline="")

        self._writer: Optional[csv.DictWriter]=None

    def log_measurements(self, measurements:list[Measurement]) -> None:
        for m in measurements:
            row=m.as_row()
            if self._writer is None:
                self._writer=csv.DictWriter(self._file,fieldnames=list(row.keys()))
                self._writer.writeheader()
            self._writer.writerow(row)
        self._file.flush()

    def close(self) -> None:
        if not self._file.closed:
            self._file.close()