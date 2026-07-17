import asyncio

from asyncua.client.client import Client

from bridge.opcua_server import ENDPOINT, NAMESPACE_URI

async def main():
    async with Client(url=ENDPOINT) as client:
        idx=await client.get_namespace_index(NAMESPACE_URI)
        objects=client.get_objects_node()
        instrument=await objects.get_child(f"{idx}:Instrument")

        for _ in range(5):
            capacitance=await instrument.get_child(f"{idx}:capacitance")
            loss=await instrument.get_child(f"{idx}:loss")
            print(
                "capacitance:", await capacitance.read_value(),
                "loss:", await loss.read_value()
            )
            await asyncio.sleep(2.0)



if __name__=="__main__":
    asyncio.run(main())