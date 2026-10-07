import os
import time
import logging
import psycopg2
from dotenv import load_dotenv
from .simulated_source import SimulatedSource
from .real_source import RealAllenBradleySource
from .modbus_source import ModbusSource
from .db_writer import (
    get_resilient_connection,
    insert_readings,
    get_active_tags,
    get_tag_limits,
    get_plc_config,
    get_active_alarms,
    trigger_alarm,
    clear_alarm,
)

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


def build_source(plc_config):
    data_source = plc_config.get('data_source', 'simulated')
    if data_source == 'real':
        return RealAllenBradleySource(plc_config.get('plc_ip'))
    if data_source == 'modbus':
        return ModbusSource(
            plc_config.get('plc_ip'),
            plc_config.get('port') or 502,
            plc_config.get('unit_id') or 1,
        )
    return SimulatedSource()


def evaluate_alarms(conn, readings, tag_limits, active_alarms):
    for tag_name, data in readings.items():
        limits = tag_limits.get(tag_name)
        if limits is None or data['value'] is None:
            continue
        value = data['value']
        low = limits.get('low')
        high = limits.get('high')
        out_of_range = False
        limit_type = None
        limit_value = None
        if low is not None and value < low:
            out_of_range = True
            limit_type = 'low'
            limit_value = low
        elif high is not None and value > high:
            out_of_range = True
            limit_type = 'high'
            limit_value = high

        if out_of_range:
            if tag_name not in active_alarms:
                alarm_id = trigger_alarm(conn, tag_name, value, limit_type, limit_value)
                active_alarms[tag_name] = alarm_id
                logger.warning('ALARM triggered: ' + tag_name + ' = ' + str(value) + ' (' + limit_type + ' limit ' + str(limit_value) + ')')
        else:
            if tag_name in active_alarms:
                clear_alarm(conn, active_alarms[tag_name])
                logger.info('ALARM cleared: ' + tag_name)
                del active_alarms[tag_name]


def main():
    conn = get_resilient_connection()
    tags = get_active_tags(conn)
    tag_limits = get_tag_limits(conn)
    active_alarms = get_active_alarms(conn)
    plc_config = get_plc_config(conn)
    source = build_source(plc_config)
    logger.info('Active tags: ' + str([t['name'] for t in tags]))
    logger.info('PLC config: ' + str(plc_config))
    last_refresh = time.time()
    try:
        while True:
            try:
                if time.time() - last_refresh > TAG_REFRESH_SECONDS:
                    tags = get_active_tags(conn)
                    tag_limits = get_tag_limits(conn)

                    new_plc_config = get_plc_config(conn)
                    if new_plc_config != plc_config:
                        logger.info('PLC config changed: ' + str(plc_config) + ' -> ' + str(new_plc_config))
                        plc_config = new_plc_config
                        source = build_source(plc_config)

                    last_refresh = time.time()
                if not tags:
                    time.sleep(1)
                    continue
                readings = source.read_tags(tags)
                insert_readings(conn, readings)
                evaluate_alarms(conn, readings, tag_limits, active_alarms)
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
                active_alarms = get_active_alarms(conn)
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
