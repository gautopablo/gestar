# GESTAR - Gestión de Solicitudes y Tareas

Sistema MVP para la gestión interna de tickets y tareas.

## Tecnologías

- Python 3.x
- Streamlit
- SQLite

## Instalación

1. Instalar dependencias:

   ```bash
   pip install -r requirements.txt
   ```

2. Ejecutar la aplicación:

   ```bash
   streamlit run app.py
   ```

## Actualización de la App Desplegada

La aplicación en **Streamlit Community Cloud** se actualiza automáticamente al detectar cambios en el repositorio de GitHub. Para subir tus cambios:

1. **Asegúrate de guardar tus cambios locales:**

   ```bash
   git add .
   git commit -m "Descripción de los cambios"
   ```

2. **Sube los cambios a GitHub:**

   ```bash
   git push origin main
   ```

3. **Verificación:**

   La app se actualizará en unos segundos. Puedes ver el estado en el panel de control de Streamlit Cloud.

## Funcionalidades (V2 MVP)

- **Simulación de Sesión**: Sidebar para cambiar de usuario, rol (Analista, Jefe, Director) y área.
- **Cola de Tickets**: Vista de tickets "Nuevos" específicos para el área del usuario.
- **Flujo de Trabajo**:
  - Tickets nacen en estado `NUEVO`.
  - Acción **"Tomar Ticket"** para autoasignación.
  - Estados: `NUEVO` -> `ASIGNADO` -> `EN PROCESO` -> `RESUELTO`.
- **Creación Detallada**: Separación de Urgencia (Solicitante) y Prioridad (Analista).
- **Auditoría**: Registro de quién creó el ticket y fechas de actualización `updated_at`.
- **Persistencia**: Base de datos SQLite local (`gestar.db`).
