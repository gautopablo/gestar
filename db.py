import sqlite3
import pandas as pd
import json
import streamlit as st
import os
import threading
import logging
import time
import re

# Configurar logging básico para capturar errores silenciosos
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import pyodbc
except ImportError:
    pyodbc = None
from datetime import datetime, timezone
from models import (
    CREATE_TICKETS_TABLE,
    CREATE_TASKS_TABLE,
    CREATE_TICKET_LOG_TABLE,
    CREATE_USERS_TABLE,
)

DB_NAME = "gestar.db"
_db_lock = threading.Lock()

# Whitelists para evitar inyección SQL por nombres de columnas
ALLOWED_COLUMNS = {
    "tickets": [
        "id",
        "titulo",
        "descripcion",
        "area_destino",
        "categoria",
        "subcategoria",
        "division",
        "planta",
        "prioridad",
        "urgencia_sugerida",
        "responsable_sugerido",
        "responsable_asignado",
        "estado",
        "solicitante",
        "created_by",
        "created_at",
        "updated_at",
        "closed_at",
    ],
    "users": ["id", "nombre_completo", "email", "rol", "area", "activo"],
    "tasks": [
        "id",
        "ticket_id",
        "descripcion",
        "responsable",
        "estado",
        "fecha_creacion",
    ],
}

MASTER_CATALOGS = {
    "areas": "Areas",
    "divisiones": "Divisiones",
    "plantas": "Plantas",
    "prioridades": "Prioridades",
    "roles": "Roles",
    "categorias": "Categorias",
}


def get_now_utc():
    """Retorna el timestamp actual en UTC."""
    return datetime.now(timezone.utc)


def _parse_conn_str(conn_str):
    parts = {}
    for chunk in conn_str.split(";"):
        if not chunk.strip():
            continue
        if "=" not in chunk:
            continue
        k, v = chunk.split("=", 1)
        parts[k.strip().lower()] = v.strip()
    return parts


def _mask_conn_str(conn_str):
    return re.sub(r"(?i)(Pwd|Password)\s*=\s*[^;]*", r"\1=***", conn_str)


def _normalize_bool_attr(conn_str, key):
    pattern = rf"(?i){key}\s*=\s*(true|false|0|1|yes|no)"

    def _repl(match):
        val = match.group(1).lower()
        if val in ("true", "1", "yes"):
            return f"{key}=yes"
        if val in ("false", "0", "no"):
            return f"{key}=no"
        return match.group(0)

    return re.sub(pattern, _repl, conn_str)


@st.cache_resource(show_spinner=False)
def _get_cached_sql_conn(conn_str):
    """
    Gestiona la conexión a SQL Server detectando el mejor driver disponible.
    """
    import re

    # Normalizar valores booleanos inválidos para ODBC Driver 18
    conn_str = _normalize_bool_attr(conn_str, "Encrypt")
    conn_str = _normalize_bool_attr(conn_str, "TrustServerCertificate")

    # Usar pyodbc con detección dinámica de drivers
    if pyodbc:
        # Detectar drivers instalados en el sistema (ej: 'ODBC Driver 18 for SQL Server')
        available_drivers = pyodbc.drivers()
        sql_drivers = [d for d in available_drivers if "SQL Server" in d]

        if sql_drivers:
            # Elegir el más actual (normalmente el último de la lista)
            best_driver = sql_drivers[-1]

            # Reemplazar el driver de la cadena de conexión por el detectado
            if "driver=" in conn_str.lower():
                conn_str = re.sub(
                    r"(?i)driver=\{[^{}]+\}", f"Driver={{{best_driver}}}", conn_str
                )
            else:
                conn_str += f";Driver={{{best_driver}}}"

            # Si es Driver 18, requiere ajustes específicos para Azure SQL en Linux
            if "Driver 18" in best_driver:
                if "TrustServerCertificate" not in conn_str:
                    conn_str += ";TrustServerCertificate=yes;"

                # Forzar Encrypt=yes y eliminar cualquier conflicto con Encrypt=no/0
                if "Encrypt" not in conn_str:
                    conn_str += ";Encrypt=yes;"
                else:
                    # Reemplazar Encrypt=no, Encrypt=0 o Encrypt=false por Encrypt=yes
                    conn_str = re.sub(
                        r"(?i)Encrypt=(no|0|false)", "Encrypt=yes", conn_str
                    )

        last_err = None
        for attempt in range(3):
            try:
                return pyodbc.connect(conn_str)
            except Exception as e:
                last_err = e
                masked = _mask_conn_str(conn_str)
                logger.error(
                    f"Error conectando con pyodbc (intento {attempt + 1}/3). Driver={sql_drivers[-1] if sql_drivers else 'N/A'}; ConnStr={masked}; Error={e}"
                )
                time.sleep(0.5 * (2**attempt))
        if last_err:
            raise last_err

    raise RuntimeError("No hay drivers disponibles (pyodbc) para conectar a SQL.")


