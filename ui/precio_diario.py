from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QDateEdit, QMessageBox, QSpinBox, QHeaderView
)
from PySide6.QtCore import QDate, Qt
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data.db"

class PrecioDiario(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Análisis de Costos y Precios")
        self.resize(700, 450)

        layout = QVBoxLayout(self)

        # -------- CONTROLES SUPERIORES --------
        top = QHBoxLayout()
        
        self.fecha = QDateEdit()
        self.fecha.setCalendarPopup(True)
        self.fecha.setDate(QDate.currentDate())
        self.fecha.dateChanged.connect(self.cargar_precios)

        self.margen = QSpinBox()
        self.margen.setRange(0, 500)
        self.margen.setSuffix("%")
        self.margen.setValue(30) # Margen por defecto
        self.margen.valueChanged.connect(self.calcular_sugeridos)

        top.addWidget(QLabel("Fecha:"))
        top.addWidget(self.fecha)
        top.addSpacing(20)
        top.addWidget(QLabel("Margen de Ganancia:"))
        top.addWidget(self.margen)
        top.addStretch()
        
        layout.addLayout(top)

        # -------- TABLA EXTENDIDA --------
        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels([
            "Referencia", "Costo Real/Kg", "Precio Sugerido", "Precio de Venta"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabla)

        # -------- BOTÓN --------
        self.btn_guardar = QPushButton("💾 Guardar Precios de Venta")
        self.btn_guardar.setStyleSheet("height: 40px; font-weight: bold;")
        self.btn_guardar.clicked.connect(self.guardar)
        layout.addWidget(self.btn_guardar)

        self.referencias = []
        self.cargar_referencias_base()
        self.cargar_precios()

    def conectar(self):
        return sqlite3.connect(DB_PATH)

    def cargar_referencias_base(self):
        """Obtiene las referencias y calcula su costo promedio histórico"""
        conn = self.conectar()
        cursor = conn.cursor()
        
        # Esta consulta calcula el costo promedio por kilo basado en las tandas
        cursor.execute("""
            SELECT 
                r.id, 
                r.nombre,
                IFNULL(AVG(tm.total / t.cantidad_producida), 0) as costo_promedio
            FROM referencias_chorizo r
            LEFT JOIN tandas t ON r.id = t.referencia_id
            LEFT JOIN tanda_materia_prima tm ON t.id = tm.tanda_id
            GROUP BY r.id
        """)
        self.referencias = cursor.fetchall()
        conn.close()

    def calcular_sugeridos(self):
        """Recalcula la columna de precio sugerido según el margen"""
        porcentaje = self.margen.value() / 100
        for fila in range(self.tabla.rowCount()):
            try:
                costo = float(self.tabla.item(fila, 1).text().replace("$ ", ""))
                sugerido = costo * (1 + porcentaje)
                item_sugerido = QTableWidgetItem(f"$ {sugerido:.2f}")
                item_sugerido.setFlags(Qt.ItemIsEnabled) # No editable
                item_sugerido.setForeground(Qt.blue)
                self.tabla.setItem(fila, 2, item_sugerido)
            except:
                pass

    def cargar_precios(self):
        self.cargar_referencias_base() # Refrescar costos
        fecha = self.fecha.date().toString("yyyy-MM-dd")
        
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT referencia_id, precio_venta FROM precio_chorizo_dia WHERE fecha = ?", (fecha,))
        precios_guardados = {r: p for r, p in cursor.fetchall()}
        conn.close()

        self.tabla.setRowCount(len(self.referencias))

        for fila, (ref_id, nombre, costo) in enumerate(self.referencias):
            # 1. Nombre
            item_nombre = QTableWidgetItem(nombre)
            item_nombre.setFlags(Qt.ItemIsEnabled)
            self.tabla.setItem(fila, 0, item_nombre)

            # 2. Costo Real (Calculado de la DB)
            item_costo = QTableWidgetItem(f"{costo:.2f}")
            item_costo.setFlags(Qt.ItemIsEnabled)
            self.tabla.setItem(fila, 1, item_costo)

            # 3. Precio de Venta (Traído de la DB o 0 si es nuevo)
            precio_actual = precios_guardados.get(ref_id, 0)
            self.tabla.setItem(fila, 3, QTableWidgetItem(f"{precio_actual:.2f}"))

        self.calcular_sugeridos()

    def guardar(self):
        fecha = self.fecha.date().toString("yyyy-MM-dd")
        conn = self.conectar()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM precio_chorizo_dia WHERE fecha = ?", (fecha,))
            for fila in range(self.tabla.rowCount()):
                ref_id = self.referencias[fila][0]
                precio_texto = self.tabla.item(fila, 3).text()
                precio = float(precio_texto)
                
                cursor.execute("""
                    INSERT INTO precio_chorizo_dia (fecha, referencia_id, precio_venta)
                    VALUES (?, ?, ?)
                """, (fecha, ref_id, precio))

            conn.commit()
            QMessageBox.information(self, "Éxito", "Precios de venta actualizados correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar: {str(e)}")
        finally:
            conn.close()