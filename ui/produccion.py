from PySide6.QtWidgets import ( # type: ignore
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox
)

from ..db.conexion import conectar


class ProduccionDiaria(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Producción Diaria")

        layout = QVBoxLayout()

        # ---- FORMULARIO ----
        form_layout = QHBoxLayout()

        self.fecha = QLineEdit()
        self.insumo = QLineEdit()
        self.cantidad = QLineEdit()
        self.costo = QLineEdit()

        form_layout.addWidget(QLabel("Fecha"))
        form_layout.addWidget(self.fecha)
        form_layout.addWidget(QLabel("Insumo"))
        form_layout.addWidget(self.insumo)
        form_layout.addWidget(QLabel("Cantidad"))
        form_layout.addWidget(self.cantidad)
        form_layout.addWidget(QLabel("Costo Unitario"))
        form_layout.addWidget(self.costo)

        layout.addLayout(form_layout)

        # ---- BOTÓN ----
        btn_guardar = QPushButton("Guardar Producción")
        btn_guardar.clicked.connect(self.guardar)
        layout.addWidget(btn_guardar)

        # ---- TABLA ----
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(
            ["Fecha", "Insumo", "Cantidad", "Costo Unitario", "Total"]
        )

        layout.addWidget(self.tabla)

        self.setLayout(layout)
        self.cargar_datos()

    # -------------------------------
    def guardar(self):
        try:
            fecha = self.fecha.text()
            insumo = self.insumo.text()
            cantidad = float(self.cantidad.text())
            costo = float(self.costo.text())
            total = cantidad * costo

            conn = conectar()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO produccion_diaria
                (fecha, insumo, cantidad, costo_unitario, total)
                VALUES (?, ?, ?, ?, ?)
            """, (fecha, insumo, cantidad, costo, total))

            conn.commit()
            conn.close()

            self.fecha.clear()
            self.insumo.clear()
            self.cantidad.clear()
            self.costo.clear()

            self.cargar_datos()

        except ValueError:
            QMessageBox.warning(self, "Error", "Cantidad y costo deben ser numéricos")

    # -------------------------------
    def cargar_datos(self):
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT fecha, insumo, cantidad, costo_unitario, total
            FROM produccion_diaria
            ORDER BY fecha
        """)

        datos = cursor.fetchall()
        conn.close()

        self.tabla.setRowCount(len(datos))

        for fila, row in enumerate(datos):
            for columna, valor in enumerate(row):
                self.tabla.setItem(fila, columna, QTableWidgetItem(str(valor)))
