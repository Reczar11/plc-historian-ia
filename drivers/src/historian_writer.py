import os
import time
from dotenv import load_dotenv
from .simulated_source import SimulatedSource
from .real_source import RealAllenBradleySource
from .db_writer import get_connection, insert_readings, get_active_tags

load_dotenv()

TAG_REFRESH_SECONDS = 30


def get_source():
    if os.getenv('DATA_SOURCE', 'simulated') == 'real':
        return RealAllenBradleySource()
    return SimulatedSource()


def main():
    source = get_source()
    conn = get_connection()
    print('Connected to TimescaleDB. Writing readings every 1 second...')
    tags = get_active_tags(conn)
    print('Active tags: ' + str(tags))
    last_refresh = time.time()
    try:
        while True:
            if time.time() - last_refresh > TAG_REFRESH_SECONDS:
                tags = get_active_tags(conn)
                last_refresh = time.time()
            if not tags:
                time.sleep(1)
                continue
            readings = source.read_tags(tags)
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
