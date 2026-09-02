import os
import psycopg2


def get_connection():
    return psycopg2.connect(
        host=os.getenv('TIMESCALE_HOST', 'localhost'),
        port=os.getenv('TIMESCALE_PORT', '5432'),
        user=os.getenv('TIMESCALE_USER'),
        password=os.getenv('TIMESCALE_PASSWORD'),
        dbname=os.getenv('TIMESCALE_DB'),
    )


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
