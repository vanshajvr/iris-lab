from abc import ABC, abstractmethod

class Protocol(ABC):

    @abstractmethod
    def open(self, resource_address: str) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def write(self, command: str) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def query(self, command: str) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError