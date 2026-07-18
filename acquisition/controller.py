from enum import Enum

from acquistion.logger import MeasurementLogger
from core.driver_base import InstrumentDriver
from core.measurement import Measurement

class AcquisitionState(Enum):
    IDLE="Idle"
    RUNNING="Running"
    STOPPED="Stopped"

class AcquisitionController:

    def __init__(self,driver:InstrumentDriver):
        self.driver=driver
        self.logger:MeasurementLogger | None=None
        self.state=AcquisitionState.IDLE

    def start(self, params:dict) ->None:
        self.driver.configure(params)
        self.logger=MeasurementLogger()
        self.state=AcquisitionState.RUNNING

    def step(self) -> list[Measurement]:
        if self.state != AcquisitionState.RUNNING:
            return []
        readings=self.driver.measure()
        if self.logger is not None:
            self.logger.log_measurements(readings)
        return readings
    
    def stop(self) -> None:
        self.state=AcquisitionState.STOPPED
        if self.logger is not None:
            self.logger.close()