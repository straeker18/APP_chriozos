from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem, 
    QDateEdit, QPushButton, QHeaderView
)
from PySide6.QtCore import QDate
import sqlite3
from ..db.conexion import conectar

class InventarioProductoFinal(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Resumen de Producción Diaria (Producto Terminado)")

        layout = QVBoxLayout(self)

        # ---- FILTROS (Para buscar por día) ----
        filtros_layout = QHBoxLayout()
        
        self.fecha_busqueda = QDateEdit()
        self.fecha_busqueda.setCalendarPopup(True)
        self.fecha_busqueda.setDate(QDate.currentDate())
        self.fecha_busqueda.dateChanged.connect(self.cargar_datos) # Actualiza al cambiar fecha

        btn_hoy = QPushButton("Ver Hoy")
        btn_hoy.clicked.connect(lambda: self.fecha_busqueda.setDate(QDate.currentDate()))

        filtros_layout.addWidget(QLabel("Seleccionar Fecha:"))
        filtros_layout.addWidget(self.fecha_busqueda)
        filtros_layout.addWidget(btn_hoy)
        filtros_layout.addStretch()
        
        layout.addLayout(filtros_layout)

        # ---- TABLA DE CHORIZOS HECHOS ----
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(
            ["Referencia", "Total Tandas", "Kg Totales", "Unds Totales", "Costo Promedio"]
        )
        # Hacer que las columnas ocupen el espacio
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.tabla)

        # ---- RESUMEN INFERIOR ----
        self.label_resumen = QLabel("Cargando datos...")
        self.label_resumen.setStyleSheet("font-weight: bold; font-size: 13px; color: #2c3e50;")
        layout.addWidget(self.label_resumen)

        self.cargar_datos()

    def cargar_datos(self):
        """Consulta las tandas realizadas en la fecha seleccionada"""
        fecha_str = self.fecha_busqueda.date().toString("yyyy-MM-dd")
        
        conn = None
        try:
            conn = conectar()
            cursor = conn.cursor()

            # Agrupamos por referencia para ver el total de chorizos hechos de cada tipo
            query = """
                SELECT 
                    r.nombre,
                    COUNT(t.id) as num_tandas,
                    SUM(t.cantidad_producida) as kg_totales,
                    SUM(t.unidades) as unds_totales,
                    AVG(t.cantidad_producida) -- Simulación de costo o dato extra
                FROM tandas t
                JOIN referencias_chorizo r ON r.id = t.referencia_id
                WHERE t.fecha = ?
                GROUP BY r.nombre
            """
            cursor.execute(query, (fecha_str,))
            datos = cursor.fetchall()

            self.tabla.setRowCount(len(datos))
            
            total_kg = 0
            total_unds = 0

            for fila, row in enumerate(datos):
                # Referencia
                self.tabla.setItem(fila, 0, QTableWidgetItem(str(row[0])))
                # Cantidad de tandas
                self.tabla.setItem(fila, 1, QTableWidgetItem(str(row[1])))
                # Kg totales
                self.tabla.setItem(fila, 2, QTableWidgetItem(f"{row[2]:.2f} kg"))
                # Unidades totales
                self.tabla.setItem(fila, 3, QTableWidgetItem(f"{row[3]} und"))
                # Un dato de referencia o costo si lo tienes
                self.tabla.setItem(fila, 4, QTableWidgetItem("--"))
                
                total_kg += row[2]
                total_unds += row[3]

            self.label_resumen.setText(
                f"Resumen del {fecha_str}: Total {total_kg:.2f} kg producidos en {total_unds} unidades."
            )

        except Exception as e:
            print(f"Error al consultar producción: {e}")
        finally:
            if conn:
                conn.close()