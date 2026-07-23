import os
import sys
from datetime import datetime

import pyqtgraph as pg
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication, QComboBox, QHBoxLayout, QLabel, QListWidget, QMainWindow, QVBoxLayout, QWidget,
)

from core.driver_base import InstrumentDriver
from core.registry import create_driver
from drivers.replay_driver import ReplayDriver

POLL_INTERVAL_MS=500
MAX_POINTS=100
LOG_DIR="logs"
CURVE_COLORS=["c", "y", "m", "g", "r"]

STYLESHEET= """
QMainWindow, QWidget {
    background-color: #1a1a1a;
    color: #e0e0e0;
    font-family: 'Menlo', 'Consolas', monospace;
}

QLabel#status {
    font-size: 14px;
    font-weight: bold;
    padding: 8px;
    border: 1px solid #333;
    border-radius: 6 px;
    background-color: #202020;
}

QLabel#valueCard {
    font-size: 16px;
    padding: 10px;
    border: 1px solid #333;
    border-radius: 6px;
    background-color: #202020;
}

QLabel#sectionHeader {
    font-size: 12px;
    color: #888;
    padding-top: 6px;
}

QListWidget {
    background-color: #101010:
    border: 1px solid #333;
    border-radius: 6px;
    font-size: 11px;
}

QComboBox {
    padding: 6px;
    border-radius: 6px;
    border: 1px solid #333;
    background-color: #202020;
}

"""

def make_ah2700_sim() -> InstrumentDriver:
    return create_driver(
        "GPIB0::22::INSTR", visa_library="config/ah2700a_sim.yaml@sim"
    )

def make_replay() -> InstrumentDriver:
    driver=ReplayDriver()
    driver.connect("tests/fixtures/sample_measurement.csv")
    driver.configure({"loop": True})
    return driver

DRIVER_FACTORIES={
    "AH2700A (Simulated)": make_ah2700_sim,
    "Replay (Real Recorded Data)": make_replay
}


class DashboardWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.driver:InstrumentDriver | None=None
        self.setWindowTitle("IRIS: Dashboard")
        self.resize(700,800)
        self.setStyleSheet(STYLESHEET)

        central=QWidget()
        self.main_layout=QVBoxLayout(central)

        selector_row=QHBoxLayout()
        selector_row.setSpacing(8)
        selector_row.addWidget(QLabel("Instrument:"))
        self.driver_selector=QComboBox()
        self.driver_selector.addItems(list(DRIVER_FACTORIES.keys()))
        self.driver_selector.currentTextChanged.connect(self.switch_driver)
        selector_row.addWidget(self.driver_selector)
        selector_row.addStretch()
        self.main_layout.addLayout(selector_row)

        self.status_label=QLabel("Status: not connected")
        self.status_label.setObjectName("status")
        self.main_layout.addWidget(self.status_label)

        self.dynamic_container=QWidget()
        self.dynamic_layout=QVBoxLayout(self.dynamic_container)
        self.main_layout.addWidget(self.dynamic_container)

        self.main_layout.addWidget(self._section_header("Activity Log"))
        self.log_list=QListWidget()
        self.main_layout.addWidget(self.log_list)

        self.setCentralWidget(central)

        self.value_labels: dict[str, QLabel]={}
        self.plot_curves={}
        self.plot_data: dict[str, list[float]]={}

        self.timer=QTimer()
        self.timer.timeout.connect(self.poll)

        self.switch_driver(self.driver_selector.currentText())



    def _section_header(self, text: str) -> QLabel:
        label=QLabel(text)
        label.setObjectName("sectionHeader")
        return label


    def log(self, message:str):
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_list.addItem(f"[{timestamp}] {message}")

    def _clear_dynamic_layout(self) -> None:
        while self.dynamic_layout.count():
            item=self.dynamic_layout.takeAt(0)
            if item is None:
                continue
            widget=item.widget()
            if widget is not None:
                widget.deleteLater()

    def switch_driver(self, name:str) -> None:
        self.timer.stop()

        if self.driver is not None:
            try:
                self.driver.disconnect()
            except Exception:
                pass

        self.log(f"Switching to: {name}")
        try:
            self.driver=DRIVER_FACTORIES[name]()
            idn=self.driver.identify()
            self.status_label.setText(f"Connected: {idn}")
            self.log(f"Instrument identified: {idn}")
        except Exception as e:
            self.driver=None
            self.status_label.setText("Status: not connected")
            self.log(f"Connection failed: {e}")
            return
        
        self._rebuild_dynamic_ui()
        self.timer.start(POLL_INTERVAL_MS)
    
    def _rebuild_dynamic_ui(self) -> None:
        self._clear_dynamic_layout()
        self.value_labels={}
        self.plot_widgets={}
        self.plot_curves={}
        self.plot_data={}

        if self.driver is None:
            return
        
        outputs=self.driver.get_output()

        cards_row=QHBoxLayout()
        for quantity in outputs:
            label=QLabel(f"{quantity}: --")
            label.setObjectName("valueCard")
            cards_row.addWidget(label)
            self.value_labels[quantity]=label
        self.dynamic_layout.addLayout(cards_row)

        for i, quantity in enumerate(outputs):
            color=CURVE_COLORS[i%len(CURVE_COLORS)]
            plot=pg.PlotWidget(title=quantity)
            plot.setBackground("#101010")
            plot.enableAutoRange(y=False)
            curve=plot.plot(pen=pg.mkPen(color, width=2))
            self.dynamic_layout.addWidget(plot)
            self.plot_widgets[quantity]=plot
            self.plot_curves[quantity]=curve
            self.plot_data[quantity]=[]

    
    def _rescale_plot(self,quantity:str,values:list[float]) -> None:
        if quantity not in self.plot_widgets or not values:
            return
        lo,hi=min(values),max(values)
        if lo==hi:
            pad=abs(lo)*0.001 if lo!=0 else 0.001
        else:
            pad=(hi-lo)*0.1
        self.plot_widgets[quantity].setYRange(lo-pad,hi+pad,padding=0)

    def poll(self) -> None:
        if self.driver is None:
            return
        try:
            readings=self.driver.measure()
            for m in readings:
                if m.quantity not in self.value_labels:
                    continue
                unit=f"{m.unit}" if m.unit else ""
                self.value_labels[m.quantity].setText(
                    f"{m.quantity}: {m.value:.6f}{unit}"
                )
                self.plot_data[m.quantity].append(m.value)
                trimmed=self.plot_data[m.quantity][-MAX_POINTS:]
                self.plot_data[m.quantity]=trimmed
                self.plot_curves[m.quantity].setData(trimmed)
                self._rescale_plot(m.quantity,trimmed)
        except Exception as e:
            self.log(f"Measurement error: {e}")

    def closeEvent(self, event) -> None:
        os.makedirs(LOG_DIR, exist_ok=True)
        timestamp=datetime.now().strftime("%Y%m%d_%H%M%S")
        path=os.path.join(LOG_DIR, f"session_{timestamp}.txt")
        with open(path, "w") as f:
            for i in range(self.log_list.count()):
                f.write(self.log_list.item(i).text()+ "\n")
        
        if self.driver is not None:
            try:
                self.driver.disconnect()
            except Exception:
                pass
        event.accept()

def main():
    app=QApplication(sys.argv)
    window=DashboardWindow()
    window.show()
    sys.exit(app.exec())

if __name__=="__main__":
    main()