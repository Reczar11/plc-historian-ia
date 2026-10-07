import struct
from datetime import datetime, timezone

from pymodbus.client import ModbusTcpClient

from .data_source import PLCDataSource

# Convention for the "PLC Address" field on a tag when using Modbus:
#   "<REGISTER_TYPE>:<ADDRESS>"
#   REGISTER_TYPE is one of: HR (holding register), IR (input register),
#                             COIL, DI (discrete input)
#   ADDRESS is the raw 0-based register/coil offset (NOT the classic
#   Modicon 40001-style numbering — subtract the offset yourself, e.g.
#   holding register 40101 -> "HR:100").
#
# The tag's Data Type field controls how HR/IR values are decoded:
#   INT    -> 1 register,  signed 16-bit
#   DINT   -> 2 registers, signed 32-bit (big-endian word order)
#   REAL   -> 2 registers, IEEE-754 float32 (big-endian word order)
#   BOOL   -> ignored for HR/IR (use COIL or DI instead)
# COIL / DI are always read as a single bit regardless of Data Type.
# STRING tags are not supported over Modbus in this version.

_REGISTER_TYPES = {'HR', 'IR', 'COIL', 'DI'}


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _bad_reading() -> dict:
    return {"value": None, "timestamp": _iso_now(), "quality": "bad"}


def _parse_address(plc_address):
    if not plc_address or ':' not in plc_address:
        return None
    reg_type, _, addr_str = plc_address.partition(':')
    reg_type = reg_type.strip().upper()
    if reg_type not in _REGISTER_TYPES:
        return None
    try:
        address = int(addr_str.strip())
    except ValueError:
        return None
    return reg_type, address


def _decode_registers(registers, data_type):
    if data_type == 'REAL':
        packed = struct.pack('>HH', registers[0], registers[1])
        return struct.unpack('>f', packed)[0]
    if data_type == 'DINT':
        packed = struct.pack('>HH', registers[0], registers[1])
        return float(struct.unpack('>i', packed)[0])
    # Default: INT (also used as fallback for BOOL/STRING misconfigured on HR/IR)
    packed = struct.pack('>H', registers[0])
    return float(struct.unpack('>h', packed)[0])


class ModbusSource(PLCDataSource):
    def __init__(self, plc_ip: str | None = None, port: int = 502, unit_id: int = 1):
        self.plc_ip = plc_ip
        self.port = port or 502
        self.unit_id = unit_id or 1

    def set_connection(self, plc_ip, port=502, unit_id=1):
        self.plc_ip = plc_ip
        self.port = port or 502
        self.unit_id = unit_id or 1

    def read_tags(self, tags: list[dict]) -> dict[str, dict]:
        if not tags:
            return {}
        if not self.plc_ip:
            return {tag['name']: _bad_reading() for tag in tags}

        readings: dict[str, dict] = {}
        try:
            with ModbusTcpClient(self.plc_ip, port=self.port, timeout=2, retries=1) as client:
                for tag in tags:
                    readings[tag['name']] = self._read_one(client, tag)
        except Exception:
            # Connection-level failure (e.g. host unreachable): mark everything bad.
            return {tag['name']: _bad_reading() for tag in tags}
        return readings

    def _read_one(self, client, tag) -> dict:
        parsed = _parse_address(tag.get('plc_address'))
        if parsed is None:
            return _bad_reading()
        reg_type, address = parsed
        data_type = tag.get('data_type', 'INT')

        try:
            if reg_type == 'COIL':
                response = client.read_coils(address, count=1, device_id=self.unit_id)
                if response.isError():
                    return _bad_reading()
                value = 1.0 if response.bits[0] else 0.0
            elif reg_type == 'DI':
                response = client.read_discrete_inputs(address, count=1, device_id=self.unit_id)
                if response.isError():
                    return _bad_reading()
                value = 1.0 if response.bits[0] else 0.0
            else:
                count = 2 if data_type in ('REAL', 'DINT') else 1
                if reg_type == 'HR':
                    response = client.read_holding_registers(address, count=count, device_id=self.unit_id)
                else:  # IR
                    response = client.read_input_registers(address, count=count, device_id=self.unit_id)
                if response.isError():
                    return _bad_reading()
                value = _decode_registers(response.registers, data_type)
        except Exception:
            return _bad_reading()

        return {"value": value, "timestamp": _iso_now(), "quality": "good"}