def _is_sql_server_conn(conn):
    return hasattr(conn, "cursor") and not hasattr(conn, "backup")


def close_connection(conn):
    """
    En Streamlit, no queremos cerrar conexiones que están cacheadas con @st.cache_resource.
    Esta función solo cerrará si es estrictamente necesario (actualmente no cerramos nada cacheado).
    """
    # En esta arquitectura, preferimos dejar que la caché maneje la vida de la conexión.
    # Si cerráramos una conexión SQLite cacheada, la aplicación daría error en la siguiente llamada.
    return


def _get_lastrowid(cursor, conn):
    last_id = None
    try:
        last_id = cursor.lastrowid
    except Exception:
        last_id = None
    if last_id:
        return int(last_id)
    if _is_sql_server_conn(conn):
        try:
            cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
            row = cursor.fetchone()
            if row and row[0] is not None:
                return int(row[0])
        except Exception:
            return None
    return None


def _ensure_master_tables(conn, is_sql_server):
    cur = conn.cursor()
    if is_sql_server:
        cur.execute(
            """
            IF OBJECT_ID('master_catalogs','U') IS NULL
            CREATE TABLE master_catalogs (
                id INT IDENTITY(1,1) PRIMARY KEY,
                code NVARCHAR(100) NOT NULL,
                label NVARCHAR(255) NOT NULL,
                is_active BIT NOT NULL DEFAULT 1,
                created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
            );
            """
        )
        cur.execute(
            """
            IF OBJECT_ID('master_catalog_items','U') IS NULL
            CREATE TABLE master_catalog_items (
                id INT IDENTITY(1,1) PRIMARY KEY,
                catalog_id INT NOT NULL,
                code NVARCHAR(200) NULL,
                label NVARCHAR(255) NOT NULL,
                sort_order INT NOT NULL DEFAULT 0,
                is_active BIT NOT NULL DEFAULT 1,
                parent_item_id INT NULL,
                created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
                CONSTRAINT FK_master_items_catalog
                    FOREIGN KEY (catalog_id) REFERENCES master_catalogs(id),
                CONSTRAINT FK_master_items_parent
                    FOREIGN KEY (parent_item_id) REFERENCES master_catalog_items(id)
            );
            """
        )
        cur.execute(
            """
            IF NOT EXISTS (
                SELECT 1 FROM sys.indexes
                WHERE name = 'UX_master_catalogs_code'
                AND object_id = OBJECT_ID('master_catalogs')
            )
                CREATE UNIQUE INDEX UX_master_catalogs_code ON master_catalogs(code);
            """
        )
        cur.execute(
            """
            IF NOT EXISTS (
                SELECT 1 FROM sys.indexes
                WHERE name = 'IX_master_items_lookup'
                AND object_id = OBJECT_ID('master_catalog_items')
            )
                CREATE INDEX IX_master_items_lookup
                ON master_catalog_items(catalog_id, is_active, sort_order, label);
            """
        )
    else:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS master_catalogs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                label TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS master_catalog_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                catalog_id INTEGER NOT NULL,
                code TEXT,
                label TEXT NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                parent_item_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(catalog_id) REFERENCES master_catalogs(id),
                FOREIGN KEY(parent_item_id) REFERENCES master_catalog_items(id)
            );
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS IX_master_items_lookup
            ON master_catalog_items(catalog_id, is_active, sort_order, label);
            """
        )


def _ensure_catalog(cur, code, label):
    cur.execute("SELECT id FROM master_catalogs WHERE code = ?", (code,))
    row = cur.fetchone()
    if row:
        return int(row[0])
    cur.execute(
        "INSERT INTO master_catalogs (code, label, is_active) VALUES (?, ?, 1)",
        (code, label),
    )
    cur.execute("SELECT id FROM master_catalogs WHERE code = ?", (code,))
    return int(cur.fetchone()[0])


def _ensure_catalog_item(cur, catalog_id, label, sort_order, parent_item_id=None):
    if parent_item_id is None:
        cur.execute(
            """
            SELECT id FROM master_catalog_items
            WHERE catalog_id = ? AND label = ? AND parent_item_id IS NULL
            """,
            (catalog_id, label),
        )
    else:
        cur.execute(
            """
            SELECT id FROM master_catalog_items
            WHERE catalog_id = ? AND label = ? AND parent_item_id = ?
            """,
            (catalog_id, label, parent_item_id),
        )
    row = cur.fetchone()
    if row:
        item_id = int(row[0])
        cur.execute(
            """
            UPDATE master_catalog_items
            SET sort_order = ?, is_active = 1
            WHERE id = ?
            """,
            (sort_order, item_id),
        )
        return item_id

    cur.execute(
        """
        INSERT INTO master_catalog_items (catalog_id, label, sort_order, is_active, parent_item_id)
        VALUES (?, ?, ?, 1, ?)
        """,
        (catalog_id, label, sort_order, parent_item_id),
    )
    if parent_item_id is None:
        cur.execute(
            """
            SELECT id FROM master_catalog_items
            WHERE catalog_id = ? AND label = ? AND parent_item_id IS NULL
            """,
            (catalog_id, label),
        )
    else:
        cur.execute(
            """
            SELECT id FROM master_catalog_items
            WHERE catalog_id = ? AND label = ? AND parent_item_id = ?
            """,
            (catalog_id, label, parent_item_id),
        )
    return int(cur.fetchone()[0])


def _seed_master_data(conn):
    from models import (
        AREAS,
        CATEGORIAS,
        DIVISIONES,
        PLANTAS,
        PRIORIDADES,
        ROLES,
        SUBCATEGORIAS,
    )

    cur = conn.cursor()
    catalog_values = {
        "areas": AREAS,
        "divisiones": DIVISIONES,
        "plantas": PLANTAS,
        "prioridades": PRIORIDADES,
        "roles": ROLES,
    }
    for code, values in catalog_values.items():
        catalog_id = _ensure_catalog(cur, code, MASTER_CATALOGS[code])
        for idx, label in enumerate(values):
            _ensure_catalog_item(cur, catalog_id, label, idx)

    categorias_id = _ensure_catalog(cur, "categorias", MASTER_CATALOGS["categorias"])
    categoria_item_ids = {}
    for idx, categoria in enumerate(CATEGORIAS):
        item_id = _ensure_catalog_item(cur, categorias_id, categoria, idx)
        categoria_item_ids[categoria] = item_id

    for categoria, subcategorias in SUBCATEGORIAS.items():
        parent_id = categoria_item_ids.get(categoria)
        if not parent_id:
            continue
        for idx, sub in enumerate(subcategorias):
            _ensure_catalog_item(cur, categorias_id, sub, idx, parent_item_id=parent_id)


@st.cache_resource(show_spinner="Conectando a DB...")
def _get_connection_cached(conn_str):
    """Crea y retorna una conexión a la base de datos (Azure SQL o SQLite)."""
    if conn_str:
        try:
            conn = _get_cached_sql_conn(conn_str)
            try:
                conn.execute("SELECT 1")
            except Exception:
                _get_cached_sql_conn.clear()
                conn = _get_cached_sql_conn(conn_str)
            return conn
        except Exception as e:
            # Silenciamos el warning en la UI para evitar mensajes redundantes.
            # El error ya queda registrado en los logs del servidor.
            logger.info(f"Azure SQL no disponible, usando SQLite: {e}")

    # Fallback a SQLite local
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    # Habilitar foreign keys (Solo SQLite)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_connection():
    """
    Wrapper para resolver la cadena de conexión.
    Se pasa como argumento cacheado para evitar que quede fija una conexión
    SQLite si la app arrancó sin variables de entorno y luego se reconfigura.
    """
    conn_str = os.environ.get("AZURE_SQL_CONNECTION_STRING")

    if not conn_str and "azure_sql" in st.secrets:
        conn_str = st.secrets["azure_sql"].get("connection_string")

    return _get_connection_cached(conn_str or "")


def init_db():
    """Inicializa la base de datos creando las tablas si no existen."""
    # Evitar reinicialización redundante en la misma sesión
    if st.session_state.get("db_initialized"):
        return

    conn = get_connection()
    try:
        with _db_lock:
            # Detectar si es SQL Server o SQLite
            is_sql_server = _is_sql_server_conn(conn)

            # Crear tablas
            if is_sql_server:
                cursor = conn.cursor()
                create_statements = [
                    """
                    IF OBJECT_ID('tickets','U') IS NULL
                    CREATE TABLE tickets (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        titulo NVARCHAR(MAX) NOT NULL,
                        descripcion NVARCHAR(MAX) NULL,
                        area_destino NVARCHAR(255) NULL,
                        categoria NVARCHAR(255) NULL,
                        subcategoria NVARCHAR(255) NULL,
                        division NVARCHAR(255) NULL,
                        planta NVARCHAR(255) NULL,
                        prioridad NVARCHAR(50) NULL,
                        urgencia_sugerida NVARCHAR(50) NULL,
                        responsable_sugerido NVARCHAR(255) NULL,
                        responsable_asignado NVARCHAR(255) NULL,
                        estado NVARCHAR(50) DEFAULT 'NUEVO',
                        solicitante NVARCHAR(255) NULL,
                        created_by NVARCHAR(255) NULL,
                        created_at DATETIME2 DEFAULT SYSUTCDATETIME(),
                        updated_at DATETIME2 NULL,
                        closed_at DATETIME2 NULL
                    );
                    """,
                    """
                    IF OBJECT_ID('users','U') IS NULL
                    CREATE TABLE users (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        nombre_completo NVARCHAR(255) NOT NULL,
                        email NVARCHAR(255) NULL,
                        rol NVARCHAR(50) NULL,
                        area NVARCHAR(255) NULL,
                        activo BIT DEFAULT 1
                    );
                    """,
                    """
                    IF OBJECT_ID('tasks','U') IS NULL
                    CREATE TABLE tasks (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        ticket_id INT NOT NULL,
                        descripcion NVARCHAR(MAX) NOT NULL,
                        responsable NVARCHAR(255) NULL,
                        estado NVARCHAR(50) DEFAULT 'PENDIENTE',
                        fecha_creacion DATETIME2 DEFAULT SYSUTCDATETIME(),
                        CONSTRAINT FK_tasks_tickets FOREIGN KEY(ticket_id) REFERENCES tickets(id)
                    );
                    """,
                    """
                    IF OBJECT_ID('ticket_log','U') IS NULL
                    CREATE TABLE ticket_log (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        ticket_id INT NOT NULL,
                        created_at DATETIME2 DEFAULT SYSUTCDATETIME(),
                        author NVARCHAR(255) NULL,
                        event_type NVARCHAR(100) NULL,
                        message NVARCHAR(MAX) NULL,
                        meta_json NVARCHAR(MAX) NULL,
                        CONSTRAINT FK_ticket_log_tickets FOREIGN KEY(ticket_id) REFERENCES tickets(id)
                    );
                    """,
                ]
                for statement in create_statements:
                    cursor.execute(statement)
            else:
                conn.execute(CREATE_TICKETS_TABLE)
                conn.execute(CREATE_TASKS_TABLE)
                conn.execute(CREATE_TICKET_LOG_TABLE)
                conn.execute(CREATE_USERS_TABLE)

            # Crear y sembrar tablas maestras (idempotente)
            _ensure_master_tables(conn, is_sql_server)
            _seed_master_data(conn)

            # MIGRATION: Check if subcategoria exists in tickets
            if not is_sql_server:
                cur = conn.cursor()
                cur.execute("PRAGMA table_info(tickets)")
                columns = [col[1] for col in cur.fetchall()]
                if "subcategoria" not in columns:
                    conn.execute("ALTER TABLE tickets ADD COLUMN subcategoria TEXT")
            else:
                # SQL Server migration check: use dynamic SQL to avoid parse-time errors if table missing
                cursor = conn.cursor()
                cursor.execute(
                    """
                    IF OBJECT_ID('tickets','U') IS NOT NULL 
                    BEGIN
                    IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('tickets') AND name = 'subcategoria')
                        BEGIN
                            EXEC sp_executesql N'ALTER TABLE tickets ADD subcategoria NVARCHAR(MAX)';
                        END
                    END
                    """
                )

            # Check if users table is empty and populate initial users
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM users")
            if cur.fetchone()[0] == 0:
                from models import USERS_PROV

                # Primary Admin
                if is_sql_server:
                    cur.execute(
                        "INSERT INTO users (nombre_completo, email, rol, area, activo) VALUES (?, ?, ?, ?, 1)",
                        (
                            "Gauto, Pablo",
                            "gautop@taranto.com.ar",
                            "Administrador",
                            "Sistemas",
                        ),
                    )
                else:
                    conn.execute(
                        "INSERT INTO users (nombre_completo, email, rol, area, activo) VALUES (?, ?, ?, ?, 1)",
                        (
                            "Gauto, Pablo",
                            "gautop@taranto.com.ar",
                            "Administrador",
                            "Sistemas",
                        ),
                    )

                for u in USERS_PROV:
                    # Basic parsing "Name <email>"
                    if " <" in u:
                        name, email = u.split(" <")
                        email = email.rstrip(">")
                    else:
                        name, email = u, ""

                    # Assign default for current list
                    role = "Analista"
                    area = "IT"  # Default to IT for initial list
                    if "Ranea" in name:
                        area = "Ing. Procesos"
                    if "Vazquez" in name:
                        area = "Sistemas"  # Placeholder

                    if is_sql_server:
                        cur.execute(
                            "INSERT INTO users (nombre_completo, email, rol, area, activo) VALUES (?, ?, ?, ?, 1)",
                            (name, email, role, area),
                        )
                    else:
                        conn.execute(
                            "INSERT INTO users (nombre_completo, email, rol, area, activo) VALUES (?, ?, ?, ?, 1)",
                            (name, email, role, area),
                        )

            # Check if empty and populate tickets
            cur.execute("SELECT count(*) FROM tickets")
            if cur.fetchone()[0] == 0:
                populate_samples(conn)

            conn.commit()
            clear_master_cache()
        st.session_state["db_initialized"] = True
    finally:
        close_connection(conn)


def populate_samples(conn):
    """Carga datos de ejemplo."""
    tickets_data = [
        (
            "Falla en Impresora",
            "La impresora de RRHH no conecta en red.",
            "IT",
            "Hardware",
            "Administración",
            "Planta 1",
            "Media",
            "Media",
            "Juan Perez",
            None,
            "NUEVO",
            "Maria Garcia",
            "Maria Garcia",
        ),
        (
            "Mantenimiento AA",
            "Aire acondicionado de sala de reuniones gotea.",
            "Mantenimiento",
            "Infraestructura",
            "Administración",
            "Planta 1",
            "Baja",
            "Baja",
            "Luis Gomez",
            "Carlos Ruiz",
            "ASIGNADO",
            "Pedro Martinez",
            "Pedro Martinez",
        ),
        (
            "Error en validación",
            "El sistema de calidad da error 500 al guardar.",
            "IT",
            "Software",
            "Calidad",
            "Planta 2",
            "Alta",
            "Alta",
            "Ana Lopez",
            None,
            "NUEVO",
            "Juan Lopez",
            "Juan Lopez",
        ),
        (
            "Solicitud de Notebook",
            "Notebook para nuevo ingreso.",
            "IT",
            "Hardware",
            "RRHH",
            "Planta 1",
            "Media",
            "Media",
            None,
            "Juan Perez",
            "EN PROCESO",
            "Maria Garcia",
            "Maria Garcia",
        ),
    ]

    cur = conn.cursor()
    for t in tickets_data:
        cur.execute(
            """
            INSERT INTO tickets (
                titulo, descripcion, area_destino, categoria, division, planta,
                prioridad, urgencia_sugerida, responsable_sugerido, responsable_asignado,
                estado, solicitante, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            t,
        )

        ticket_id = _get_lastrowid(cur, conn)

        # Add sample task if not NEW
        if ticket_id and t[10] != "NUEVO":
            cur.execute(
                "INSERT INTO tasks (ticket_id, descripcion, responsable, estado) VALUES (?, ?, ?, ?)",
                (
                    ticket_id,
                    f"Investigar {t[0]}",
                    t[9] if t[9] else "Sin Asignar",
                    "PENDIENTE",
                ),
            )

        # Add init log
        if ticket_id:
            cur.execute(
                "INSERT INTO ticket_log (ticket_id, author, event_type, message) VALUES (?, ?, ?, ?)",
                (ticket_id, "System", "system", "Ticket creado con datos de ejemplo."),
            )

    conn.commit()


