import asyncio

from asyncua.common.node import Node
from asyncua.server.server import Server

from core.driver_base import InstrumentDriver

NAMESPACE_URI="http://iris-lab/measurements"
ENDPOINT="opc.tcp://0.0.0.0:4840/iris/server/"

class MeasurementOPCUAServer:
    def __init__(self, driver:InstrumentDriver, poll_interval: float=1.0):
        self.driver=driver
        self.poll_interval=poll_interval
        self.server=Server()

        self.nodes:dict[str, Node]={}

    async def setup(self) -> None:
        await self.server.init()
        self.server.set_endpoint(ENDPOINT)
        idx=await self.server.register_namespace(NAMESPACE_URI)

        objects=self.server.get_objects_node()
        instrument=await objects.add_object(idx,"Instrument")

        outputs=self.driver.get_output()
        for quantity in outputs:
            node=await instrument.add_variable(idx,quantity,0.0)

            await node.set_writable(False)
            self.nodes[quantity]=node

    async def poll_loop(self) -> None:
        loop=asyncio.get_event_loop()
        while True:
            readings=await loop.run_in_executor(None, self.driver.measure)

            for m in readings:
                if m.quantity in self.nodes:
                    await self.nodes[m.quantity].write_value(m.value)
            
            await asyncio.sleep(self.poll_interval)

    async def run(self) -> None:
        await self.setup()
        async with self.server:
            print(f"IRIS OPC-UA bridge live at {ENDPOINT}")
            await self.poll_loop()


if __name__=="__main__":

    from drivers.replay_driver import ReplayDriver

    driver=ReplayDriver()
    driver.connect("tests/fixtures/sample_measurement.csv")
    driver.configure({"loop": True})

    bridge=MeasurementOPCUAServer(driver, poll_interval=2.0)
    asyncio.run(bridge.run())
                