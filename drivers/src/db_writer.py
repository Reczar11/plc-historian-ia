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


def insert_readings(conn, readings):
    with conn.cursor() as cur:
        for tag_name, data in readings.items():
            cur.execute(
                'INSERT INTO plc_readings (time, tag_name, value, quality) VALUES (%s, %s, %s, %s)',
                (data['timestamp'], tag_name, data['value'], data['quality']),
            )
    conn.commit()