# --- LOGGING ---


def add_ticket_log(ticket_id, author, event_type, message, meta_json=None):
    """Inserta un registro en el log del ticket."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        with _db_lock:
            cur.execute(
                """
                INSERT INTO ticket_log (ticket_id, author, event_type, message, meta_json)
                VALUES (?, ?, ?, ?, ?)
            """,
                (ticket_id, author, event_type, message, meta_json),
            )
            conn.commit()
    finally:
        close_connection(conn)


def get_ticket_logs(ticket_id):
    """Retorna los logs de un ticket ordenados cronológicamente."""
    conn = get_connection()
    try:
        query = "SELECT id, ticket_id, created_at, author, event_type, message, meta_json FROM ticket_log WHERE ticket_id = ? ORDER BY id ASC"
        return pd.read_sql_query(
            query,
            conn,
            params=(ticket_id,),
        )
    finally:
        close_connection(conn)


# --- TICKETS ---


def create_ticket(data):
    """
    Crea un nuevo ticket.
    data: dict con las columnas del ticket.
    """
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO tickets (
            titulo, descripcion, area_destino, categoria, subcategoria, division, planta,
            prioridad, urgencia_sugerida, responsable_sugerido, solicitante,
            created_by, estado
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    # Prioridad default a Media (o Null) si no se provee. Logica de negocio: Solicitante no define prioridad final.
    prioridad = data.get("prioridad", "Media")

    try:
        with _db_lock:
            cursor.execute(
                query,
                (
                    data["titulo"],
                    data["descripcion"],
                    data["area_destino"],
                    data["categoria"],
                    data.get("subcategoria"),
                    data["division"],
                    data["planta"],
                    prioridad,
                    data.get("urgencia_sugerida"),
                    data.get("responsable_sugerido"),
                    data["solicitante"],
                    data.get("created_by"),
                    "NUEVO",
                ),
            )
            ticket_id = _get_lastrowid(cursor, conn)

            # Log creation
            if ticket_id:
                cursor.execute(
                    """
                    INSERT INTO ticket_log (ticket_id, author, event_type, message)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        ticket_id,
                        data.get("created_by", "System"),
                        "system",
                        "Ticket creado.",
                    ),
                )

            conn.commit()
        return ticket_id
    finally:
        close_connection(conn)


