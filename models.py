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
    subcategoria TEXT,
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

# Esquema de la tabla Logs
CREATE_TICKET_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS ticket_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    author TEXT,
    event_type TEXT,
    message TEXT,
    meta_json TEXT,
    FOREIGN KEY(ticket_id) REFERENCES tickets(id)
);
"""

# Constantes

AREAS = [
    "Dirección División",
    "Mantenimiento",
    "Abastecimiento y PCP",
    "GICASH",
    "Capital Humano",
    "Ing. Procesos",
    "Matricería",
    "Administración",
    "Sistemas",
    "Sin Definir",
    "Ing. Desarrollo",
    "Producción UT1-2",
    "Producción UT3",
    "Producción UT4",
    "Producción UT5",
    "Mecatrónica",
]

DIVISIONES = ["Division Sellado", "División Dirección, Suspensión y Fricción"]

PLANTAS = ["UT1", "UT2", "UT3", "UT4", "UT5"]

USERS_PROV = [
    "Ranea, Mauricio <ranea@taranto.com.ar>",
    "Firmapaz, Alfredo <firmapaz@taranto.com.ar>",
    "Leiva, Mauricio <leivam@taranto.com.ar>",
    "Riveros, Emilio <riveros@taranto.com.ar>",
    "Parra, Francisco <Parraf@taranto.com.ar>",
    "Vazquez, Pilar <vazquezp@taranto.com.ar>",
    "Guillen, Lucas <guillen@taranto.com.ar>",
    "Vera, Juan <veraj@taranto.com.ar>",
    "Brochero, Javier <brochero@taranto.com.ar>",
]

CATEGORIAS = [
    "Mantenimiento Industrial",
    "Sistemas e IT",
    "Matricería y Herramental",
    "Calidad y Procesos",
    "Producción y Logística",
]

SUBCATEGORIAS = {
    "Mantenimiento Industrial": [
        "Maquinaria (Prensas/Inyectoras)",
        "Servicios Generales (Luz/Agua/Gas)",
        "Neumática e Hidráulica",
        "PLC y Automatización",
        "Edificio / Infraestructura",
    ],
    "Sistemas e IT": [
        "Software de Gestión (ERP)",
        "Hardware (PCs/Impresoras)",
        "Redes y Conectividad",
        "Telefonía / Comunicaciones",
        "Cuentas de Usuario y Accesos",
    ],
    "Matricería y Herramental": [
        "Reparación de Matriz",
        "Construcción de Insertos",
        "Pulido y Ajuste",
        "Cambio de Modelo (Set-up)",
        "Afilado de Herramientas",
    ],
    "Calidad y Procesos": [
        "No Conformidad de Producto",
        "Calibración de Instrumentos",
        "Auditoría de Proceso",
        "Mejora Continua (KAIZEN)",
        "Documentación Técnica",
    ],
    "Producción y Logística": [
        "Abastecimiento de Materia Prima",
        "Movimiento de Materiales (Autoelevadores)",
        "Embalaje y Packaging",
        "Planificación y PCP",
        "Scrap / Retrabajo",
    ],
}

PRIORIDADES = ["Baja", "Media", "Alta", "Crítica"]
ESTADOS_TICKET = ["NUEVO", "ASIGNADO", "EN PROCESO", "RESUELTO", "CERRADO"]
ESTADOS_TAREA = ["PENDIENTE", "EN PROCESO", "COMPLETADA", "CANCELADA"]
ROLES = ["Solicitante", "Analista", "Jefe", "Director", "Administrador"]
