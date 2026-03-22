import asyncio
import logging
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusDeviceContext,
    ModbusServerContext,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Zone Index Mapping: 0: Hospital, 1: Mall, 2: Residential, 3: Industrial
block = ModbusSequentialDataBlock(0, [1] * 10) # 10 coils at address 0
store = ModbusDeviceContext(di=block, co=block, hr=block, ir=block)
# In pymodbus 3.x, use 'devices' instead of 'slaves'
context = ModbusServerContext(devices={1: store}, single=False)

async def run_server():
    log.info("Starting SCADA Modbus TCP Server on port 502...")
    await StartAsyncTcpServer(context=context, address=("0.0.0.0", 502))

if __name__ == "__main__":
    asyncio.run(run_server())
