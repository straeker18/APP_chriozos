# Copiar TODO este contenido en: ui/historial_inventario_materia_prima.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QDateEdit,
    QComboBox, QPushButton, QHeaderView
)
from PySide6.QtCore import QDate
from PySide6.QtGui import QColor
import sqlite3
from pathlib import Path

# Usar la misma ruta de DB que los demás archivos
DB_PATH = Path(__file__).resolve().parents[1] / "data.db"


def conectar():
    """Función de conexión local"""
    return sqlite3.connect(DB_PATH)


class HistorialInventarioMateriaPrima(QWidget):
    """Widget para mostrar el historial de movimientos de inventario"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Historial de Inventario - Materia Prima")
        self.resize(1000, 600)
        
        layout = QVBoxLayout(self)
        
        # -------- FILTROS --------
        filtros = QHBoxLayout()
        
        # Filtro por materia prima
        filtros.addWidget(QLabel("Materia Prima:"))
        self.combo_materia = QComboBox()
        self.combo_materia.addItem("Todas", None)
        self.cargar_materias_filtro()
        self.combo_materia.currentIndexChanged.connect(self.cargar_historial)
        filtros.addWidget(self.combo_materia)
        
        # Filtro por tipo de movimiento
        filtros.addWidget(QLabel("Tipo:"))
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItem("Todos", None)
        self.combo_tipo.addItem("Entradas", "ENTRADA")
        self.combo_tipo.addItem("Salidas", "SALIDA")
        self.combo_tipo.currentIndexChanged.connect(self.cargar_historial)
        filtros.addWidget(self.combo_tipo)
        
        # Filtro por fechas
        filtros.addWidget(QLabel("Desde:"))
        self.fecha_desde = QDateEdit()
        self.fecha_desde.setCalendarPopup(True)
        self.fecha_desde.setDate(QDate.currentDate().addMonths(-1))
        self.fecha_desde.dateChanged.connect(self.cargar_historial)
        filtros.addWidget(self.fecha_desde)
        
        filtros.addWidget(QLabel("Hasta:"))
        self.fecha_hasta = QDateEdit()
        self.fecha_hasta.setCalendarPopup(True)
        self.fecha_hasta.setDate(QDate.currentDate())
        self.fecha_hasta.dateChanged.connect(self.cargar_historial)
        filtros.addWidget(self.fecha_hasta)
        
        # Botón refrescar
        btn_refrescar = QPushButton("🔄 Actualizar")
        btn_refrescar.clicked.connect(self.cargar_historial)
        filtros.addWidget(btn_refrescar)
        
        filtros.addStretch()
        layout.addLayout(filtros)
        
        # -------- RESUMEN --------
        resumen = QHBoxLayout()
        self.lbl_total_entradas = QLabel("Total Entradas: $0.00")
        self.lbl_total_entradas.setStyleSheet("color: green; font-weight: bold;")
        self.lbl_total_salidas = QLabel("Total Salidas: $0.00")
        self.lbl_total_salidas.setStyleSheet("color: red; font-weight: bold;")
        self.lbl_saldo = QLabel("Saldo: $0.00")
        self.lbl_saldo.setStyleSheet("color: blue; font-weight: bold; font-size: 14px;")
        
        resumen.addWidget(self.lbl_total_entradas)
        resumen.addWidget(self.lbl_total_salidas)
        resumen.addWidget(self.lbl_saldo)
        resumen.addStretch()
        layout.addLayout(resumen)
        
        # -------- TABLA --------
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(9)
        self.tabla.setHorizontalHeaderLabels([
            "Fecha", "Hora", "Tipo", "Materia Prima", 
            "Cantidad", "Costo Unit.", "Total", 
            "Stock Resultante", "Referencia"
        ])
        
        # Ajustar columnas
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(8, QHeaderView.Stretch)
        
        layout.addWidget(self.tabla)
        
        # Cargar datos iniciales
        self.cargar_historial()
    
    def cargar_materias_filtro(self):
        """Carga las materias primas para el filtro"""
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre FROM inventario_materia_prima ORDER BY nombre")
            for id_, nombre in cursor.fetchall():
                self.combo_materia.addItem(nombre, id_)
            conn.close()
        except Exception as e:
            print(f"Error cargando materias: {e}")
    
    def cargar_historial(self):
        """Carga el historial de movimientos"""
        try:
            materia_id = self.combo_materia.currentData()
            tipo_mov = self.combo_tipo.currentData()
            fecha_desde = self.fecha_desde.date().toString("yyyy-MM-dd")
            fecha_hasta = self.fecha_hasta.date().toString("yyyy-MM-dd")
            
            conn = conectar()
            cursor = conn.cursor()
            
            # Verificar si la tabla existe
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='historial_inventario_materia_prima'
            """)
            
            if not cursor.fetchone():
                # La tabla no existe, mostrar mensaje
                self.tabla.setRowCount(0)
                self.lbl_total_entradas.setText("Total Entradas: $0.00")
                self.lbl_total_salidas.setText("Total Salidas: $0.00")
                self.lbl_saldo.setText("⚠️ Tabla de historial no existe")
                conn.close()
                return
            
            # Construir query dinámicamente según filtros
            query = """
            SELECT 
                h.fecha,
                h.hora,
                h.tipo_movimiento,
                i.nombre,
                h.cantidad,
                h.costo_unitario,
                h.total,
                h.stock_resultante,
                h.referencia
            FROM historial_inventario_materia_prima h
            JOIN inventario_materia_prima i ON i.id = h.materia_prima_id
            WHERE h.fecha BETWEEN ? AND ?
            """
            params = [fecha_desde, fecha_hasta]
            
            if materia_id is not None:
                query += " AND h.materia_prima_id = ?"
                params.append(materia_id)
            
            if tipo_mov is not None:
                query += " AND h.tipo_movimiento = ?"
                params.append(tipo_mov)
            
            query += " ORDER BY h.fecha DESC, h.hora DESC"
            
            cursor.execute(query, params)
            datos = cursor.fetchall()
            conn.close()
            
            # Llenar tabla
            self.tabla.setRowCount(len(datos))
            
            total_entradas = 0
            total_salidas = 0
            
            for fila, row in enumerate(datos):
                fecha, hora, tipo, nombre, cantidad, costo, total, stock_result, ref = row
                
                # Calcular totales
                if tipo == "ENTRADA":
                    total_entradas += total
                else:
                    total_salidas += total
                
                # Fecha
                self.tabla.setItem(fila, 0, QTableWidgetItem(fecha))
                
                # Hora
                self.tabla.setItem(fila, 1, QTableWidgetItem(hora))
                
                # Tipo con color
                item_tipo = QTableWidgetItem(tipo)
                if tipo == "ENTRADA":
                    item_tipo.setBackground(QColor(200, 255, 200))
                else:
                    item_tipo.setBackground(QColor(255, 200, 200))
                self.tabla.setItem(fila, 2, item_tipo)
                
                # Materia prima
                self.tabla.setItem(fila, 3, QTableWidgetItem(nombre))
                
                # Cantidad
                self.tabla.setItem(fila, 4, QTableWidgetItem(f"{cantidad:.3f} kg"))
                
                # Costo unitario
                self.tabla.setItem(fila, 5, QTableWidgetItem(f"${costo:.2f}"))
                
                # Total
                self.tabla.setItem(fila, 6, QTableWidgetItem(f"${total:.2f}"))
                
                # Stock resultante
                self.tabla.setItem(fila, 7, QTableWidgetItem(f"{stock_result:.3f} kg"))
                
                # Referencia
                self.tabla.setItem(fila, 8, QTableWidgetItem(ref or "--"))
            
            # Actualizar resumen
            saldo = total_entradas - total_salidas
            self.lbl_total_entradas.setText(f"Total Entradas: ${total_entradas:.2f}")
            self.lbl_total_salidas.setText(f"Total Salidas: ${total_salidas:.2f}")
            self.lbl_saldo.setText(f"Saldo: ${saldo:.2f}")
            
            if saldo > 0:
                self.lbl_saldo.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
            elif saldo < 0:
                self.lbl_saldo.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
            else:
                self.lbl_saldo.setStyleSheet("color: blue; font-weight: bold; font-size: 14px;")
                
        except Exception as e:
            print(f"Error cargando historial: {e}")
            self.tabla.setRowCount(0)