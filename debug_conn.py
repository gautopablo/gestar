import pyodbc
import time
import sys

# Reducimos el timeout en la cadena de conexión para que falle rápido si no hay respuesta del servidor
conn_str = "Driver={ODBC Driver 18 for SQL Server};Server=tcp:server-sql-gestar.database.windows.net,1433;Database=sql-db-gestar;Uid=admin_gestar;Pwd=Taranto.26;Encrypt=yes;TrustServerCertificate=yes;"


def test_conn():
    print(f"Probando conexión a Azure SQL...")
    print(f"Servidor: server-sql-gestar.database.windows.net")
    try:
        print("Intentando conectar (timeout=5s)...")
        start_time = time.time()
        # El parámetro timeout aquí también ayuda
        conn = pyodbc.connect(conn_str, timeout=5)
        print(f"CONEXIÓN ESTABLECIDA en {time.time() - start_time:.2f} segundos.")

        cur = conn.cursor()
        print("Ejecutando consulta de prueba (SELECT 1)...")
        cur.execute("SELECT 1")
        result = cur.fetchone()[0]
        print(f"RESULTADO EXITOSO: {result}")
        conn.close()
    except pyodbc.Error as e:
        print(f"\nERROR DE ODBC:")
        print(f"SQLState: {e.args[0]}")
        print(f"Mensaje: {e.args[1]}")
    except Exception as e:
        print(f"\nERROR INESPERADO:")
        print(f"Tipo: {type(e).__name__}")
        print(f"Detalle: {e}")

    print("\nSi la conexión falló por timeout, lo más probable es que tu IP actual")
    print("no esté habilitada en el firewall de Azure SQL.")


if __name__ == "__main__":
    test_conn()