def get_tickets(filters=None):
    """
    Retorna Tickets como DataFrame.
    filters: dict opcional para filtrar.
    """
    conn = get_connection()
    try:
        cols = ", ".join(ALLOWED_COLUMNS["tickets"])
        query = f"SELECT {cols} FROM tickets"
        params = []
        if filters:
            conditions = []
            for k, v in filters.items():
                # Validar que la columna esté en el whitelist
                if k not in ALLOWED_COLUMNS["tickets"]:
                    logger.warning(f"Intento de filtrar por columna no permitida: {k}")
                    continue

                if v and v != "Todos" and v != "Todas":
                    # Handle list filters for IN clause
                    if isinstance(v, list):
                        placeholders = ",".join("?" * len(v))
                        conditions.append(f"{k} IN ({placeholders})")
                        params.extend(v)
                    else:
                        conditions.append(f"{k} = ?")
                        params.append(v)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)

        df = pd.read_sql_query(query, conn, params=params)
        return df
    finally:
        close_connection(conn)


@st.cache_data(ttl=600)
def get_master_items(catalog_code, include_inactive=False):
    """Retorna labels de un catálogo maestro ordenados."""
    conn = get_connection()
    try:
        query = """
            SELECT i.label
            FROM master_catalog_items i
            INNER JOIN master_catalogs c ON c.id = i.catalog_id
            WHERE c.code = ?
              AND i.parent_item_id IS NULL
        """
        params = [catalog_code]
        if not include_inactive:
            query += " AND c.is_active = 1 AND i.is_active = 1"
        query += " ORDER BY i.sort_order ASC, i.label ASC"
        df = pd.read_sql_query(query, conn, params=params)
        return df["label"].tolist() if not df.empty else []
    finally:
        close_connection(conn)


