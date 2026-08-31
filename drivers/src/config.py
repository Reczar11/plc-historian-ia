import os
from pathlib import Path

from dotenv import load_dotenv

_DRIVERS_DIR = Path(__file__).resolve().parent.parent
load_dotenv(_DRIVERS_DIR / ".env")

PLC_IP = os.getenv("PLC_IP")
PLC_TAG_TEST = os.getenv("PLC_TAG_TEST")
DATA_SOURCE = os.getenv("DATA_SOURCE", "simulated")
