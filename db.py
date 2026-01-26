# db.py
# Acceso a datos (SQLite / Azure SQL)
# Funciones CRUD para tickets y tareas

import sqlite3
import pandas as pd
import json
import streamlit as st

try:
    import pyodbc
except ImportError:
    pyodbc = None
try:
    import pymssql
except ImportError:
    pymssql = None
from datetime import datetime
from models import (
    CREATE_TICKETS_TABLE,
    CREATE_TASKS_TABLE,
    CREATE_TICKET_LOG_TABLE,
    CREATE_USERS_TABLE,
)

DB_NAME = "gestar.db"


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


@st.cache_resource
def _get_cached_sql_conn(conn_str):
    # Try pymssql first to avoid ODBC/TLS issues on Windows.
    if pymssql:
        cfg = _parse_conn_str(conn_str)
        server_raw = cfg.get("server", "")
        server = server_raw.replace("tcp:", "").strip()
        port = 1433
        if "," in server:
            server, port_str = server.split(",", 1)
            try:
                port = int(port_str)
            except ValueError:
                port = 1433
        user = cfg.get("uid") or cfg.get("user id") or cfg.get("user")
        password = cfg.get("pwd") or cfg.get("password")
        database = cfg.get("database")
        if server and user and password and database:
            conn = pymssql.connect(
                server=server,
                user=user,
                password=password,
                database=database,
                port=port,
                tds_version="7.4",
                login_timeout=30,
                timeout=30,
            )
            return _PymssqlConnWrapper(conn)
    if pyodbc:
        return pyodbc.connect(conn_str)
    raise RuntimeError("No hay driver disponible para Azure SQL.")


def _adapt_query_for_pymssql(query):
    return query.replace("?", "%s")


class _PymssqlCursorWrapper:
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, query, params=None):
        query = _adapt_query_for_pymssql(query)
        if params is None:
            return self._cursor.execute(query)
        return self._cursor.execute(query, params)

    def executemany(self, query, params_seq):
        query = _adapt_query_for_pymssql(query)
        return self._cursor.executemany(query, params_seq)

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class _PymssqlConnWrapper:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self, *args, **kwargs):
        return _PymssqlCursorWrapper(self._conn.cursor(*args, **kwargs))

    def execute(self, query, params=None):
        cur = self.cursor()
        return cur.execute(query, params)

    def commit(self):
        return self._conn.commit()

    def close(self):
        return self._conn.close()

    def __getattr__(self, name):
        return getattr(self._conn, name)


def _is_sql_server_conn(conn):
    return hasattr(conn, "cursor") and not hasattr(conn, "backup")


def close_connection(conn):
    if _is_sql_server_conn(conn):
        return
    conn.close()


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


@st.cache_resource(show_spinner="Conectando a DB...")
def get_connection():
    """Crea y retorna una conexión a la base de datos (Azure SQL o SQLite)."""
    # 1. Intentar conexión a Azure SQL via Streamlit Secrets
    if "azure_sql" in st.secrets:
        try:
            conn_str = st.secrets["azure_sql"]["connection_string"]
            return _get_cached_sql_conn(conn_str)
        except Exception as e:
            st.warning(
                f"No se pudo conectar a Azure SQL, usando SQLite local. Error: {e}"
            )

    # 2. Fallback a SQLite local
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    # Habilitar foreign keys (Solo SQLite)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Inicializa la base de datos creando las tablas si no existen."""
    # Evitar reinicialización redundante en la misma sesión
    if st.session_state.get("db_initialized"):
        return

    conn = get_connection()
    try:
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
                    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tickets') AND name = 'subcategoria')
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
        return pd.read_sql_query(
            "SELECT * FROM ticket_log WHERE ticket_id = ? ORDER BY id ASC",
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
        query = "SELECT * FROM tickets"
        params = []
        if filters:
            conditions = []
            for k, v in filters.items():
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


# --- GESTION DE USUARIOS ---


@st.cache_data(ttl=600)  # Caché de 10 minutos para usuarios
def get_users(only_active=False):
    """Retorna un DataFrame con todos los usuarios."""
    conn = get_connection()
    try:
        query = "SELECT * FROM users"
        if only_active:
            query += " WHERE activo = 1"
        query += " ORDER BY nombre_completo ASC"
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        close_connection(conn)


def create_user(data):
    """Crea un nuevo usuario."""
    conn = get_connection()
    try:
        query = """
            INSERT INTO users (nombre_completo, email, rol, area, activo)
            VALUES (?, ?, ?, ?, ?)
        """
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
    finally:
        close_connection(conn)


def update_user(user_id, updates):
    """Actualiza datos de un usuario."""
    if not updates:
        return
    conn = get_connection()
    try:
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values())
        values.append(user_id)
        query = f"UPDATE users SET {set_clause} WHERE id = ?"
        conn.execute(query, values)
        conn.commit()
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
        df = pd.read_sql_query(
            "SELECT * FROM tickets WHERE id = ?", conn, params=(ticket_id,)
        )
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
                    (datetime.now(), ticket_id),
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
        updates["updated_at"] = datetime.now()

        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values())
        values.append(ticket_id)

        query = f"UPDATE tickets SET {set_clause} WHERE id = ?"
        conn.execute(query, values)

        conn.commit()
    finally:
        close_connection(conn)


# --- TASKS ---


def create_task(ticket_id, descripcion, responsable):
    conn = get_connection()
    try:
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
        return pd.read_sql_query(
            "SELECT * FROM tasks WHERE ticket_id = ?", conn, params=(ticket_id,)
        )
    finally:
        close_connection(conn)


def update_task_status(task_id, new_status):
    conn = get_connection()
    try:
        conn.execute("UPDATE tasks SET estado = ? WHERE id = ?", (new_status, task_id))
        conn.commit()
    finally:
        close_connection(conn)


def get_tasks_by_user(user_name):
    """Retorna tareas asignadas a un usuario específico."""
    conn = get_connection()
    try:
        return pd.read_sql_query(
            "SELECT t.*, tk.titulo as ticket_titulo FROM tasks t JOIN tickets tk ON t.ticket_id = tk.id WHERE t.responsable = ? AND t.estado != 'COMPLETADA'",
            conn,
            params=(user_name,),
        )
    finally:
        close_connection(conn)
