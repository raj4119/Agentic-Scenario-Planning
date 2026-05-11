from sqlalchemy import create_engine, text
from casci.settings import settings

# Shared read-only connection pool — all agent tool functions use this
_engine = create_engine(
    settings.db_connection_string,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True,
)


def execute_query(sql: str, params: dict) -> list[dict]:
    """Execute a parameterised read-only query and return rows as dicts."""
    with _engine.connect() as conn:
        result = conn.execute(text(sql), params)
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result]