@st.cache_data(ttl=600)
def get_subcategories_map(include_inactive=False):
    """Retorna mapa categoria -> [subcategorias]."""
    conn = get_connection()
    try:
        query = """
            SELECT p.label AS categoria, c.label AS subcategoria
            FROM master_catalog_items c
            INNER JOIN master_catalog_items p ON p.id = c.parent_item_id
            INNER JOIN master_catalogs cat ON cat.id = c.catalog_id
            WHERE cat.code = 'categorias'
        """
        if not include_inactive:
            query += (
                " AND cat.is_active = 1 AND p.is_active = 1 AND c.is_active = 1"
            )
        query += " ORDER BY p.sort_order ASC, c.sort_order ASC, c.label ASC"

        df = pd.read_sql_query(query, conn)
        result = {}
        if df.empty:
            return result
        for _, row in df.iterrows():
            result.setdefault(row["categoria"], []).append(row["subcategoria"])
        return result
    finally:
        close_connection(conn)


def clear_master_cache():
    get_master_items.clear()
    get_subcategories_map.clear()


@st.cache_data(ttl=600)
def get_master_catalogs():
    """Retorna catálogo de maestras disponibles."""
    conn = get_connection()
    try:
        query = """
            SELECT id, code, label, is_active
            FROM master_catalogs
            ORDER BY label ASC
        """
        return pd.read_sql_query(query, conn)
    finally:
        close_connection(conn)


