import sys

import pyqtgraph as pg
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

from drivers.replay_driver import ReplayDriver

POLL_INTERVAL_MS=500
MAX_POINTS=100

class LiveDemoWindow(QMainWindow):

    def __init__(self, driver):
        super().__init__()
        self.driver=driver
        self.setWindowTitle("IRIS: live replay demo (AH2700A, real recorded data)")
        self.resize(800,500)

        self.cap_data:list[float]=[]
        self.loss_data:list[float]=[]

        central=QWidget()
        layout=QVBoxLayout(central)

        self.cap_plot=pg.PlotWidget(title="Capacitance (pF)")
        self.cap_curve=self.cap_plot.plot(pen="c")
        layout.addWidget(self.cap_plot)

        self.loss_plot=pg.PlotWidget(title="Loss")
        self.loss_curve=self.loss_plot.plot(pen="y")
        layout.addWidget(self.loss_plot)

        self.setCentralWidget(central)

        self.timer=QTimer()
        self.timer.timeout.connect(self.poll)
        self.timer.start(POLL_INTERVAL_MS)

    def poll(self) -> None:
        readings=self.driver.measure()
        for m in readings:
            if m.quantity=="capacitance":
                self.cap_data.append(m.value)
            elif m.quantity=="loss":
                self.loss_data.append(m.value)
        
        self.cap_data=self.cap_data[-MAX_POINTS:]
        self.loss_data=self.loss_data[-MAX_POINTS:]

        self.cap_curve.setData(self.cap_data)
        self.loss_curve.setData(self.loss_data)

def main():
    driver=ReplayDriver()
    driver.connect("tests/fixtures/sample_measurement.csv")
    driver.configure({"loop": True})

    app=QApplication(sys.argv)
    window=LiveDemoWindow(driver)
    window.show()
    sys.exit(app.exec())

if __name__=="__main__":
    main()
        