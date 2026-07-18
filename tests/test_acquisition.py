import csv
import glob
import os

from acquisition.controller import AcquisitionController, AcquisitionState
from drivers.replay_driver import ReplayDriver

SAMPLE_CSV="tests/fixtures/sample_measurement.csv"

def make_connected_controller() -> AcquisitionController:
    driver=ReplayDriver()
    driver.connect(SAMPLE_CSV)
    return AcquisitionController(driver)

def test_starts_idle():
    controller=make_connected_controller()
    assert controller.state==AcquisitionState.IDLE

def test_step_before_start_returns_nothing():
    controller=make_connected_controller()
    assert controller.step()==[]

def test_start_transitions_to_running_and_step_returns_readings():
    controller=make_connected_controller()
    controller.start({"loop": True})
    assert controller.state==AcquisitionState.RUNNING

    readings=controller.step()
    assert len(readings)==2
    controller.stop()

def test_stop_transitions_state_and_closes_logger():
    controller=make_connected_controller()
    controller.start({"loop":True})
    controller.step()
    controller.stop()

    assert controller.state==AcquisitionState.STOPPED
    assert controller.logger is not None
    assert controller.logger._file.closed

def test_start_creates_a_real_csv_with_logged_rows():
    controller=make_connected_controller()
    controller.start({"loop":True})
    controller.step()
    controller.step()
    controller.stop()

    assert controller.logger is not None
    with open(controller.logger.path) as f:
        rows=list(csv.DictReader(f))

    assert len(rows)==4
    assert rows[0]["quantity"]=="capacitance"

def teardown_module():
    for f in glob.glob("data/measurement_*.csv"):
        os.remove(f)