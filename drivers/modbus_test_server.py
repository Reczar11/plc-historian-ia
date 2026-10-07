from pymodbus.datastore import ModbusDeviceContext, ModbusServerContext, ModbusSequentialDataBlock
from pymodbus.server import StartTcpServer
import struct

packed = struct.pack('>f', 42.5)
real_regs = list(struct.unpack('>HH', packed))

packed_dint = struct.pack('>i', -1000)
dint_regs = list(struct.unpack('>HH', packed_dint))

hr_values = [0] * 50
hr_values[0], hr_values[1] = real_regs
hr_values[10] = 123
hr_values[20], hr_values[21] = dint_regs

# NOTE: this pymodbus version's ModbusSequentialDataBlock subtracts 1 from
# the starting address internally, so pass 1 here to land on raw address 0.
hr_block = ModbusSequentialDataBlock(1, hr_values)
coil_block = ModbusSequentialDataBlock(1, [True] + [False] * 9)

context = ModbusDeviceContext(hr=hr_block, co=coil_block)
server_context = ModbusServerContext(devices=context, single=True)

print("Modbus TCP test server running on 127.0.0.1:5020")
print("HR:0  (REAL) = 42.5")
print("HR:10 (INT)  = 123")
print("HR:20 (DINT) = -1000")
print("COIL:0       = True")
StartTcpServer(context=server_context, address=("127.0.0.1", 5020))
