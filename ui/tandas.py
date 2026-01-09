from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QComboBox,
    QSpinBox, QDoubleSpinBox, QMessageBox
)
from PySide6.QtCore import Signal # <--- IMPORTANTE
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data.db"

class Tandas(QWidget):
    # Definimos la señal para avisar a otras pestañas
    tanda_creada = Signal()

    def __init__(self):
        super().__init__()
        self.fecha_actual = None
        self.tanda_id_edicion = None # Para saber si estamos editando
        
        layout = QVBoxLayout(self)

        # ---------- FORMULARIO ----------
        form = QHBoxLayout()

        self.referencia = QComboBox()
        self.cargar_referencias()

        self.numero_tanda = QSpinBox()
        self.numero_tanda.setRange(1, 1000)

        self.cantidad = QDoubleSpinBox()
        self.cantidad.setSuffix(" kg")
        self.cantidad.setDecimals(2)
        self.cantidad.setMaximum(100000)

        self.unidades = QSpinBox()
        self.unidades.setRange(0, 10000)
        self.unidades.setSuffix(" und")

        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.btn_guardar.clicked.connect(self.guardar)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setVisible(False)
        self.btn_cancelar.clicked.connect(self.limpiar_formulario)

        for label, widget in [
            ("Tipo", self.referencia),
            ("Tanda", self.numero_tanda),
            ("Kg", self.cantidad),
            ("Unds", self.unidades)
        ]:
            form.addWidget(QLabel(label))
            form.addWidget(widget)

        form.addWidget(self.btn_guardar)
        form.addWidget(self.btn_cancelar)
        layout.addLayout(form)

        # ---------- TABLA ----------
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels(["ID", "Fecha", "Tipo", "Tanda", "Kg", "Unidades"])
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows) # Selección de fila completa
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.tabla)

        # ---------- ACCIONES ----------
        acciones = QHBoxLayout()
        self.btn_editar = QPushButton("✏️ Editar")
        self.btn_editar.clicked.connect(self.preparar_edicion)
        
        self.btn_eliminar = QPushButton("🗑️ Eliminar")
        self.btn_eliminar.setStyleSheet("color: red;")
        self.btn_eliminar.clicked.connect(self.eliminar)
        
        acciones.addWidget(self.btn_editar)
        acciones.addWidget(self.btn_eliminar)
        acciones.addStretch()
        layout.addLayout(acciones)

    def conectar(self):
        return sqlite3.connect(DB_PATH, timeout=10)

    def cargar_referencias(self):
        try:
            conn = self.conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre FROM referencias_chorizo")
            self.referencia.clear()
            for ref_id, nombre in cursor.fetchall():
                self.referencia.addItem(nombre, ref_id)
            conn.close()
        except Exception as e: print(e)

    def cargar_tandas(self):
        self.tabla.setRowCount(0)
        if not self.fecha_actual: return

        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT t.id, t.fecha, r.nombre, t.numero_tanda, t.cantidad_producida, t.unidades
        FROM tandas t
        JOIN referencias_chorizo r ON r.id = t.referencia_id
        WHERE t.fecha = ?
        ORDER BY t.numero_tanda
        """, (self.fecha_actual,))

        for fila, datos in enumerate(cursor.fetchall()):
            self.tabla.insertRow(fila)
            for col, valor in enumerate(datos):
                self.tabla.setItem(fila, col, QTableWidgetItem(str(valor)))
        conn.close()

    def guardar(self):
        if not self.fecha_actual: return

        conn = None
        try:
            conn = self.conectar()
            cursor = conn.cursor()

            if self.tanda_id_edicion:
                # ACTUALIZAR
                cursor.execute("""
                UPDATE tandas SET numero_tanda=?, referencia_id=?, cantidad_producida=?, unidades=?
                WHERE id=?
                """, (self.numero_tanda.value(), self.referencia.currentData(), 
                      self.cantidad.value(), self.unidades.value(), self.tanda_id_edicion))
            else:
                # INSERTAR NUEVO
                cursor.execute("""
                INSERT INTO tandas (fecha, numero_tanda, referencia_id, cantidad_producida, unidades)
                VALUES (?, ?, ?, ?, ?)
                """, (self.fecha_actual, self.numero_tanda.value(), self.referencia.currentData(), 
                      self.cantidad.value(), self.unidades.value()))

            conn.commit()
            
            # EMITIR SEÑAL PARA OTRAS PESTAÑAS
            self.tanda_creada.emit()
            
            self.limpiar_formulario()
            self.cargar_tandas()

        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "Error", "Esta tanda ya existe para este producto hoy.")
        finally:
            if conn: conn.close()

    def preparar_edicion(self):
        fila = self.tabla.currentRow()
        if fila < 0: return
        
        self.tanda_id_edicion = self.tabla.item(fila, 0).text()
        self.referencia.setCurrentText(self.tabla.item(fila, 2).text())
        self.numero_tanda.setValue(int(self.tabla.item(fila, 3).text()))
        self.cantidad.setValue(float(self.tabla.item(fila, 4).text()))
        self.unidades.setValue(int(self.tabla.item(fila, 5).text()))
        
        self.btn_guardar.setText("Actualizar")
        self.btn_guardar.setStyleSheet("background-color: #2196F3; color: white;")
        self.btn_cancelar.setVisible(True)

    def eliminar(self):
        fila = self.tabla.currentRow()
        if fila < 0: return
        
        id_tanda = self.tabla.item(fila, 0).text()
        res = QMessageBox.question(self, "Confirmar", "¿Eliminar esta tanda?", QMessageBox.Yes | QMessageBox.No)
        
        if res == QMessageBox.Yes:
            conn = self.conectar()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tandas WHERE id=?", (id_tanda,))
            conn.commit()
            conn.close()
            self.tanda_creada.emit() # Avisar que se borró algo
            self.cargar_tandas()

    def limpiar_formulario(self):
        self.tanda_id_edicion = None
        self.cantidad.setValue(0)
        self.unidades.setValue(0)
        self.btn_guardar.setText("Guardar")
        self.btn_guardar.setStyleSheet("background-color: #4CAF50; color: white;")
        self.btn_cancelar.setVisible(False)

    def set_fecha(self, fecha):
        self.fecha_actual = fecha
        self.cargar_tandas()