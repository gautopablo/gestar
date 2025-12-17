# models.py
# Definición de modelos y tablas
# Ticket y Tarea

# Esquema de la tabla Tickets
CREATE_TICKETS_TABLE = """
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    descripcion TEXT,
    area_destino TEXT,
    categoria TEXT,
    division TEXT,
    planta TEXT,
    prioridad TEXT,
    urgencia_sugerida TEXT,
    responsable_sugerido TEXT,
    responsable_asignado TEXT,
    estado TEXT DEFAULT 'NUEVO',
    solicitante TEXT,
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    closed_at TIMESTAMP
);
"""

# Esquema de la tabla Tareas
CREATE_TASKS_TABLE = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    descripcion TEXT NOT NULL,
    responsable TEXT,
    estado TEXT DEFAULT 'PENDIENTE',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(ticket_id) REFERENCES tickets(id)
);
"""

# Constantes
AREAS = ["Mantenimiento", "IT", "Recursos Humanos", "Calidad", "Producción"]
PRIORIDADES = ["Baja", "Media", "Alta", "Crítica"]
ESTADOS_TICKET = ["NUEVO", "ASIGNADO", "EN PROCESO", "RESUELTO", "CERRADO"]
ESTADOS_TAREA = ["PENDIENTE", "EN PROCESO", "COMPLETADA", "CANCELADA"]
ROLES = ["Solicitante", "Analista", "Jefe", "Director"]
