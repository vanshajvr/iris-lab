from protocols.scpi_protocol import SCPIProtocol

SIM_VISA_LIBRARY="config/ah2700a_sim.yaml@sim"
SIM_RESOURCE_ADDRESS="GPIB0::22::INSTR"



def test_identify_returns_expected_idn():
    p=SCPIProtocol(visa_library=SIM_VISA_LIBRARY)
    p.open(SIM_RESOURCE_ADDRESS)
    idn=p.query("*IDN?")
    p.close()
    assert idn=="ANDEEEN-HAGERLING,2700A,SIM0001,1.0"

def test_configure_and_fetch_sequence():
    p=SCPIProtocol(visa_library=SIM_VISA_LIBRARY)
    p.open(SIM_RESOURCE_ADDRESS)

    assert p.query("FUNC:IMP CPD") == "OK"
    assert p.query("FREQ 1000") == "OK"

    reading=p.query("FETCH")
    p.close()

    assert reading == "0.960123,0.000110"

def test_write_before_open_raises():
    p=SCPIProtocol(visa_library=SIM_VISA_LIBRARY)
    try:
        p.write("*IDN?")
        assert False, "expected RuntimeError, got no exception"
    except RuntimeError as e:
        assert "Not connected" in str(e)