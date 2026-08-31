from datetime import datetime, timezone

from pycomm3 import LogixDriver

from .config import PLC_IP
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
    def read_tags(self, tag_names: list[str]) -> dict[str, dict]:
        if not tag_names:
            return {}
        if not PLC_IP:
            return _bad_readings(tag_names)

        try:
            with LogixDriver(PLC_IP) as plc:
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
