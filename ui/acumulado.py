from PySide6.QtWidgets import (
    QWidget, QVBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView
)
from datetime import datetime
import sqlite3
from ..db.conexion import conectar


class AcumuladoMensual(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Acumulado Mensual de Producción")

        layout = QVBoxLayout(self)

        # Configurar Mes y Año actual para el título
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        ahora = datetime.now()
        nombre_mes = meses[ahora.month - 1]
        
        titulo = QLabel(f"Chorizos Producidos: {nombre_mes} {ahora.year}")
        titulo.setStyleSheet("font-size:18px; font-weight:bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(titulo)

        # Tabla configurada para Producto Terminado
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(
            ["Referencia", "Total Tandas", "Total Kilos", "Total Unidades"]
        )
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(self.tabla)

        self.cargar_datos()

    def cargar_datos(self):
        conn = None
        try:
            conn = conectar()
            cursor = conn.cursor()

            # Obtenemos mes y año actual en formato (01, 02, etc)
            mes_actual = datetime.now().strftime("%m")
            anio_actual = datetime.now().strftime("%Y")

            # Consulta para agrupar la producción de chorizos por tipo
            cursor.execute("""
                SELECT 
                    r.nombre,
                    COUNT(t.id) as total_tandas,
                    SUM(t.cantidad_producida) as total_kilos,
                    SUM(t.unidades) as total_unidades
                FROM tandas t
                JOIN referencias_chorizo r ON r.id = t.referencia_id
                WHERE strftime('%m', t.fecha) = ? AND strftime('%Y', t.fecha) = ?
                GROUP BY r.nombre
                ORDER BY total_kilos DESC
            """, (mes_actual, anio_actual))

            datos = cursor.fetchall()
            self.tabla.setRowCount(len(datos))

            for fila, row in enumerate(datos):
                # Referencia
                self.tabla.setItem(fila, 0, QTableWidgetItem(str(row[0])))
                # Total Tandas
                self.tabla.setItem(fila, 1, QTableWidgetItem(str(row[1])))
                # Total Kilos
                self.tabla.setItem(fila, 2, QTableWidgetItem(f"{row[2]:.2f} kg"))
                # Total Unidades (Chorizos individuales)
                self.tabla.setItem(fila, 3, QTableWidgetItem(f"{row[3]} und"))

        except Exception as e:
            print(f"Error al cargar acumulado de chorizos: {e}")
        finally:
            if conn:
                conn.close()