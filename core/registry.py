import importlib
import pkgutil

from core.driver_base import InstrumentDriver
from protocols.scpi_protocol import SCPIProtocol

_REGISTRY: dict[str, type[InstrumentDriver]]={}

def register_driver(idn_substring: str):
    def wrapper(driver_cls):
        _REGISTRY[idn_substring]=driver_cls
        return driver_cls
    return wrapper

def _load_all_drivers() -> None:
    import drivers as drivers_package
    for _, module_name, _ in pkgutil.iter_modules(
        drivers_package.__path__, drivers_package.__name__ + "."
    ):
        importlib.import_module(module_name)

def identify_driver(resource_address: str, visa_library: str = "") -> type[InstrumentDriver]:
    _load_all_drivers()

    probe=SCPIProtocol(visa_library=visa_library)
    probe.open(resource_address)
    idn=probe.query("*IDN?")
    probe.close()

    for idn_substring, driver_cls in _REGISTRY.items():
        if idn_substring in idn:
            return driver_cls
    raise ValueError(f"No registered driver matches IDN: {idn}")

def create_driver(resource_address: str, visa_library: str="") -> InstrumentDriver:
    driver_cls=identify_driver(resource_address, visa_library)
    driver=driver_cls(visa_library=visa_library)
    driver.connect(resource_address)
    return driver