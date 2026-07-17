from core.registry import _REGISTRY, _load_all_drivers, create_driver, identify_driver
from drivers.ah2700a_driver import AH2700ADriver

SIM_VISA_LIBRARY="config/ah2700a_sim.yaml@sim"
SIM_RESOURCE_ADDRESS="GPIB0::22::INSTR"

def test_load_all_drivers_registers_ah2700a():
    _load_all_drivers()
    assert "ANDEEEN-HAGERLING" in _REGISTRY
    assert _REGISTRY["ANDEEEN-HAGERLING"] is AH2700ADriver

def test_identify_driver_matches_by_idn():
    driver_cls=identify_driver(SIM_RESOURCE_ADDRESS,visa_library=SIM_VISA_LIBRARY)
    assert driver_cls is AH2700ADriver

def test_identify_driver_raises_for_unknown_idn():
    try:
        identify_driver("GPIB0::99::INSTR", visa_library=SIM_VISA_LIBRARY)
        assert False, "expected ValueError, got no exception"

    except Exception as e:
        assert type(e).__name__ in ("ValueError", "VisaIOError")
    
def test_create_driver_returns_connected_instance():
    driver=create_driver(SIM_RESOURCE_ADDRESS,visa_library=SIM_VISA_LIBRARY)
    assert isinstance(driver,AH2700ADriver)
    assert driver.identify()=="ANDEEEN-HAGERLING,2700A,SIM0001,1.0"
    driver.disconnect()