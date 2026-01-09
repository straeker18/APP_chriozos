from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QDoubleSpinBox, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data.db"


class MateriaPrimaTanda(QWidget):
    # Señal que se emite cuando se usa materia prima
    stock_actualizado = Signal()
    
    def __init__(self):
        super().__init__()
        self.fecha_actual = None

        layout = QVBoxLayout(self)

        # ---------- FORM ----------
        form = QHBoxLayout()

        self.tanda = QComboBox()
        self.tanda.currentIndexChanged.connect(self.cargar_detalle)

        self.materia = QComboBox()
        
        self.cantidad = QDoubleSpinBox()
        self.cantidad.setDecimals(3)
        self.cantidad.setMaximum(100000)
        self.cantidad.valueChanged.connect(self.validar_cantidad)

        # Label para mostrar stock disponible (CREAR ANTES de cargar_materias)
        self.stock_label = QLabel("Stock disponible: --")
        self.stock_label.setStyleSheet("color: blue; font-weight: bold;")
        
        # Cargar materias DESPUÉS de crear todos los widgets
        self.materia.currentIndexChanged.connect(self.actualizar_stock_disponible)
        self.cargar_materias()

        self.btn_agregar = QPushButton("Agregar")
        self.btn_agregar.clicked.connect(self.agregar)

        # Botón de refrescar
        self.btn_refrescar = QPushButton("🔄")
        self.btn_refrescar.setMaximumWidth(40)
        self.btn_refrescar.setToolTip("Actualizar stock disponible")
        self.btn_refrescar.clicked.connect(self.refrescar_stock)

        for label, widget in [
            ("Tanda", self.tanda),
            ("Materia Prima", self.materia),
            ("Cantidad usada (kg)", self.cantidad)
        ]:
            form.addWidget(QLabel(label))
            form.addWidget(widget)

        form.addWidget(self.stock_label)
        form.addWidget(self.btn_refrescar)
        form.addWidget(self.btn_agregar)
        layout.addLayout(form)

        # ---------- TABLA ----------
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(
            ["Materia Prima", "Cantidad", "Costo Unit.", "Total"]
        )
        layout.addWidget(self.tabla)

        self.total_label = QLabel("Total Tanda: 0.00")
        layout.addWidget(self.total_label)

    # ---------------------------------
    def set_fecha(self, fecha):
        self.fecha_actual = fecha
        self.cargar_tandas()
        self.cargar_detalle()

    # ---------------------------------
    def conectar(self):
        return sqlite3.connect(DB_PATH)

    # ---------------------------------
    def cargar_tandas(self):
        # Guardamos que ID estaba seleccionado antes de borrar
        id_seleccionado = self.tanda.currentData()
        
        self.tanda.clear()
        if not self.fecha_actual:
            return

        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.id, r.nombre || ' - T' || t.numero_tanda
            FROM tandas t
            JOIN referencias_chorizo r ON r.id = t.referencia_id
            WHERE t.fecha = ?
            ORDER BY t.numero_tanda
        """, (self.fecha_actual,))

        for id_, texto in cursor.fetchall():
            self.tanda.addItem(texto, id_)
            # Si el ID coincide con el que estaba antes, lo volvemos a seleccionar
            if id_ == id_seleccionado:
                index = self.tanda.count() - 1
                self.tanda.setCurrentIndex(index)

        conn.close()

    # ---------------------------------
    def cargar_materias(self):
        """Carga las materias primas con su stock actualizado"""
        # Guardar la selección actual
        seleccion_actual = self.materia.currentData()
        
        self.materia.clear()
        
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT id, nombre, costo_unitario, stock_actual
        FROM inventario_materia_prima
        ORDER BY nombre
        """)
        
        index_a_seleccionar = -1
        for idx, (id_, nombre, costo, stock) in enumerate(cursor.fetchall()):
            self.materia.addItem(
                f"{nombre} (${costo:.2f})", 
                (id_, costo, stock)
            )
            # Restaurar la selección si coincide
            if seleccion_actual and seleccion_actual[0] == id_:
                index_a_seleccionar = idx
        
        conn.close()
        
        # Restaurar la selección
        if index_a_seleccionar >= 0:
            self.materia.setCurrentIndex(index_a_seleccionar)

    # ---------------------------------
    def refrescar_stock(self):
        """Refresca manualmente el stock"""
        self.cargar_materias()
        self.actualizar_stock_disponible()
        QMessageBox.information(self, "Actualizado", "Stock actualizado correctamente")

    # ---------------------------------
    def actualizar_stock_disponible(self):
        """Muestra el stock disponible de la materia prima seleccionada"""
        data = self.materia.currentData()
        if data:
            _, _, stock = data
            self.stock_label.setText(f"Stock disponible: {stock:.3f} kg")
            
            # Cambiar color según el stock
            if stock <= 0:
                self.stock_label.setStyleSheet("color: red; font-weight: bold;")
            elif stock < 10:
                self.stock_label.setStyleSheet("color: orange; font-weight: bold;")
            else:
                self.stock_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.stock_label.setText("Stock disponible: --")

    # ---------------------------------
    def validar_cantidad(self):
        """Valida que la cantidad no exceda el stock disponible"""
        data = self.materia.currentData()
        if not data:
            return
        
        _, _, stock = data
        cantidad = self.cantidad.value()
        
        # Cambiar color del spinbox según la validez
        if cantidad > stock:
            self.cantidad.setStyleSheet("background-color: #ffcccc;")
        else:
            self.cantidad.setStyleSheet("")

    # ---------------------------------
    def cargar_detalle(self):
        self.tabla.setRowCount(0)
        total = 0

        tanda_id = self.tanda.currentData()
        if not tanda_id:
            self.total_label.setText("Total Tanda: 0.00")
            return

        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT i.nombre, tm.cantidad_usada, tm.costo_unitario, tm.total
        FROM tanda_materia_prima tm
        JOIN inventario_materia_prima i ON i.id = tm.materia_prima_id
        WHERE tm.tanda_id = ?
        """, (tanda_id,))

        for fila, datos in enumerate(cursor.fetchall()):
            self.tabla.insertRow(fila)
            for col, valor in enumerate(datos):
                self.tabla.setItem(fila, col, QTableWidgetItem(str(valor)))
            total += datos[3]

        conn.close()
        self.total_label.setText(f"Total Tanda: {total:.2f}")

    # ---------------------------------
    def agregar(self):
        tanda_id = self.tanda.currentData()
        if not tanda_id:
            QMessageBox.warning(self, "Error", "Seleccione una tanda")
            return

        data = self.materia.currentData()
        if not data:
            QMessageBox.warning(self, "Error", "Seleccione una materia prima")
            return

        materia_id, costo, stock_disponible = data
        cantidad = self.cantidad.value()

        # VALIDACIÓN: Verificar que hay suficiente stock
        if cantidad <= 0:
            QMessageBox.warning(self, "Error", "La cantidad debe ser mayor a 0")
            return

        if cantidad > stock_disponible:
            respuesta = QMessageBox.critical(
                self,
                "Stock Insuficiente",
                f"No hay suficiente stock disponible.\n\n"
                f"Cantidad solicitada: {cantidad:.3f} kg\n"
                f"Stock disponible: {stock_disponible:.3f} kg\n"
                f"Faltante: {cantidad - stock_disponible:.3f} kg\n\n"
                f"¿Desea agregar stock de esta materia prima?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if respuesta == QMessageBox.Yes:
                QMessageBox.information(
                    self,
                    "Información",
                    "Vaya a la pestaña 'Stock de Materia Prima' para agregar más inventario."
                )
            return

        # Verificar stock actual en la BD
        conn = self.conectar()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT stock_actual, nombre 
        FROM inventario_materia_prima 
        WHERE id = ?
        """, (materia_id,))
        
        resultado = cursor.fetchone()
        if not resultado:
            conn.close()
            QMessageBox.critical(self, "Error", "Materia prima no encontrada")
            return
        
        stock_actual, nombre_materia = resultado
        
        if cantidad > stock_actual:
            conn.close()
            QMessageBox.critical(
                self,
                "Stock Insuficiente",
                f"El stock de '{nombre_materia}' ha cambiado.\n\n"
                f"Stock actual: {stock_actual:.3f} kg\n"
                f"Cantidad solicitada: {cantidad:.3f} kg"
            )
            self.cargar_materias()
            return

        total = cantidad * costo

        # Registrar uso en la tanda
        cursor.execute("""
        INSERT INTO tanda_materia_prima
        (tanda_id, materia_prima_id, cantidad_usada, costo_unitario, total)
        VALUES (?, ?, ?, ?, ?)
        """, (tanda_id, materia_id, cantidad, costo, total))

        # Descontar del inventario
        cursor.execute("""
        UPDATE inventario_materia_prima
        SET stock_actual = stock_actual - ?
        WHERE id = ?
        """, (cantidad, materia_id))
        
        # Obtener stock resultante
        cursor.execute("""
        SELECT stock_actual FROM inventario_materia_prima WHERE id = ?
        """, (materia_id,))
        stock_resultante = cursor.fetchone()[0]
        
        # Registrar en el historial
        from datetime import datetime
        fecha_actual = datetime.now().strftime("%Y-%m-%d")
        hora_actual = datetime.now().strftime("%H:%M:%S")
        
        # Obtener nombre de la tanda para referencia
        cursor.execute("""
        SELECT r.nombre || ' - T' || t.numero_tanda
        FROM tandas t
        JOIN referencias_chorizo r ON r.id = t.referencia_id
        WHERE t.id = ?
        """, (tanda_id,))
        nombre_tanda = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT INTO historial_inventario_materia_prima
            (fecha, hora, materia_prima_id, tipo_movimiento, cantidad, 
             costo_unitario, total, stock_anterior, stock_resultante, 
             referencia, tanda_id)
            VALUES (?, ?, ?, 'SALIDA', ?, ?, ?, ?, ?, ?, ?)
        """, (fecha_actual, hora_actual, materia_id, cantidad, 
              costo, total, stock_actual, stock_resultante, 
              f"Usado en {nombre_tanda}", tanda_id))

        conn.commit()
        conn.close()

        # Emitir señal de que el stock cambió
        self.stock_actualizado.emit()

        # Mensaje de éxito
        QMessageBox.information(
            self,
            "Éxito",
            f"Se agregaron {cantidad:.3f} kg de '{nombre_materia}' a la tanda.\n"
            f"Stock restante: {stock_actual - cantidad:.3f} kg"
        )

        self.cantidad.setValue(0)
        self.cargar_detalle()
        self.cargar_materias()
        self.actualizar_stock_disponible()