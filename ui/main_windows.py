from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QFileDialog,
    QMessageBox
)
from .inventario_pf import InventarioProductoFinal
from .acumulado import AcumuladoMensual
from ..export.export_excel import exportar_excel
from .produccion_diaria import ProduccionDiaria


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Producción de Chorizos")
        self.setMinimumSize(900, 600)
        
        layout = QVBoxLayout()
        
        # ========== INVENTARIOS ==========
        btn_inventario_mp = QPushButton("📦 Gestión de Inventario - Materia Prima")
        btn_inventario_mp.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        btn_inventario_mp.clicked.connect(self.abrir_gestion_inventario)
        layout.addWidget(btn_inventario_mp)
        
        btn_pf = QPushButton("📊 Inventario Producto Final")
        btn_pf.clicked.connect(self.abrir_pf)
        layout.addWidget(btn_pf)
        
        # ========== PRODUCCIÓN ==========
        btn_prod = QPushButton("🏭 Producción Diaria")
        btn_prod.clicked.connect(self.abrir_produccion)
        layout.addWidget(btn_prod)
        
        btn_acu = QPushButton("📈 Acumulado Mensual")
        btn_acu.clicked.connect(self.abrir_acumulado)
        layout.addWidget(btn_acu)
        
        # ========== EXPORTAR ==========
        btn_excel = QPushButton("📄 Exportar a Excel")
        btn_excel.clicked.connect(self.exportar_excel)
        layout.addWidget(btn_excel)
        
        # Aplicar estilos generales
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
    
    # ==========================================
    # VENTANAS
    # ==========================================
    
    def abrir_gestion_inventario(self):
        """
        Abre el módulo integrado de gestión de inventario
        que incluye:
        - Stock de Materia Prima
        - Asignar a Tandas
        - Consumo Diario
        - Historial de Movimientos
        """
        # Importación local para evitar problemas circulares
        from .gestion_inventario import GestionInventario
        
        self.ventana_inventario = GestionInventario()
        self.ventana_inventario.show()
    
    def abrir_pf(self):
        self.ventana_pf = InventarioProductoFinal()
        self.ventana_pf.show()
    
    def abrir_produccion(self):
        self.ventana_prod = ProduccionDiaria()
        self.ventana_prod.show()
    
    def abrir_acumulado(self):
        self.ventana_acu = AcumuladoMensual()
        self.ventana_acu.show()
    
    def exportar_excel(self):
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Excel",
            "",
            "Excel (*.xlsx)"
        )
        if not ruta:
            return
        
        # Forzar extensión .xlsx
        if not ruta.lower().endswith(".xlsx"):
            ruta += ".xlsx"
        
        try:
            exportar_excel(ruta)
            QMessageBox.information(
                self,
                "Exportación exitosa",
                "El archivo Excel fue generado correctamente"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error al exportar: {str(e)}"
            )