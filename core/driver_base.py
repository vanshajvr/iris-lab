from abc import ABC, abstractmethod
from typing import Optional

from core.measurement import Measurement

class InstrumentDriver(ABC):
    PARAMETERS: dict={}
    OUTPUTS: dict={}

    def __init__(self, visa_library: str=""):
        self.visa_library=visa_library

    @abstractmethod
    def connect(self, resource_address: str) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def identify(self) -> str:
        raise NotImplementedError
    
    @abstractmethod
    def configure(self, params: dict) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def measure(self) -> list[Measurement]:
        raise NotImplementedError
    
    @abstractmethod
    def disconnect(self) -> None:
        raise NotImplementedError
    
    def can_source(self) -> bool:
        return False
    
    def set_output(self, value: float, channel: Optional[str]=None) -> None:
        raise NotImplementedError(
            f"{type(self).__name__} does not support set_output() "
            f"(can_source() is False)"
        )
    def get_output(self, current_params: Optional[dict]=None) -> dict:
        return self.OUTPUTS