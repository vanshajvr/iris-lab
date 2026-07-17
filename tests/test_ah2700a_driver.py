from drivers.ah2700a_driver import AH2700ADriver

SIM_VISA_LIBRARY = "config/ah2700a_sim.yaml@sim"
SIM_RESOURCE_ADDRESS = "GPIB0::22::INSTR"


def test_identify_returns_expected_idn():
    d = AH2700ADriver(visa_library=SIM_VISA_LIBRARY)
    d.connect(SIM_RESOURCE_ADDRESS)
    idn = d.identify()
    d.disconnect()
    assert idn == "ANDEEEN-HAGERLING,2700A,SIM0001,1.0"


def test_configure_and_measure_returns_capacitance_and_loss():
    d = AH2700ADriver(visa_library=SIM_VISA_LIBRARY)
    d.connect(SIM_RESOURCE_ADDRESS)
    d.configure({"frequency": 1000, "voltage": 15, "average_count": 4, "units": "PF"})

    readings = d.measure()
    d.disconnect()

    assert len(readings) == 2
    cap = next(m for m in readings if m.quantity == "capacitance")
    loss = next(m for m in readings if m.quantity == "loss")
    assert cap.value == 0.960123
    assert cap.unit == "pF"
    assert loss.value == 0.000110
    assert loss.unit == ""


def test_configure_rejects_unknown_parameter():
    d = AH2700ADriver(visa_library=SIM_VISA_LIBRARY)
    d.connect(SIM_RESOURCE_ADDRESS)
    try:
        d.configure({"not_a_real_param": 123})
        assert False, "expected ValueError, got no exception"
    except ValueError as e:
        assert "Unknown parameter" in str(e)
    finally:
        d.disconnect()


def test_frequency_clamps_above_max():
    d = AH2700ADriver(visa_library=SIM_VISA_LIBRARY)
    d.connect(SIM_RESOURCE_ADDRESS)
    # 25000 Hz exceeds the AH2700A's real 20 kHz max; configure() should
    # clamp it rather than send an out-of-range command to the instrument.
    d.configure({"frequency": 25000})
    d.disconnect()