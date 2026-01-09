# ui/gestion_inventario.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget


class GestionInventario(QWidget):
    """Widget principal que integra todos los módulos de inventario"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Inventario - Materia Prima")
        self.resize(1000, 650)
        
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        
        # Importaciones locales DENTRO del __init__
        from .inventario_mp import InventarioMateriaPrima
        from .materia_prima_tanda import MateriaPrimaTanda
        from .inventario_diario import InventarioDiario
        from .historial_inventario_materia_prima import HistorialInventarioMateriaPrima
        
        # Pestaña 1
        self.inventario_stock = InventarioMateriaPrima()
        tabs.addTab(self.inventario_stock, "📦 Stock")
        
        # Pestaña 2
        self.materia_tanda = MateriaPrimaTanda()
        tabs.addTab(self.materia_tanda, "🏭 Asignar a Tandas")
        
        # Pestaña 3
        self.inventario_diario = InventarioDiario()
        tabs.addTab(self.inventario_diario, "📊 Consumo Diario")
        
        # Pestaña 4
        self.historial = HistorialInventarioMateriaPrima()
        tabs.addTab(self.historial, "📋 Historial")
        
        layout.addWidget(tabs)
        
        # Conectar señales
        tabs.currentChanged.connect(self.actualizar_pestaña)
        
        try:
            self.inventario_stock.stock_actualizado.connect(self.on_stock_actualizado)
            self.materia_tanda.stock_actualizado.connect(self.on_stock_actualizado)
        except AttributeError:
            pass  # Las señales aún no están implementadas
    
    def actualizar_pestaña(self, index):
        """Actualiza los datos cuando se cambia de pestaña"""
        try:
            if index == 0:
                self.inventario_stock.cargar_tabla()
            elif index == 1:
                self.materia_tanda.cargar_materias()
                self.materia_tanda.cargar_detalle()
            elif index == 2:
                self.inventario_diario.cargar()
            elif index == 3:
                self.historial.cargar_historial()
        except Exception as e:
            print(f"Error actualizando pestaña {index}: {e}")
    
    def on_stock_actualizado(self):
        """Se ejecuta cuando hay cambios en el stock"""
        try:
            self.inventario_stock.cargar_tabla()
            self.materia_tanda.cargar_materias()
            self.inventario_diario.cargar()
            self.historial.cargar_historial()
        except Exception as e:
            print(f"Error actualizando stock: {e}")
    
    def set_fecha(self, fecha):
        """Propaga la fecha a los widgets que la necesitan"""
        try:
            self.materia_tanda.set_fecha(fecha)
        except Exception as e:
            print(f"Error configurando fecha: {e}")