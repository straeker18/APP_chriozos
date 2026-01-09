from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTabWidget, QPushButton, QDateEdit
)
from PySide6.QtCore import QDate
from .tandas import Tandas
from .materia_prima_tanda import MateriaPrimaTanda
from .precio_diario import PrecioDiario


class ProduccionDiaria(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Producción Diaria")
        self.resize(900, 550)
        
        layout = QVBoxLayout(self)
        
        # ---------- FECHA ----------
        header = QHBoxLayout()
        self.fecha = QDateEdit()
        self.fecha.setCalendarPopup(True)
        self.fecha.setDate(QDate.currentDate())
        header.addWidget(QLabel("Fecha"))
        header.addWidget(self.fecha)
        header.addStretch()
        layout.addLayout(header)
        
        # ---------- TABS ----------
        self.tabs = QTabWidget()
        
        self.tab_tandas = Tandas()
        self.tab_mp = MateriaPrimaTanda()
        self.tab_precio = PrecioDiario()
        
        self.tabs.addTab(self.tab_tandas, "Tandas")
        self.tabs.addTab(self.tab_mp, "Materia Prima")
        self.tabs.addTab(self.tab_precio, "Precio Diario")
        
        layout.addWidget(self.tabs)
        
        # ---------- CONECTAR SEÑALES (TIEMPO REAL) ----------
        
        # 1. Cuando se crea una TANDA, actualizar el ComboBox de Materia Prima
        self.tab_tandas.tanda_creada.connect(self.tab_mp.cargar_tandas)
        
        # 2. Cuando se usa Materia Prima, avisar a otras pestañas (si es necesario)
        try:
            self.tab_mp.stock_actualizado.connect(self.actualizar_tabs)
        except AttributeError:
            pass
        
        # Conectar cambio de pestañas para actualizar datos al hacer clic
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # ---------- EVENTO FECHA ----------
        self.fecha.dateChanged.connect(self.cambiar_fecha)
        
        # Inicializar con la fecha actual
        self.cambiar_fecha(self.fecha.date())
    
    def cambiar_fecha(self, fecha):
        """Cambia la fecha en todas las pestañas"""
        fecha_str = fecha.toString("yyyy-MM-dd")
        
        # Actualizar fecha en cada pestaña de forma segura
        try:
            if hasattr(self.tab_tandas, 'set_fecha'):
                self.tab_tandas.set_fecha(fecha_str)
        except Exception as e:
            print(f"Error en tab_tandas.set_fecha: {e}")
        
        try:
            if hasattr(self.tab_mp, 'set_fecha'):
                self.tab_mp.set_fecha(fecha_str)
        except Exception as e:
            print(f"Error en tab_mp.set_fecha: {e}")
        
        try:
            if hasattr(self.tab_precio, 'set_fecha'):
                self.tab_precio.set_fecha(fecha_str)
        except Exception as e:
            print(f"Error en tab_precio.set_fecha: {e}")
    
    def on_tab_changed(self, index):
        """Se ejecuta cuando el usuario hace clic en una pestaña"""
        if index == 0:  # Tandas
            self.tab_tandas.cargar_tandas()
        elif index == 1:  # Materia Prima
            # Recargar todo para asegurar datos frescos
            try:
                self.tab_mp.cargar_tandas() # <--- Crucial para ver tandas nuevas
                self.tab_mp.cargar_materias()
                self.tab_mp.cargar_detalle()
                self.tab_mp.actualizar_stock_disponible()
            except Exception as e:
                print(f"Error recargando materia prima: {e}")
        elif index == 2:  # Precio Diario
            try:
                # Asegúrate de que PrecioDiario tenga cargar_precios o cargar
                if hasattr(self.tab_precio, 'cargar_precios'):
                    self.tab_precio.cargar_precios()
            except Exception as e:
                print(f"Error recargando precio: {e}")
    
    def actualizar_tabs(self):
        """Se ejecuta cuando se actualiza el stock de materia prima"""
        try:
            self.tab_mp.cargar_materias()
            self.tab_mp.actualizar_stock_disponible()
        except Exception as e:
            print(f"Error actualizando tabs: {e}")