from drivers.replay_driver import ReplayDriver

SAMPLE_CSV = "tests/fixtures/sample_measurement.csv"


def test_identify_includes_csv_path():
    d = ReplayDriver()
    d.connect(SAMPLE_CSV)
    idn = d.identify()
    d.disconnect()
    assert SAMPLE_CSV in idn


def test_first_measurement_matches_real_recorded_startup_row():
    d = ReplayDriver()
    d.connect(SAMPLE_CSV)
    readings = d.measure()
    d.disconnect()

    cap = next(m for m in readings if m.quantity == "capacitance")
    loss = next(m for m in readings if m.quantity == "loss")

    assert cap.value == 0.964
    assert cap.unit == "pF"
    # Real startup artifact: Fluke not ready at t=0, per the findings doc.
    assert cap.extra["temperature_c"] == 0.0
    assert cap.extra["humidity_pct"] == 0.0

    assert loss.value == 0.000109
    assert loss.timestamp == cap.timestamp


def test_measure_advances_through_real_rows_in_order():
    d = ReplayDriver()
    d.connect(SAMPLE_CSV)

    first = d.measure()
    second = d.measure()
    d.disconnect()

    first_cap = next(m for m in first if m.quantity == "capacitance")
    second_cap = next(m for m in second if m.quantity == "capacitance")

    assert second_cap.timestamp > first_cap.timestamp
    assert second_cap.value == 0.964001


def test_measure_raises_when_data_exhausted_without_loop():
    d = ReplayDriver()
    d.connect(SAMPLE_CSV)

    for _ in range(20):
        d.measure()

    try:
        d.measure()
        assert False, "expected RuntimeError, got no exception"
    except RuntimeError as e:
        assert "exhausted" in str(e)
    finally:
        d.disconnect()


def test_loop_cycles_back_to_first_row():
    d = ReplayDriver()
    d.connect(SAMPLE_CSV)
    d.configure({"loop": True})

    for _ in range(20):
        d.measure()

    wrapped = d.measure()
    d.disconnect()

    wrapped_cap = next(m for m in wrapped if m.quantity == "capacitance")
    assert wrapped_cap.value == 0.964