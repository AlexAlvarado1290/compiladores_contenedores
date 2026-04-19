import os
import time
from psycopg_pool import ConnectionPool

DB_CONF = {
    "host": os.getenv("DB_HOST", "db"),
    "port": os.getenv("DB_PORT", "5432"),
    "user": os.getenv("DB_USER", "pasteleria_user"),
    "password": os.getenv("DB_PASSWORD", "pasteleria_pass"),
    "dbname": os.getenv("DB_NAME", "pasteleria_db"),
}

CONN_STR = (
    f"host={DB_CONF['host']} port={DB_CONF['port']} "
    f"user={DB_CONF['user']} password={DB_CONF['password']} "
    f"dbname={DB_CONF['dbname']}"
)

pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:
    global pool
    if pool is None:
        last_err = None
        for _ in range(15):
            try:
                pool = ConnectionPool(conninfo=CONN_STR, min_size=1, max_size=5, open=True)
                with pool.connection() as conn:
                    conn.execute("SELECT 1")
                return pool
            except Exception as e:
                last_err = e
                time.sleep(2)
        raise RuntimeError(f"No se pudo conectar a la BD: {last_err}")
    return pool
