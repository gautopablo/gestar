# GESTAR v2.0 - Versión Premium

Esta es la nueva versión estética de GESTAR, diseñada siguiendo los lineamientos de marca de Taranto y tendencias de UI/UX 2026.

## Características
- **Top Bar**: Navegación horizontal persistente.
- **Identidad de Marca**: Colores institucionales (Rojo #d52e25 y Azul #156099).
- **Layout Modular**: Organización en columnas 1:3 para mejor jerarquía visual.
- **Tipografía Premium**: Lato para lectura y Raleway para títulos.

## Cómo ejecutar

1. Definir `AZURE_SQL_CONNECTION_STRING` en forma persistente (PowerShell, una sola vez):

```powershell
[Environment]::SetEnvironmentVariable(
  "AZURE_SQL_CONNECTION_STRING",
  "Driver={ODBC Driver 18 for SQL Server};Server=tcp:server-sql-gestar.database.windows.net,1433;Database=sql-db-gestar;Uid=admin_gestar;Pwd=TU_CLAVE;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;",
  "User"
)
```

2. (Opcional) Ejecutar en Azure SQL Query Editor el script `sql/azure_master_tables.sql`.

3. Ejecutar la app:

```bash
streamlit run app_v2.py
```

## Archivos
- `app_v2.py`: Nueva interfaz premium.
- `db.py` / `models.py`: Capa de datos compartida.
- `sql/azure_master_tables.sql`: Script idempotente para crear tablas maestras en Azure SQL.

---

## Actualización en Producción

Para subir cambios a la versión desplegada en Streamlit Cloud:

```bash
git add .
git commit -m "Actualización interfaz"
git push origin main
```
