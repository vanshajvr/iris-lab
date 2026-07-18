# IRIS -- Instrument-agnostic Real-time Interface Suite

A Python framework for automating lab instruments through a shared driver
interface. Swap the instrument, keep the framework -- adding support for a
new device means writing a driver against a documented contract, not
rebuilding the acquisition pipeline, GUI, or protocol layer.

Originated from automating an AH2700A capacitance bridge during a CSIR-NPL
(India's National Metrology Institute) research internship, then
generalized into an instrument-independent architecture.

## What it does

- **Auto-discovers instruments** via SCPI `*IDN?`, matching a connected
  resource to the correct driver with zero hardcoded instrument names
  anywhere in the framework
- **Renders a live dashboard** (PySide6 + pyqtgraph) purely from whatever
  quantities the connected driver declares -- switch instruments while the
  app is running and the value cards, plots, and identity banner all
  rebuild automatically
- **Exposes live measurements over OPC-UA**, the industrial standard for
  interoperable machine-to-machine data (used across Siemens, Rockwell,
  ABB, Schneider, and similar systems), via `asyncua`
- **Logs every measurement** to timestamped CSV, in a long/tidy format
  that scales to any number of quantities per instrument without a schema
  change

## Why this architecture

Every instrument driver, no matter the manufacturer or command set (SCPI,
TSP, or otherwise), does the same five things: connect, identify itself,
accept configuration, produce a measurement, disconnect. IRIS defines that
contract once (`core/driver_base.py`) and builds everything else --
GUI, logging, the OPC-UA bridge -- against the contract, never against a
specific instrument. A driver only needs to declare:

- `PARAMETERS` -- what can be configured (type, range, or options), used
  to render the acquisition form dynamically
- `OUTPUTS` (or `get_outputs()`, for mode-dependent instruments) -- what
  quantities `measure()` will produce

## Built and validated without hardware access

Every piece of this framework was built and tested without access to a
physical instrument, using two complementary approaches:

1. **`pyvisa-sim`** (`config/ah2700a_sim.yaml`) -- a simulated AH2700A
   that responds to the exact SCPI sequence the real bridge expects
   (`*CLS` -> `FUNC:IMP CPD` -> `FREQ`/`VOLT`/`AVG`/`UNITS` -> `FETCH`),
   letting the protocol layer and real driver be tested structurally
   against realistic instrument behavior.
2. **`ReplayDriver`** -- streams real recorded measurement data (a
   trimmed sample from an actual multi-hour AH2700A acquisition session,
   `tests/fixtures/sample_measurement.csv`) through the same
   `InstrumentDriver` interface, preserving genuine timestamps and even
   the real startup noise artifact from the original session. This is
   what proves the pipeline works against *real* data, not just
   synthetic test values.

## Architecture

```
core/         Measurement model, InstrumentDriver interface, registry
protocols/    SCPI-over-PyVISA implementation
drivers/      AH2700ADriver (real + simulated), ReplayDriver (real recorded data)
config/       pyvisa-sim instrument profile
bridge/       OPC-UA server exposing live measurements
gui/          Dashboard: live plots, instrument switcher, activity log
acquisition/  CSV logging (used internally by future acquisition flows)
tests/        21 tests covering protocol, drivers, registry, acquisition
```

Dependency direction is strict: `core/` depends on nothing else in the
project; `protocols/` and `drivers/` depend on `core/`; nothing outside
`core/` is ever imported back into it.

## Demo

The clearest demonstration of the architecture is switching instruments
live in the Dashboard: select "AH2700A (Simulated)", then switch to
"Replay (Real Recorded Data)" mid-run. The value cards, plots, and
connection banner all tear down and rebuild automatically, sourced from
`driver.get_outputs()` -- no code path branches on which instrument is
active.

*(GIF/screen recording of the live switch goes here.)*

## Getting started

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Run the test suite:
```bash
pytest tests/ -v
```

Run the Dashboard:
```bash
python3 -m gui.dashboard
```

Run the OPC-UA bridge (streams real recorded data, loops continuously):
```bash
python3 -m bridge.opcua_server
```
In a second terminal, a minimal client demonstrating a third-party
program reading the live data:
```bash
python3 -m bridge.test_client
```

## Adding a new instrument

1. Create `drivers/<name>_driver.py`, implementing `InstrumentDriver`
2. Declare `PARAMETERS` and `OUTPUTS` (or `get_outputs()`, if the
   quantities produced depend on the instrument's current mode)
3. Add `@register_driver("<IDN substring>")` above the class

Nothing else needs to change -- the registry, GUI, and logging all pick
up the new driver automatically.

## Future scope

Deliberately out of scope for this version, documented rather than built:

- **TSP protocol support** (for Lua-scripted instruments, e.g. newer
  Keithley SMUs) -- the protocol layer is designed to support a second
  implementation of the `Protocol` interface alongside `SCPIProtocol`
- **Multi-instrument concurrent orchestration** -- coordinating several
  instruments in one experiment (bus locking, sequencing) rather than
  one instrument at a time
- **Digital Calibration Certificate (DCC) generation** -- exporting
  measurement sessions as standards-compliant calibration certificates
- **Modbus bridge**, alongside the existing OPC-UA bridge

## Origin

The AH2700A driver logic in this project was ported from a working
automation suite built during a CSIR-NPL research internship, where it
ran real capacitance-temperature dependence measurements over
multi-hour sessions. This project generalizes that specific
implementation into a reusable, instrument-agnostic architecture.