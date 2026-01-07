# Documentación del Proyecto GESTAR

GESTAR es un sistema de gestión de solicitudes (tickets) y tareas diseñado para facilitar la coordinación interna entre diferentes áreas de la organización. El sistema permite el seguimiento completo desde la creación de una solicitud hasta su resolución final.

## 🏗 Arquitectura del Sistema

El proyecto sigue una estrategia de evolución por etapas, pasando de una base local a una solución empresarial en la nube.

### Arquitectura Actual (Inicial y Básica)

Orientada a un MVP (Producto Mínimo Viable) de rápida iteración:

- **Frontend**: Desarrollado con [Streamlit](https://streamlit.io/), proporcionando una interfaz web interactiva y reactiva.
- **Backend/Lógica**: Python 3.x manejando la lógica de negocio y procesamiento de datos.
- **Base de Datos**: [SQLite](https://www.sqlite.org/) local (`gestar.db`).

### Arquitectura Final (Objetivo)

Orientada a escalabilidad, seguridad y alta disponibilidad:

- **Infraestructura**: Despliegue en **Azure App Service**.
- **Base de Datos**: **Azure SQL Database** (SQL Server).
- **Autenticación**: Integración con Azure AD (Entra ID).

## 🗺 Hoja de Ruta y Etapas (Roadmap)

Para alcanzar la arquitectura final, se han definido las siguientes etapas de transición:

### Etapa 1: MVP Local (Actual)

- Validación de funcionalidades principales.
- Uso de SQLite y servidor local.
- Definición de modelos de datos y flujos de trabajo.

### Etapa 2: Migración de Datos y Módulo de Administración

- Migración de la base de datos de SQLite a **SQL Server**.
- Creación de **Tablas Maestras** (Usuarios, Áreas, Divisiones, Plantas, Categorías) en la base de datos.
- Implementación de un **Módulo de Administración** dentro de la app para gestionar estas tablas de forma dinámica (CRUD).
- Refactorización de la capa de datos en `db.py` para compatibilidad con SQL Server.

### Etapa 3: Despliegue en la Nube

- Configuración de **Azure App Service** para el alojamiento de la aplicación Streamlit.
- Implementación de variables de entorno seguras para credenciales.
- Pruebas de rendimiento y latencia en la nube.

### Etapa 4: Seguridad y Escalabilidad

- Gestión de identidades mediante Azure Active Directory.
- Implementación de respaldos automatizados en Azure SQL.
- Optimización de consultas y monitoreo (Azure Monitor / Application Insights).

## 📊 Modelos de Datos

El sistema utiliza tres tablas principales en la base de datos:

1. **`tickets`**: Almacena la información principal de la solicitud.
   - Campos: Título, descripción, área destino, categoría, subcategoría, división, planta, prioridad, urgencia, responsables, estado, solicitante y marcas de tiempo.
2. **`tasks`**: Tareas específicas asociadas a un ticket.
   - Cada ticket puede tener múltiples tareas asignadas a diferentes responsables.
3. **`ticket_log`**: Historial de eventos y comentarios.
   - Registra cambios de estado, asignaciones y comentarios de los usuarios para auditoría completa.

## 📋 Tablas Auxiliares (Maestras)

El sistema utiliza las siguientes listas de valores predefinidos (definidas en `models.py`):

### Área Destino (`AREAS`)

A continuación se detallan las áreas oficiales y sus líderes a cargo:

| Área | Lider Area |
| :--- | :--- |
| Dirección División | Cane, Alejandro |
| Mantenimiento | Fabregas, Maria Ester |
| Abastecimiento y PCP | Gutierrez, Sebastian |
| GICASH | D´Asta, Fabiola |
| Capital Humano | Caballero, Cecilia |
| Ing. Procesos | Ranea, Mauricio |
| Matricería | Bumjeil, Alfonso |
| Administración | Furlani, Noelia |
| Sistemas | Llado, Damian |
| Sin Definir | Gauto, Pablo |
| Ing. Desarrollo | Sanchez Palma, Pablo Ernesto |
| Producción UT1-2 | Aguero, Jorge |
| Producción UT3 | Poblete, Victor / Aguero, Gaston |
| Producción UT4 | Vargas Ricardo |
| Producción UT5 | Fiol, Sebastian |
| Mecatrónica | Turchetti, Cecilia |

### Categorías y Subcategorías

Diseñadas específicamente para el entorno de fabricación de autopartes:

1. **Mantenimiento Industrial**
   - Maquinaria (Prensas/Inyectoras)
   - Servicios Generales (Luz/Agua/Gas)
   - Neumática e Hidráulica
   - PLC y Automatización
   - Edificio / Infraestructura

2. **Sistemas e IT**
   - Software de Gestión (ERP)
   - Hardware (PCs/Impresoras)
   - Redes y Conectividad
   - Telefonía / Comunicaciones
   - Cuentas de Usuario y Accesos

3. **Matricería y Herramental**
   - Reparación de Matriz
   - Construcción de Insertos
   - Pulido y Ajuste
   - Cambio de Modelo (Set-up)
   - Afilado de Herramientas

4. **Calidad y Procesos**
   - No Conformidad de Producto
   - Calibración de Instrumentos
   - Auditoría de Proceso
   - Mejora Continua (KAIZEN)
   - Documentación Técnica

5. **Producción y Logística**
   - Abastecimiento de Materia Prima
   - Movimiento de Materiales (Autoelevadores)
   - Embalaje y Packaging
   - Planificación y PCP
   - Scrap / Retrabajo

### Prioridades / Urgencias (`PRIORIDADES`)

- Baja
- Media
- Alta
- Crítica

### Estados del Ticket (`ESTADOS_TICKET`)

- **NUEVO**: Recién creado, pendiente de revisión.
- **ASIGNADO**: Tiene un responsable definido.
- **EN PROCESO**: Se están realizando tareas.
- **RESUELTO**: El problema ha sido solucionado.
- **CERRADO**: Versión final del ticket tras validación.

### Estados de Tarea (`ESTADOS_TAREA`)

- PENDIENTE
- EN PROCESO
- COMPLETADA
- CANCELADA

### Divisiones (`DIVISIONES`)

- Division Sellado
- División Dirección, Suspensión y Fricción

### Plantas (`PLANTAS`)

- UT1
- UT2
- UT3
- UT4
- UT5

### Usuarios y Perfiles (`users`)

Para la simulación actual de identidades, se utiliza la siguiente lista provisional:

- Ranea, Mauricio <ranea@taranto.com.ar>
- Firmapaz, Alfredo <firmapaz@taranto.com.ar>
- Leiva, Mauricio <leivam@taranto.com.ar>
- Riveros, Emilio <riveros@taranto.com.ar>
- Parra, Francisco <Parraf@taranto.com.ar>
- Vazquez, Pilar <vazquezp@taranto.com.ar>
- Guillen, Lucas <guillen@taranto.com.ar>
- Vera, Juan <veraj@taranto.com.ar>
- Brochero, Javier <brochero@taranto.com.ar>

En el futuro, esta información se gestionará dinámicamente:

- **Usuario**: ID de red o correo.
- **Rol**: Nivel de acceso (Solicitante, Analista, Jefe, etc.).
- **Área**: Área a la que pertenece el usuario.

### Gestión de Maestras (Futuro)

En la versión final, las listas anteriores dejarán de ser constantes en el código para ser tablas editables por el **Administrador**.

## 👤 Roles y Permisos

El sistema simula un contexto de sesión con los siguientes roles:

- **Solicitante**: Puede crear tickets y consultar el estado de sus solicitudes.
- **Analista**: Encargado de tomar tickets, definir prioridades y gestionar tareas.
- **Jefe**: Tiene visibilidad de los tickets de su área y puede asignar responsables.
- **Director**: Acceso global y capacidad de supervisión en todas las áreas.
- **Administrador**: Responsable de la gestión de usuarios, roles, áreas y mantenimiento de las tablas maestras.

## 🖥 Navegación y Paneles de la App

La interfaz de GESTAR se organiza mediante una barra lateral de navegación y cuatro paneles principales:

### 🛠 Barra Lateral (Sidebar)

- **Simulación de Sesión**: Permite cambiar el **Usuario Actual**. Al seleccionarlo, el **Rol** y el **Área** se muestran automáticamente como campos de solo lectura (lectura desde la Base de Datos). Esto condiciona qué tickets son visibles y qué acciones están permitidas.
- **Selector de Página**: Navegación entre los paneles principales. El panel de "Administración" solo es visible para usuarios con rol `Administrador`.

### 📝 Panel: Crear Ticket

- **Función**: Formulario de ingreso para nuevas solicitudes.
- **Campos**: Título y descripción (obligatorios), Área Destino, Categoria, Subcategoría, Urgencia Sugerida, Categoría, División, Planta y Responsable Sugerido.
- **Resultado**: Crea un ticket en estado `NUEVO`.

### 📥 Panel: Bandeja de Tickets

Es el centro operativo, dividido en pestañas de filtrado rápido:

- **🔴 Cola (Nuevos)**: Muestra tickets en estado `NUEVO` que pertenecen al área del usuario actual (o todos si es Director).
- **👤 Mis Asignados**: Lista los tickets asignados al usuario actual en estados `ASIGNADO` o `EN PROCESO`.
- **🟡 En Proceso**: Vista de todos los tickets activos, con capacidad de filtrar por área.
- **🟢 Cerrados**: Historial de tickets con estado `RESUELTO` o `CERRADO`.
- **📋 Todos**: Listado completo con buscador y filtros avanzados.

Desde cualquier pestaña se puede seleccionar un ID de ticket y hacer clic en **"Ver Detalle"** para gestionarlo.

### 🔍 Panel: Detalle de Ticket

Vista completa para la gestión individual de un ticket:

- **Acciones**: Botón de **"Tomar Ticket"** (autoasignación) si el ticket está nuevo.
- **Gestión**: Formulario para cambiar Prioridad, Estado y Asignar Responsable (permisos según rol).
- **Información**: Despliegue de todos los datos de creación y marcas de tiempo.
- **Tareas**: Lista de tareas asociadas con opción de marcar como completadas y agregar nuevas.
- **Historial**: Chat/Log cronológico que muestra comentarios y cambios de estado.

### 👤 Panel: Mis Tareas

- **Función**: Vista simplificada que muestra exclusivamente las tareas pendientes (individuales, no tickets) que tienen al usuario actual como responsable.

## 🔄 Flujo de Trabajo (Lifecycle)

1. **Creación**: Un usuario crea un ticket (`Estado: NUEVO`). Se define una *Urgencia Sugerida*.
2. **Asignación**: Un responsable toma el ticket o es asignado por un jefe (`Estado: ASIGNADO`). Se define la *Prioridad* real.
3. **Ejecución**: Se crean tareas y se trabaja en la solicitud (`Estado: EN PROCESO`).
4. **Resolución**: Una vez completadas las tareas, el ticket se marca como `RESUELTO` o `CERRADO`.

## 📂 Estructura del Código

- `app.py`: Punto de entrada de la aplicación Streamlit. Contiene toda la interfaz de usuario y navegación.
- `db.py`: Capa de acceso a datos. Contiene las funciones CRUD (Crear, Leer, Actualizar, Borrar) y gestión de la conexión.
- `models.py`: Definición de los esquemas de tablas SQL y constantes del sistema (áreas, estados, prioridades).
- `requirements.txt`: Lista de dependencias del proyecto.

## 🚀 Instalación y Ejecución

1. Asegúrese de tener Python instalado.
2. Instale las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

3. Ejecute la aplicación:

   ```bash
   streamlit run app.py
   ```
