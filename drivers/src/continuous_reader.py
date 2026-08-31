import time

from .config import DATA_SOURCE
from .real_source import RealAllenBradleySource
from .simulated_source import SimulatedSource

TAGS = ["Temperature", "Pressure", "Vibration", "MotorCurrent"]


def _make_source():
    name = (DATA_SOURCE or "simulated").strip().lower()
    if name == "real":
        return RealAllenBradleySource()
    return SimulatedSource()


def main() -> None:
    source = _make_source()
    while True:
        readings = source.read_tags(TAGS)
        for tag_name, reading in readings.items():
            print(
                f"{reading['timestamp']}  {tag_name}="
                f"{reading['value']}  quality={reading['quality']}"
            )
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
