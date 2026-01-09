from .conexion import conectar


def crear_tablas():
    conn = conectar()
    cursor = conn.cursor()
    
    # Tabla de inventario de materia prima
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventario_materia_prima (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE,
            unidad TEXT DEFAULT 'kg',
            stock_actual REAL DEFAULT 0,
            costo_unitario REAL DEFAULT 0
        );
    """)
    
    # Tabla de inventario de producto final
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventario_producto_final (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto TEXT,
            cantidad REAL,
            costo_unitario REAL,
            total REAL
        )
    """)
    
    # Tabla de producción diaria
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produccion_diaria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            insumo TEXT,
            cantidad REAL,
            costo_unitario REAL,
            total REAL
        )
    """)
    
    # Tabla de acumulado mensual
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS acumulado_mensual (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concepto TEXT,
            cantidad REAL,
            total REAL
        )
    """)
    
    # Tabla de referencias de chorizo
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referencias_chorizo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            unidad TEXT NOT NULL
        )
    """)
    
    # Tabla de tandas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tandas ( 
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            numero_tanda INTEGER NOT NULL,
            referencia_id INTEGER NOT NULL,
            cantidad_producida REAL NOT NULL,
            unidades INTEGER DEFAULT 0, -- <--- NUEVA COLUMNA
            FOREIGN KEY (referencia_id) REFERENCES referencias_chorizo(id)
        )
    """)

    # NUEVO: Índice para evitar duplicados de tanda del mismo tipo en el mismo día
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_tanda_unica 
        ON tandas (fecha, numero_tanda, referencia_id);
    """)
    
    # Tabla de materia prima por tanda
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tanda_materia_prima (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanda_id INTEGER NOT NULL,
            materia_prima_id INTEGER NOT NULL,
            cantidad_usada REAL NOT NULL,
            costo_unitario REAL NOT NULL,
            total REAL NOT NULL,
            FOREIGN KEY (tanda_id) REFERENCES tandas(id),
            FOREIGN KEY (materia_prima_id) REFERENCES inventario_materia_prima(id)
        )
    """)
    
    # Tabla de precio de chorizo por día
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS precio_chorizo_dia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            referencia_id INTEGER NOT NULL,
            precio_venta REAL NOT NULL,
            FOREIGN KEY (referencia_id) REFERENCES referencias_chorizo(id)
        )
    """)
    
    # ========== NUEVA TABLA: HISTORIAL DE INVENTARIO ==========
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial_inventario_materia_prima (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            materia_prima_id INTEGER NOT NULL,
            tipo_movimiento TEXT NOT NULL CHECK(tipo_movimiento IN ('ENTRADA', 'SALIDA')),
            cantidad REAL NOT NULL,
            costo_unitario REAL NOT NULL,
            total REAL NOT NULL,
            stock_anterior REAL NOT NULL,
            stock_resultante REAL NOT NULL,
            referencia TEXT,
            tanda_id INTEGER,
            usuario TEXT,
            observaciones TEXT,
            FOREIGN KEY (materia_prima_id) REFERENCES inventario_materia_prima(id),
            FOREIGN KEY (tanda_id) REFERENCES tandas(id)
        )
    """)
    
    # Crear índices para mejorar el rendimiento de búsquedas
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_historial_fecha 
        ON historial_inventario_materia_prima(fecha)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_historial_materia 
        ON historial_inventario_materia_prima(materia_prima_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_historial_tipo 
        ON historial_inventario_materia_prima(tipo_movimiento)
    """)
    
    # ========== DATOS INICIALES ==========
    
    # Insertar materias primas iniciales
    cursor.execute("""
        INSERT OR IGNORE INTO inventario_materia_prima (nombre) VALUES
            ('T-grasa sin pelar'),
            ('Carne finca'),
            ('Pedacitos'),
            ('Manero'),
            ('Grasa pelada'),
            ('Barriguero')
    """)
    
    # Insertar referencias de chorizo
    cursor.execute("""
        INSERT OR IGNORE INTO referencias_chorizo (id, nombre, unidad) VALUES
            (1, 'Chorizo Económico', 'kg'),
            (2, 'Chorizo Mediano', 'kg'),
            (3, 'Chorizo Grande', 'kg'),
            (4, 'Chorizo de Cerdo', 'kg')
    """)
    
    conn.commit()
    conn.close()
    
    print("✅ Todas las tablas creadas correctamente")
    print("   - Incluyendo historial_inventario_materia_prima")