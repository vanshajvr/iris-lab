import os
import sys
from datetime import datetime

import pyqtgraph as pg
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QListWidget, QMainWindow, QVBoxLayout, QWidget,
)

from core.driver_base import InstrumentDriver

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

"""

class DashboardWindow(QMainWindow):

    def __init__(self, driver:InstrumentDriver):
        super().__init__()
        self.driver=driver
        self.setWindowTitle("IRIS: Dashboard")
        self.resize(500,500)
        self.setStyleSheet(STYLESHEET)

        central=QWidget()
        layout=QVBoxLayout(central)

        self.status_label=QLabel("Status: not connected")
        self.status_label.setObjectName("status")
        layout.addWidget(self.status_label)

        outputs=self.driver.get_output()

        cards_row=QHBoxLayout()
        self.value_labels: dict[str,QLabel]={}
        for quantity in outputs:
            label=QLabel(f"{quantity}: --")
            label.setObjectName("valuecard")
            cards_row.addWidget(label)
            self.value_labels[quantity]=label
        layout.addLayout(cards_row)

        self.plot_curves={}
        self.plot_data: dict[str, list[float]]={}
        for i, quantity in enumerate(outputs):
            color=CURVE_COLORS[i%len(CURVE_COLORS)]
            plot=pg.PlotWidget(title=quantity)
            plot.setBackground("#101010")
            curve=plot.plot(pen=pg.mkPen(color,width=2))
            layout.addWidget(plot)
            self.plot_curves[quantity]=curve
            self.plot_data[quantity]=[]

        layout.addWidget(self._section_header("Activity Log"))
        self.log_list=QListWidget()
        layout.addWidget(self.log_list)

        self.setCentralWidget(central)

        self.log("Dashboard started")
        try:
            idn=self.driver.identify()
            self.status_label.setText(f"Connected: {idn}")
            self.log(f"Instrument identified: {idn}")
        except Exception as e:
            self.status_label.setText("Status: not connected")
            self.log(f"Identify failed: {e}")
        
        self.timer=QTimer()
        self.timer.timeout.connect(self.poll)
        self.timer.start(POLL_INTERVAL_MS)


    def _section_header(self, text: str) -> QLabel:
        label=QLabel(text)
        label.setObjectName("sectionHeader")
        return label


    def log(self, message:str):
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_list.addItem(f"[{timestamp}] {message}")

    def poll(self) -> None:
        try:
            readings=self.driver.measure()
            for m in readings:
                if m.quantity not in self.value_labels:
                    continue
                unit=f"{m.unit}" if m.unit else ""
                self.value_labels[m.quantity].setText(
                    f"{m.quantity}: {m.value}{unit}"
                )
                self.plot_data[m.quantity].append(m.value)
                trimmed=self.plot_data[m.quantity][-MAX_POINTS:]
                self.plot_data[m.quantity]=trimmed
                self.plot_curves[m.quantity].setData(trimmed)
        except Exception as e:
            self.log(f"Measurement error: {e}")

    def closeEvent(self, event) -> None:
        os.makedirs(LOG_DIR, exist_ok=True)
        timestamp=datetime.now().strftime("%Y%m%d_%H%M%S")
        path=os.path.join(LOG_DIR, f"session_{timestamp}.txt")
        with open(path, "w") as f:
            for i in range(self.log_list.count()):
                f.write(self.log_list.item(i).text()+ "\n")

        try:
            self.driver.disconnect()
        except Exception:
            pass
        event.accept()

def main():
    from drivers.replay_driver import ReplayDriver

    driver=ReplayDriver()
    driver.connect("tests/fixtures/sample_measurement.csv")
    driver.configure({"loop": True})

    app=QApplication(sys.argv)
    window=DashboardWindow(driver)
    window.show()
    sys.exit(app.exec())

if __name__=="__main__":
    main()