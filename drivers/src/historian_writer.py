import os
import time
import logging
import psycopg2
from dotenv import load_dotenv
from .simulated_source import SimulatedSource
from .real_source import RealAllenBradleySource
from .db_writer import get_resilient_connection, insert_readings, get_active_tags

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('historian_writer.log'),
    ],
)
logger = logging.getLogger('historian.writer')

TAG_REFRESH_SECONDS = 30


def get_source():
    if os.getenv('DATA_SOURCE', 'simulated') == 'real':
        return RealAllenBradleySource()
    return SimulatedSource()


def main():
    source = get_source()
    conn = get_resilient_connection()
    tags = get_active_tags(conn)
    logger.info('Active tags: ' + str(tags))
    last_refresh = time.time()
    try:
        while True:
            try:
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
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as exc:
                logger.warning('Lost connection to TimescaleDB (%s). Reconnecting...', exc)
                try:
                    conn.close()
                except Exception:
                    pass
                conn = get_resilient_connection()
                last_refresh = 0
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info('Stopped.')
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == '__main__':
    main()
