from typing import Optional, cast

import pyvisa
from pyvisa.resources import MessageBasedResource

from protocols.base_protocol import Protocol

class SCPIProtocol(Protocol):

    def __init__(self, visa_library: str=""):
        self.visa_library=visa_library
        self.rm: Optional[pyvisa.ResourceManager]=None
        self.inst: Optional[MessageBasedResource]=None

    def open(self, resource_address=str) -> None:
        self.rm=pyvisa.ResourceManager(self.visa_library)
        self.inst=cast(
            MessageBasedResource, self.rm.open_resource(resource_address)
        )
        self.inst.read_termination="\n"
        self.inst.write_termination="\n"
    def write(self, command: str) -> None:
        if self.inst is None:
            raise RuntimeError("Not connected. Call open() first.")
        self.inst.write(command)

    def query(self, command: str) -> str:
        if self.inst is None:
            raise RuntimeError("Not connected. Call open() first.")
        return self.inst.query(command).strip()
    
    def close(self) -> None:
        if self.inst is not None:
            self.inst.close()
        if self.rm is not None:
            self.rm.close()