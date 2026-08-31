import math
import random
from datetime import datetime, timezone

from .data_source import PLCDataSource

_PROFILES = {
    "Temperature": {
        "base": 72.0,
        "amplitude": 6.0,
        "noise": 0.35,
        "period": 90,
        "phase": 0.0,
        "low": 45.0,
        "high": 95.0,
        "anomaly_span": 45.0,
    },
    "Pressure": {
        "base": 5.2,
        "amplitude": 0.55,
        "noise": 0.06,
        "period": 55,
        "phase": 1.1,
        "low": 2.0,
        "high": 8.5,
        "anomaly_span": 6.0,
    },
    "Vibration": {
        "base": 2.4,
        "amplitude": 0.45,
        "noise": 0.08,
        "period": 35,
        "phase": 2.3,
        "low": 0.4,
        "high": 5.0,
        "anomaly_span": 12.0,
    },
    "MotorCurrent": {
        "base": 14.8,
        "amplitude": 1.6,
        "noise": 0.2,
        "period": 70,
        "phase": 0.7,
        "low": 8.0,
        "high": 22.0,
        "anomaly_span": 28.0,
    },
}

_DEFAULT_PROFILE = {
    "base": 50.0,
    "amplitude": 8.0,
    "noise": 0.5,
    "period": 60,
    "phase": 0.0,
    "low": 10.0,
    "high": 90.0,
    "anomaly_span": 40.0,
}


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clamp_severity(severity: float) -> float:
    return max(0.0, min(float(severity), 1.0))


class SimulatedSource(PLCDataSource):
    def __init__(self) -> None:
        self._tick = 0
        self._anomalies: dict[str, dict[str, float | int]] = {}
        self._next_random_anomaly = random.randint(200, 400)

    def inject_anomaly(self, tag_name: str, severity: float) -> None:
        severity = _clamp_severity(severity)
        duration = max(4, int(4 + severity * 12))
        self._anomalies[tag_name] = {
            "remaining": duration,
            "severity": severity,
        }

    def read_tags(self, tag_names: list[str]) -> dict[str, dict]:
        if not tag_names:
            return {}

        self._tick += 1
        self._maybe_trigger_random_anomaly(tag_names)

        timestamp = _iso_now()
        readings: dict[str, dict] = {}
        for name in tag_names:
            readings[name] = {
                "value": round(self._sample(name), 4),
                "timestamp": timestamp,
                "quality": "good",
            }
        return readings

    def _maybe_trigger_random_anomaly(self, tag_names: list[str]) -> None:
        if self._tick < self._next_random_anomaly:
            return

        candidates = tag_names or list(_PROFILES)
        self.inject_anomaly(random.choice(candidates), random.uniform(0.15, 0.35))
        self._next_random_anomaly = self._tick + random.randint(200, 400)

    def _sample(self, tag_name: str) -> float:
        profile = _PROFILES.get(tag_name, _DEFAULT_PROFILE)
        wave = math.sin(
            2 * math.pi * self._tick / profile["period"] + profile["phase"]
        )
        value = (
            profile["base"]
            + profile["amplitude"] * wave
            + random.gauss(0.0, profile["noise"])
        )

        anomaly = self._anomalies.get(tag_name)
        if anomaly is None:
            return value

        anomaly["remaining"] = int(anomaly["remaining"]) - 1
        if anomaly["remaining"] <= 0:
            del self._anomalies[tag_name]

        severity = float(anomaly["severity"])
        sign = 1.0 if random.random() < 0.75 else -1.0
        ceiling = profile["high"] if sign > 0 else profile["low"]
        value = ceiling + sign * profile["anomaly_span"] * severity
        value += random.gauss(0.0, profile["noise"] * 2)
        return value
