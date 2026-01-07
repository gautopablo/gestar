# db.py
# Acceso a datos (SQLite / Azure SQL)
# Funciones CRUD para tickets y tareas

import sqlite3
import pandas as pd
import json
from datetime import datetime
from models import (
    CREATE_TICKETS_TABLE,
    CREATE_TASKS_TABLE,
    CREATE_TICKET_LOG_TABLE,
    CREATE_USERS_TABLE,
)

DB_NAME = "gestar.db"


def get_connection():
    """Crea y retorna una conexión a la base de datos."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    # Habilitar foreign keys
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Inicializa la base de datos creando las tablas si no existen."""
    conn = get_connection()
    try:
        conn.execute(CREATE_TICKETS_TABLE)
        conn.execute(CREATE_TASKS_TABLE)
        conn.execute(CREATE_TICKET_LOG_TABLE)
        conn.execute(CREATE_USERS_TABLE)

        # MIGRATION: Check if subcategoria exists in tickets
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(tickets)")
        columns = [col[1] for col in cur.fetchall()]
        if "subcategoria" not in columns:
            conn.execute("ALTER TABLE tickets ADD COLUMN subcategoria TEXT")

        # Check if users table is empty and populate initial users
        cur.execute("SELECT count(*) FROM users")
        if cur.fetchone()[0] == 0:
            from models import USERS_PROV

            # Primary Admin
            conn.execute(
                "INSERT INTO users (nombre_completo, email, rol, area, activo) VALUES (?, ?, ?, ?, 1)",
                ("Gauto, Pablo", "gautop@taranto.com.ar", "Administrador", "Sistemas"),
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

                conn.execute(
                    "INSERT INTO users (nombre_completo, email, rol, area, activo) VALUES (?, ?, ?, ?, 1)",
                    (name, email, role, area),
                )

        # Check if empty and populate tickets
        cur.execute("SELECT count(*) FROM tickets")
        if cur.fetchone()[0] == 0:
            populate_samples(conn)

        conn.commit()
    finally:
        conn.close()


def populate_samples(conn):
    """Carga datos de ejemplo."""
    # (titulo, descripcion, area, categoria, division, planta, prioridad, urgencia, resp_sug, resp_asig, estado, sol, created_by)
    tickets = [
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
    for t in tickets:
        # Insert example data
        # Note: In SQLite, if column count matches, we can use concise insert, but here explicit is safer with schema changes
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

        ticket_id = cur.lastrowid

        # Add sample task if not NEW
        if t[10] != "NUEVO":
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
        conn.execute(
            """
            INSERT INTO ticket_log (ticket_id, author, event_type, message, meta_json)
            VALUES (?, ?, ?, ?, ?)
        """,
            (ticket_id, author, event_type, message, meta_json),
        )
        conn.commit()
    finally:
        conn.close()


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
        conn.close()


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
        ticket_id = cursor.lastrowid

        # Log creation
        cursor.execute(
            """
            INSERT INTO ticket_log (ticket_id, author, event_type, message)
            VALUES (?, ?, ?, ?)
        """,
            (ticket_id, data.get("created_by", "System"), "system", "Ticket creado."),
        )

        conn.commit()
        return ticket_id
    finally:
        conn.close()


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
        conn.close()


# --- GESTION DE USUARIOS ---


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
        conn.close()


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
        conn.close()


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
        conn.close()


def get_user_by_name(name):
    """Busca un usuario por su nombre completo."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE nombre_completo = ? OR nombre_completo || ' <' || email || '>' = ?",
            (name, name),
        )
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
        conn.close()


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
        conn.close()


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
        conn.close()


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
        conn.close()


def get_tasks_for_ticket(ticket_id):
    conn = get_connection()
    try:
        return pd.read_sql_query(
            "SELECT * FROM tasks WHERE ticket_id = ?", conn, params=(ticket_id,)
        )
    finally:
        conn.close()


def update_task_status(task_id, new_status):
    conn = get_connection()
    try:
        conn.execute("UPDATE tasks SET estado = ? WHERE id = ?", (new_status, task_id))
        conn.commit()
    finally:
        conn.close()


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
        conn.close()
