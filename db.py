# db.py
# Acceso a datos (SQLite / Azure SQL)
# Funciones CRUD para tickets y tareas

import sqlite3
import pandas as pd
from datetime import datetime
from models import CREATE_TICKETS_TABLE, CREATE_TASKS_TABLE

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
        # Drop tables to force schema update (Dev MVP mode)
        # conn.execute("DROP TABLE IF EXISTS tasks")
        # conn.execute("DROP TABLE IF EXISTS tickets")

        conn.execute(CREATE_TICKETS_TABLE)
        conn.execute(CREATE_TASKS_TABLE)

        # Check if empty and populate
        cur = conn.cursor()
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

    conn.commit()


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
            titulo, descripcion, area_destino, categoria, division, planta,
            prioridad, urgencia_sugerida, responsable_sugerido, solicitante,
            created_by, estado
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        conn.commit()
        return cursor.lastrowid
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


def update_ticket(ticket_id, updates):
    """
    Actualiza campos de un ticket.
    updates: dict con {campo: valor}
    """
    conn = get_connection()
    try:
        # Add updated_at
        updates["updated_at"] = datetime.now()

        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values())
        values.append(ticket_id)

        query = f"UPDATE tickets SET {set_clause} WHERE id = ?"
        conn.execute(query, values)

        # Si se cierra, actualizar closed_at si no está seteada
        if "estado" in updates and updates["estado"] in ["RESUELTO", "CERRADO"]:
            conn.execute(
                "UPDATE tickets SET closed_at = ? WHERE id = ? AND closed_at IS NULL",
                (datetime.now(), ticket_id),
            )

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
