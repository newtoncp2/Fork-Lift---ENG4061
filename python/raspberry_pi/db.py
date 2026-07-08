
import json
import logging

logger = logging.getLogger(__name__)


def create_db_pool(host, port, dbname, user, password, minconn=1, maxconn=5):
    """Create and return a psycopg2 SimpleConnectionPool, or None if unavailable.

    Args:
        host, port, dbname, user, password: connection parameters (typically read
            from environment variables, e.g. in setup.py).
        minconn, maxconn: pool size bounds.

    Returns:
        psycopg2.pool.SimpleConnectionPool | None
    """
    if not (host and dbname and user and password):
        logger.debug("Database credentials incomplete, DB pool not created")
        return None

    try:
        from psycopg2.pool import SimpleConnectionPool

        pool = SimpleConnectionPool(
            minconn, maxconn,
            host=host, port=port, dbname=dbname, user=user, password=password,
        )
        logger.info("Database connection pool created")
        return pool
    except Exception as e:
        logger.debug(f"Database pool not available: {e}")
        return None


def parse_telemetria(line: str):
    """Parse a raw serial line (JSON telemetry payload) into a tuple of values.

    Matches the payload built by `enviarTelemetria` on the Arduino side:
        {"tipo": <int>, "falha_motor_passo": <bool>, "tensao_V": <float>,
         "corrente_mA": <float>, "potencia_mW": <float>, "rpm_esq": <int>,
         "rpm_dir": <int>, "t_ms": <float>}

    "tipo" indicates which command type the Arduino received, so every value is
    kept and stored (no filtering by tipo here).

    Returns:
        tuple | None: (tipo, falha_motor_passo, tensao, corrente, potencia, rpm_e, rpm_d, t_ms)
            or None if the line isn't a valid telemetry payload.
    """
    try:
        dados = json.loads(line)

        return (
            dados["tipo"],
            dados["falha_motor_passo"],
            dados["tensao_V"],
            dados["corrente_mA"],
            dados["potencia_mW"],
            dados["rpm_esq"],
            dados["rpm_dir"],
            dados["t_ms"],
        )
    except json.JSONDecodeError:
        logger.debug(f"Linha recebida não é JSON válido: {line}")
        return None
    except KeyError as e:
        logger.debug(f"Campo ausente no JSON de telemetria: {e}")
        return None


def insere_telemetria(pool, tipo, falha_motor_passo, tensao, corrente, potencia, rpm_e, rpm_d, t_ms):
    """Insert one telemetry row into the database. No-op if pool is None.

    Column layout matches the fields sent by `enviarTelemetria` on the Arduino,
    including `tipo` (the command type the Arduino received).
    """
    if pool is None:
        logger.debug("DB pool indisponível, pulando inserção de telemetria")
        return

    try:
        conn = pool.getconn()
    except Exception as e:
        logger.debug(f"Erro ao obter conexão do pool: {e}")
        return

    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO rb_emp (tipo, falha_motor_passo, tensao_v, corrente_ma,
                                        potencia_mw, rpm_esq, rpm_dir, t_ms)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (tipo, falha_motor_passo, tensao, corrente, potencia, rpm_e, rpm_d, t_ms),
            )
        conn.commit()
    except Exception as e:
        logger.debug(f"Erro ao inserir telemetria: {e}")
    finally:
        pool.putconn(conn)