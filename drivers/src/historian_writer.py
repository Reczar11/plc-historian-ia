import os
import time
from dotenv import load_dotenv
from .simulated_source import SimulatedSource
from .real_source import RealAllenBradleySource
from .db_writer import get_connection, insert_readings

load_dotenv()

TAGS = ['Temperature', 'Pressure', 'Vibration', 'MotorCurrent']


def get_source():
    if os.getenv('DATA_SOURCE', 'simulated') == 'real':
        return RealAllenBradleySource()
    return SimulatedSource()


def main():
    source = get_source()
    conn = get_connection()
    print('Connected to TimescaleDB. Writing readings every 1 second...')
    try:
        while True:
            readings = source.read_tags(TAGS)
            insert_readings(conn, readings)
            for tag_name, data in readings.items():
                line = str(data['timestamp']) + '  ' + tag_name + '=' + str(data['value']) + '  quality=' + str(data['quality'])
                print(line)
            time.sleep(1)
    except KeyboardInterrupt:
        print('Stopped.')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
