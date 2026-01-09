import sqlite3
import sys
import os
from pathlib import Path

# --- LÓGICA DE RUTA PARA .EXE ---
if getattr(sys, 'frozen', False):
    # Si es el archivo .exe, BASE_DIR será la carpeta donde está el ejecutable
    BASE_DIR = Path(sys.executable).parent
else:
    # Si es modo desarrollo (.py), usa la lógica de carpetas actual
    BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "data.db"
# -------------------------------

def conectar():
    # Agregamos timeout para evitar el error de "database is locked"
    return sqlite3.connect(DB_PATH, timeout=10)