@st.cache_data(ttl=600)
def get_master_items_admin(catalog_code, parent_item_id=None):
    """Retorna items de maestra para administración."""
    conn = get_connection()
    try:
        query = """
            SELECT i.id, i.label, i.sort_order, i.is_active, i.parent_item_id,
                   p.label AS parent_label
            FROM master_catalog_items i
            INNER JOIN master_catalogs c ON c.id = i.catalog_id
            LEFT JOIN master_catalog_items p ON p.id = i.parent_item_id
            WHERE c.code = ?
        """
        params = [catalog_code]
        if parent_item_id is None:
            query += " AND i.parent_item_id IS NULL"
        else:
            query += " AND i.parent_item_id = ?"
            params.append(parent_item_id)
        query += " ORDER BY i.sort_order ASC, i.label ASC"
        return pd.read_sql_query(query, conn, params=params)
    finally:
        close_connection(conn)


def clear_master_admin_cache():
    get_master_catalogs.clear()
    get_master_items_admin.clear()


def create_master_item(catalog_code, label, sort_order=0, parent_item_id=None):
    """Crea un item maestro si no existe."""
    if not label or not str(label).strip():
        raise ValueError("Label de maestra vacío.")

    label = str(label).strip()
    conn = get_connection()
    try:
        cur = conn.cursor()
        with _db_lock:
            cur.execute("SELECT id FROM master_catalogs WHERE code = ?", (catalog_code,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Catálogo inexistente: {catalog_code}")
            catalog_id = int(row[0])

            if parent_item_id is None:
                cur.execute(
                    """
                    SELECT id FROM master_catalog_items
                    WHERE catalog_id = ? AND label = ? AND parent_item_id IS NULL
                    """,
                    (catalog_id, label),
                )
            else:
                cur.execute(
                    """
                    SELECT id FROM master_catalog_items
                    WHERE catalog_id = ? AND label = ? AND parent_item_id = ?
                    """,
                    (catalog_id, label, parent_item_id),
                )

            if cur.fetchone():
                return

            cur.execute(
                """
                INSERT INTO master_catalog_items
                (catalog_id, label, sort_order, is_active, parent_item_id)
                VALUES (?, ?, ?, 1, ?)
                """,
                (catalog_id, label, int(sort_order), parent_item_id),
            )
            conn.commit()
        clear_master_cache()
        clear_master_admin_cache()
    finally:
        close_connection(conn)


def update_master_item(item_id, updates):
    """Actualiza un item de maestra."""
    if not updates:
        return
    allowed = {"label", "sort_order", "is_active", "parent_item_id"}
    filtered = {k: v for k, v in updates.items() if k in allowed}
    if not filtered:
        return

    conn = get_connection()
    try:
        set_clause = ", ".join([f"{k} = ?" for k in filtered.keys()])
        values = list(filtered.values())
        values.append(item_id)
        query = f"UPDATE master_catalog_items SET {set_clause} WHERE id = ?"
        with _db_lock:
            conn.execute(query, values)
            conn.commit()
        clear_master_cache()
        clear_master_admin_cache()
    finally:
        close_connection(conn)


# --- GESTION DE USUARIOS ---


@st.cache_data(ttl=600)  # Caché de 10 minutos para usuarios
def get_users(only_active=False):
    """Retorna un DataFrame con todos los usuarios."""
    conn = get_connection()
    try:
        cols = ", ".join(ALLOWED_COLUMNS["users"])
        query = f"SELECT {cols} FROM users"
        if only_active:
            query += " WHERE activo = 1"
        query += " ORDER BY nombre_completo ASC"
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        close_connection(conn)


def clear_users_cache():
    """Invalida la caché de usuarios."""
    get_users.clear()


def create_user(data):
    """Crea un nuevo usuario."""
    conn = get_connection()
    try:
        query = """
            INSERT INTO users (nombre_completo, email, rol, area, activo)
            VALUES (?, ?, ?, ?, ?)
        """
        with _db_lock:
            conn.execute(
                query,
                (
                    data["nombre_completo"],
                    data.get("email"),
                    data.get("rol", "Solicitante"),
                    data.get("area"),
                    data.get("activo", 1),
                ),
            )
            conn.commit()
        clear_users_cache()
    finally:
        close_connection(conn)


def update_user(user_id, updates):
    """Actualiza datos de un usuario."""
    if not updates:
        return
    # Whitelist check
    filtered_updates = {
        k: v for k, v in updates.items() if k in ALLOWED_COLUMNS["users"]
    }
    if not filtered_updates:
        return

    conn = get_connection()
    try:
        set_clause = ", ".join([f"{k} = ?" for k in filtered_updates.keys()])
        values = list(filtered_updates.values())
        values.append(user_id)
        query = f"UPDATE users SET {set_clause} WHERE id = ?"
        with _db_lock:
            conn.execute(query, values)
            conn.commit()
        clear_users_cache()
    finally:
        close_connection(conn)


def get_user_by_name(name):
    """Busca un usuario por su nombre completo."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        if _is_sql_server_conn(conn):
            query = (
                "SELECT * FROM users WHERE nombre_completo = ? OR "
                "nombre_completo + ' <' + email + '>' = ?"
            )
        else:
            query = (
                "SELECT * FROM users WHERE nombre_completo = ? OR "
                "nombre_completo || ' <' || email || '>' = ?"
            )
        cur.execute(query, (name, name))
        row = cur.fetchone()
        if row:
            # Columns: id, nombre_completo, email, rol, area, activo
            return {
                "id": row[0],
                "nombre_completo": row[1],
                "email": row[2],
                "rol": row[3],
                "area": row[4],
                "activo": row[5],
            }
        return None
    finally:
        close_connection(conn)


def get_ticket_by_id(ticket_id):
    """Retorna un ticket específico como dict (o Series)."""
    conn = get_connection()
    try:
        cols = ", ".join(ALLOWED_COLUMNS["tickets"])
        query = f"SELECT {cols} FROM tickets WHERE id = ?"
        df = pd.read_sql_query(query, conn, params=(ticket_id,))
        if not df.empty:
            return df.iloc[0]
        return None
    finally:
        close_connection(conn)


def update_ticket(ticket_id, updates, author="System"):
    """
    Actualiza campos de un ticket y registra cambios en el log.
    updates: dict con {campo: valor}
    author: usuario que realiza el cambio
    """
    conn = get_connection()
    try:
        # Get current state for comparison
        current = pd.read_sql_query(
            "SELECT * FROM tickets WHERE id = ?", conn, params=(ticket_id,)
        )
        if current.empty:
            return
        current = current.iloc[0]

        # Detect changes and log
        if "estado" in updates and updates["estado"] != current["estado"]:
            msg = f"Cambio de estado: {current['estado']} -> {updates['estado']}"
            meta = json.dumps({"from": current["estado"], "to": updates["estado"]})
            conn.execute(
                "INSERT INTO ticket_log (ticket_id, author, event_type, message, meta_json) VALUES (?, ?, ?, ?, ?)",
                (ticket_id, author, "status_change", msg, meta),
            )

            # If closed/resolved, set closed_at
            if (
                updates["estado"] in ["RESUELTO", "CERRADO"]
                and not current["closed_at"]
            ):
                conn.execute(
                    "UPDATE tickets SET closed_at = ? WHERE id = ?",
                    (get_now_utc(), ticket_id),
                )

        if (
            "responsable_asignado" in updates
            and updates["responsable_asignado"] != current["responsable_asignado"]
        ):
            old = (
                current["responsable_asignado"]
                if current["responsable_asignado"]
                else "Sin Asignar"
            )
            new = updates["responsable_asignado"]
            msg = f"Asignación: {old} -> {new}"
            conn.execute(
                "INSERT INTO ticket_log (ticket_id, author, event_type, message) VALUES (?, ?, ?, ?)",
                (ticket_id, author, "assignment", msg),
            )

        if "prioridad" in updates and updates["prioridad"] != current["prioridad"]:
            msg = (
                f"Prioridad cambiada: {current['prioridad']} -> {updates['prioridad']}"
            )
            conn.execute(
                "INSERT INTO ticket_log (ticket_id, author, event_type, message) VALUES (?, ?, ?, ?)",
                (ticket_id, author, "priority_change", msg),
            )

        # Perform Update
        updates["updated_at"] = get_now_utc()

        # Whitelist check
        filtered_updates = {
            k: v for k, v in updates.items() if k in ALLOWED_COLUMNS["tickets"]
        }
        if not filtered_updates:
            conn.commit()
            return

        set_clause = ", ".join([f"{k} = ?" for k in filtered_updates.keys()])
        values = list(filtered_updates.values())
        values.append(ticket_id)

        query = f"UPDATE tickets SET {set_clause} WHERE id = ?"
        with _db_lock:
            conn.execute(query, values)
            conn.commit()
    finally:
        close_connection(conn)


# --- TASKS ---


def create_task(ticket_id, descripcion, responsable):
    conn = get_connection()
    try:
        with _db_lock:
            conn.execute(
                """
                INSERT INTO tasks (ticket_id, descripcion, responsable, estado)
                VALUES (?, ?, ?, 'PENDIENTE')
            """,
                (ticket_id, descripcion, responsable),
            )
            conn.commit()
    finally:
        close_connection(conn)


def get_tasks_for_ticket(ticket_id):
    conn = get_connection()
    try:
        cols = ", ".join(ALLOWED_COLUMNS["tasks"])
        query = f"SELECT {cols} FROM tasks WHERE ticket_id = ?"
        return pd.read_sql_query(query, conn, params=(ticket_id,))
    finally:
        close_connection(conn)


def update_task_status(task_id, new_status):
    conn = get_connection()
    try:
        with _db_lock:
            conn.execute(
                "UPDATE tasks SET estado = ? WHERE id = ?", (new_status, task_id)
            )
            conn.commit()
    finally:
        close_connection(conn)


def get_tasks_by_user(user_name):
    """Retorna tareas asignadas a un usuario específico."""
    conn = get_connection()
    try:
        cols_tasks = ", ".join([f"t.{c}" for c in ALLOWED_COLUMNS["tasks"]])
        query = f"""
            SELECT {cols_tasks}, tk.titulo as ticket_titulo 
            FROM tasks t 
            JOIN tickets tk ON t.ticket_id = tk.id 
            WHERE t.responsable = ? AND t.estado != 'COMPLETADA'
        """
        return pd.read_sql_query(
            query,
            conn,
            params=(user_name,),
        )
    finally:
        close_connection(conn)
