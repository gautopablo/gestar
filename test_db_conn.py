import os
import re

import pyodbc


def _normalize_encrypt(conn_str: str) -> str:
    # Elimina cualquier Encrypt existente y fuerza Encrypt=yes
    if re.search(r"(?i)Encrypt\s*=", conn_str):
        conn_str = re.sub(r"(?i)Encrypt\s*=\s*[^;]*", "Encrypt=yes", conn_str)
    else:
        conn_str = conn_str + ";Encrypt=yes"
    return conn_str


def _normalize_trust_server_cert(conn_str: str) -> str:
    # Fuerza TrustServerCertificate=no (Driver 18 acepta yes/no, no true/false/0/1)
    if re.search(r"(?i)TrustServerCertificate\s*=", conn_str):
        conn_str = re.sub(
            r"(?i)TrustServerCertificate\s*=\s*[^;]*",
            "TrustServerCertificate=no",
            conn_str,
        )
    else:
        conn_str = conn_str + ";TrustServerCertificate=no"
    return conn_str


def _mask_pwd(conn_str: str) -> str:
    return re.sub(r"(?i)(Pwd|Password)\s*=\s*[^;]*", r"\1=***", conn_str)


def main() -> None:
    conn_str = os.environ.get("AZURE_SQL_CONNECTION_STRING")
    if not conn_str:
        raise RuntimeError("AZURE_SQL_CONNECTION_STRING no esta definido")

    conn_str = _normalize_encrypt(conn_str)
    conn_str = _normalize_trust_server_cert(conn_str)
    print("ConnStr:", _mask_pwd(conn_str))

    print("Probando conexion...")
    conn = pyodbc.connect(conn_str, timeout=10)
    cur = conn.cursor()
    cur.execute("SELECT 1")
    print("OK:", cur.fetchone()[0])
    conn.close()


if __name__ == "__main__":
    main()
