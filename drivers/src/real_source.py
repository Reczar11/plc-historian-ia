from datetime import datetime, timezone

from pycomm3 import LogixDriver

from .config import PLC_IP as DEFAULT_PLC_IP
from .data_source import PLCDataSource


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _bad_readings(tag_names: list[str]) -> dict[str, dict]:
    timestamp = _iso_now()
    return {
        name: {"value": None, "timestamp": timestamp, "quality": "bad"}
        for name in tag_names
    }


class RealAllenBradleySource(PLCDataSource):
    def __init__(self, plc_ip: str | None = None):
        # Falls back to the .env value if no IP is passed in explicitly,
        # so existing call sites (RealAllenBradleySource()) keep working.
        self.plc_ip = plc_ip if plc_ip else DEFAULT_PLC_IP

    def set_plc_ip(self, plc_ip: str | None) -> None:
        self.plc_ip = plc_ip

    def read_tags(self, tags: list[dict]) -> dict[str, dict]:
        if not tags:
            return {}
        # Allen-Bradley Logix tags are read by their symbolic name, so we
        # only need the "name" field here — plc_address/data_type (used by
        # register-addressed protocols like Modbus) are not needed.
        tag_names = [tag['name'] for tag in tags]

        if not self.plc_ip:
            return _bad_readings(tag_names)

        try:
            with LogixDriver(self.plc_ip) as plc:
                results = plc.read(*tag_names)
        except Exception:
            return _bad_readings(tag_names)

        if not isinstance(results, (list, tuple)):
            results = [results]

        timestamp = _iso_now()
        readings: dict[str, dict] = {}
        for name, result in zip(tag_names, results):
            if result:
                readings[name] = {
                    "value": result.value,
                    "timestamp": timestamp,
                    "quality": "good",
                }
            else:
                readings[name] = {
                    "value": None,
                    "timestamp": timestamp,
                    "quality": "bad",
                }

        for name in tag_names:
            if name not in readings:
                readings[name] = {
                    "value": None,
                    "timestamp": timestamp,
                    "quality": "bad",
                }
        return readings
