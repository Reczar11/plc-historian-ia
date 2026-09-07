import os
import time
import logging
import psycopg2

logger = logging.getLogger('historian.db')


def get_connection():
    return psycopg2.connect(
        host=os.getenv('TIMESCALE_HOST', 'localhost'),
        port=os.getenv('TIMESCALE_PORT', '5432'),
        user=os.getenv('TIMESCALE_USER'),
        password=os.getenv('TIMESCALE_PASSWORD'),
        dbname=os.getenv('TIMESCALE_DB'),
    )


def get_resilient_connection(max_backoff_seconds=30):
    backoff = 1
    while True:
        try:
            conn = get_connection()
            logger.info('Connected to TimescaleDB.')
            return conn
        except psycopg2.OperationalError as exc:
            logger.warning('Could not connect to TimescaleDB (%s). Retrying in %s seconds...', exc, backoff)
            time.sleep(backoff)
            backoff = min(backoff * 2, max_backoff_seconds)


def get_active_tags(conn):
    with conn.cursor() as cur:
        cur.execute('SELECT name FROM tags ORDER BY name')
        rows = cur.fetchall()
    return [row[0] for row in rows]


def get_tag_limits(conn):
    with conn.cursor() as cur:
        cur.execute('SELECT name, alarm_low, alarm_high FROM tags ORDER BY name')
        rows = cur.fetchall()
    limits = {}
    for row in rows:
        limits[row[0]] = {'low': row[1], 'high': row[2]}
    return limits


def get_active_alarms(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT id, tag_name FROM alarm_events WHERE status = 'active'")
        rows = cur.fetchall()
    active = {}
    for row in rows:
        active[row[1]] = row[0]
    return active


def trigger_alarm(conn, tag_name, value, limit_type, limit_value):
    with conn.cursor() as cur:
        cur.execute(
            'INSERT INTO alarm_events (tag_name, value, limit_type, limit_value) VALUES (%s, %s, %s, %s) RETURNING id',
            (tag_name, value, limit_type, limit_value),
        )
        alarm_id = cur.fetchone()[0]
    conn.commit()
    return alarm_id


def clear_alarm(conn, alarm_id):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE alarm_events SET status = 'cleared', cleared_at = now() WHERE id = %s",
            (alarm_id,),
        )
    conn.commit()


def insert_readings(conn, readings):
    with conn.cursor() as cur:
        for tag_name, data in readings.items():
            cur.execute(
                'INSERT INTO plc_readings (time, tag_name, value, quality) VALUES (%s, %s, %s, %s)',
                (data['timestamp'], tag_name, data['value'], data['quality']),
            )
    conn.commit()
