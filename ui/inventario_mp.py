from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QDoubleSpinBox, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox
)
from ..db.conexion import conectar
from datetime import datetime

class InventarioMateriaPrima(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inventario de Materia Prima")
        self.resize(700, 400)
        layout = QVBoxLayout(self)
        
        # ---- FORM ----
        form = QHBoxLayout()
        
        self.insumo = QTableWidget(6, 1)
        self.insumo.setHorizontalHeaderLabels(["Insumo"])
        self.insumo.verticalHeader().setVisible(False)
        self.cargar_insumos()
        
        self.cantidad = QDoubleSpinBox()
        self.cantidad.setMaximum(100000)
        self.cantidad.setSuffix(" kg")
        
        self.costo = QDoubleSpinBox()
        self.costo.setMaximum(1000000)
        self.costo.setPrefix("$ ")
        
        btn = QPushButton("Agregar stock")
        btn.clicked.connect(self.agregar_stock)
        
        form.addWidget(self.insumo)
        form.addWidget(QLabel("Cantidad"))
        form.addWidget(self.cantidad)
        form.addWidget(QLabel("Costo Unit."))
        form.addWidget(self.costo)
        form.addWidget(btn)
        layout.addLayout(form)
        
        # ---- TABLA ----
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(
            ["Insumo", "Stock", "Costo Unit.", "Valor"]
        )
        layout.addWidget(self.tabla)
        
        self.cargar_tabla()
    
    # -----------------------------
    def cargar_insumos(self):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT nombre FROM inventario_materia_prima ORDER BY id")
        for fila, (nombre,) in enumerate(cursor.fetchall()):
            item = QTableWidgetItem(nombre)
            item.setFlags(item.flags() & ~item.flags().ItemIsEditable)
            self.insumo.setItem(fila, 0, item)
        conn.close()
    
    # -----------------------------
    def agregar_stock(self):
        """Lógica principal para actualizar stock y registrar historial"""
        fila = self.insumo.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Advertencia", "Seleccione un insumo de la lista izquierda")
            return
        
        nombre = self.insumo.item(fila, 0).text()
        cantidad_nueva = self.cantidad.value()
        costo_nuevo = self.costo.value()
        
        if cantidad_nueva <= 0 or costo_nuevo <= 0:
            QMessageBox.warning(self, "Advertencia", "La cantidad y el costo deben ser mayores a 0")
            return
        
        try:
            conn = conectar()
            cursor = conn.cursor()
            
            # 1. Obtener datos actuales del insumo
            cursor.execute("""
                SELECT id, stock_actual, costo_unitario
                FROM inventario_materia_prima
                WHERE nombre = ?
            """, (nombre,))
            
            resultado = cursor.fetchone()
            if not resultado:
                conn.close()
                return
            
            id_materia, stock_anterior, costo_actual = resultado
            
            # 2. Cálculos de Promedio Ponderado
            valor_anterior = stock_anterior * costo_actual
            valor_nuevo = cantidad_nueva * costo_nuevo
            stock_total = stock_anterior + cantidad_nueva
            
            # Evitar división por cero si el stock era negativo por algún error previo
            if stock_total > 0:
                costo_promedio = (valor_anterior + valor_nuevo) / stock_total
            else:
                costo_promedio = costo_nuevo
            
            # 3. Actualizar tabla principal (Inventario)
            cursor.execute("""
                UPDATE inventario_materia_prima
                SET stock_actual = ?,
                    costo_unitario = ?
                WHERE id = ?
            """, (stock_total, costo_promedio, id_materia))
            
            # 4. Registrar en el historial (Corrigiendo el error de stock_anterior)
            ahora = datetime.now()
            cursor.execute("""
                INSERT INTO historial_inventario_materia_prima (
                    materia_prima_id, fecha, hora, tipo_movimiento, 
                    cantidad, costo_unitario, total, 
                    stock_anterior, stock_resultante, referencia
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                id_materia, 
                ahora.strftime("%Y-%m-%d"), 
                ahora.strftime("%H:%M:%S"), 
                "ENTRADA", 
                cantidad_nueva, 
                costo_nuevo, 
                valor_nuevo,
                stock_anterior, 
                stock_total, 
                "Carga manual de stock"
            ))
            
            conn.commit()
            conn.close()
            
            # 5. Feedback al usuario
            QMessageBox.information(
                self, 
                "Operación Exitosa",
                f"Insumo: {nombre}\n"
                f"Nuevo Stock: {stock_total:.2f} kg\n"
                f"Nuevo Costo Promedio: ${costo_promedio:.2f}"
            )
            
            # Limpiar campos y refrescar vista
            self.cantidad.setValue(0)
            self.costo.setValue(0)
            self.cargar_tabla()
            
        except Exception as e:
            QMessageBox.critical(self, "Error de Base de Datos", f"No se pudo guardar: {str(e)}")
    
    # -----------------------------
    def cargar_tabla(self):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT nombre, stock_actual, costo_unitario,
                   stock_actual * costo_unitario
            FROM inventario_materia_prima
        """)
        datos = cursor.fetchall()
        conn.close()
        
        self.tabla.setRowCount(len(datos))
        for f, row in enumerate(datos):
            for c, val in enumerate(row):
                if isinstance(val, (int, float)):
                    texto = f"{val:.2f}"
                else:
                    texto = str(val)
                self.tabla.setItem(f, c, QTableWidgetItem(texto))