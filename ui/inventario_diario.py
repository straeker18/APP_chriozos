from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem,
    QDateEdit
)
from PySide6.QtCore import QDate
from ..db.conexion import conectar


class InventarioDiario(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inventario Diario")
        self.resize(600, 400)

        layout = QVBoxLayout(self)

        # -------- FECHA --------
        top = QHBoxLayout()
        self.fecha = QDateEdit()
        self.fecha.setCalendarPopup(True)
        self.fecha.setDate(QDate.currentDate())
        self.fecha.dateChanged.connect(self.cargar)

        top.addWidget(QLabel("Fecha"))
        top.addWidget(self.fecha)
        layout.addLayout(top)

        # -------- TABLA --------
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(
            ["Materia Prima", "Cantidad Usada", "Unidad"]
        )
        layout.addWidget(self.tabla)

        self.cargar()

    # -----------------------
    def cargar(self):
        fecha = self.fecha.date().toString("yyyy-MM-dd")

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT i.nombre,
               SUM(tm.cantidad_usada),
               i.unidad
        FROM tanda_materia_prima tm
        JOIN tandas t ON t.id = tm.tanda_id
        JOIN inventario_materia_prima i ON i.id = tm.materia_prima_id
        WHERE t.fecha = ?
        GROUP BY i.nombre
        """, (fecha,))

        datos = cursor.fetchall()
        conn.close()

        self.tabla.setRowCount(len(datos))
        for f, row in enumerate(datos):
            for c, val in enumerate(row):
                self.tabla.setItem(f, c, QTableWidgetItem(str(val)))
