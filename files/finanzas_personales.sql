-- =============================================================
--  SCRIPT SQL - SISTEMA DE FINANZAS PERSONALES
--  Base de datos: SQLite (compatible con MySQL/PostgreSQL)
--  Autor: Proyecto universitario - Finanzas Personales
-- =============================================================

-- -------------------------------------------------------------
-- TABLA: usuarios
-- Almacena los datos de cada usuario registrado en el sistema
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre           VARCHAR(100)        NOT NULL,
    email            VARCHAR(150)        NOT NULL UNIQUE,
    password_hash    VARCHAR(255)        NOT NULL,
    fecha_registro   DATETIME            NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------------
-- TABLA: categorias
-- Categorias personalizadas por usuario para clasificar gastos
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categorias (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id           INTEGER         NOT NULL,
    nombre               VARCHAR(80)     NOT NULL,
    color                VARCHAR(7)      NOT NULL DEFAULT '#6C757D',
    icono                VARCHAR(50)     NOT NULL DEFAULT 'bi-tag',
    presupuesto_mensual  REAL            NOT NULL DEFAULT 0.0,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- -------------------------------------------------------------
-- TABLA: ingresos
-- Registra cada ingreso del usuario con su monto y fecha
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ingresos (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id   INTEGER         NOT NULL,
    monto        REAL            NOT NULL CHECK (monto > 0),
    descripcion  VARCHAR(200)    NOT NULL,
    fuente       VARCHAR(100)    NOT NULL DEFAULT 'General',
    fecha        DATE            NOT NULL DEFAULT CURRENT_DATE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- -------------------------------------------------------------
-- TABLA: gastos
-- Registra cada gasto del usuario asociado a una categoria
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gastos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id    INTEGER         NOT NULL,
    categoria_id  INTEGER         NOT NULL,
    monto         REAL            NOT NULL CHECK (monto > 0),
    descripcion   VARCHAR(200)    NOT NULL,
    fecha         DATE            NOT NULL DEFAULT CURRENT_DATE,
    FOREIGN KEY (usuario_id)   REFERENCES usuarios(id)   ON DELETE CASCADE,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE RESTRICT
);

-- -------------------------------------------------------------
-- TABLA: ahorros
-- Registra los montos ahorrados por el usuario con su objetivo
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ahorros (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id   INTEGER         NOT NULL,
    monto        REAL            NOT NULL CHECK (monto > 0),
    descripcion  VARCHAR(200)    NOT NULL,
    objetivo     VARCHAR(150)    NOT NULL DEFAULT 'Ahorro general',
    fecha        DATE            NOT NULL DEFAULT CURRENT_DATE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- =============================================================
--  INDICES - Mejoran la velocidad de consultas frecuentes
-- =============================================================
CREATE INDEX IF NOT EXISTS idx_ingresos_usuario ON ingresos(usuario_id);
CREATE INDEX IF NOT EXISTS idx_ingresos_fecha   ON ingresos(fecha);
CREATE INDEX IF NOT EXISTS idx_gastos_usuario   ON gastos(usuario_id);
CREATE INDEX IF NOT EXISTS idx_gastos_categoria ON gastos(categoria_id);
CREATE INDEX IF NOT EXISTS idx_gastos_fecha     ON gastos(fecha);
CREATE INDEX IF NOT EXISTS idx_ahorros_usuario  ON ahorros(usuario_id);
CREATE INDEX IF NOT EXISTS idx_categorias_usuario ON categorias(usuario_id);

-- =============================================================
--  DATOS DE PRUEBA (opcional, para desarrollo)
-- =============================================================

-- Usuario de prueba (password: admin123)
INSERT OR IGNORE INTO usuarios (id, nombre, email, password_hash) VALUES (
    1,
    'Usuario Demo',
    'demo@finanzas.com',
    'pbkdf2:sha256:260000$demo$hashdeprueba'
);

-- Categorias por defecto para el usuario demo
INSERT OR IGNORE INTO categorias (usuario_id, nombre, color, icono, presupuesto_mensual) VALUES
    (1, 'Alimentacion',  '#28A745', 'bi-cart',         500000.0),
    (1, 'Transporte',    '#007BFF', 'bi-bus-front',    200000.0),
    (1, 'Vivienda',      '#6F42C1', 'bi-house',        800000.0),
    (1, 'Salud',         '#DC3545', 'bi-heart-pulse',  150000.0),
    (1, 'Educacion',     '#FD7E14', 'bi-book',         300000.0),
    (1, 'Entretenimiento','#20C997','bi-controller',   100000.0),
    (1, 'Servicios',     '#6C757D', 'bi-lightning',    250000.0),
    (1, 'Otros',         '#ADB5BD', 'bi-three-dots',   100000.0);

-- =============================================================
--  VISTAS UTILES (consultas preconstruidas)
-- =============================================================

-- Vista: resumen mensual de gastos por categoria
CREATE VIEW IF NOT EXISTS v_gastos_por_categoria AS
SELECT
    g.usuario_id,
    c.nombre        AS categoria,
    c.color,
    c.presupuesto_mensual,
    strftime('%Y-%m', g.fecha) AS mes,
    SUM(g.monto)    AS total_gastado,
    COUNT(g.id)     AS num_transacciones
FROM gastos g
JOIN categorias c ON g.categoria_id = c.id
GROUP BY g.usuario_id, c.id, strftime('%Y-%m', g.fecha);

-- Vista: balance mensual (ingresos - gastos - ahorros)
CREATE VIEW IF NOT EXISTS v_balance_mensual AS
SELECT
    u.id            AS usuario_id,
    u.nombre        AS usuario,
    mes,
    COALESCE(total_ingresos, 0)  AS total_ingresos,
    COALESCE(total_gastos, 0)    AS total_gastos,
    COALESCE(total_ahorros, 0)   AS total_ahorros,
    COALESCE(total_ingresos, 0)
        - COALESCE(total_gastos, 0)
        - COALESCE(total_ahorros, 0) AS balance
FROM usuarios u
LEFT JOIN (
    SELECT usuario_id, strftime('%Y-%m', fecha) AS mes, SUM(monto) AS total_ingresos
    FROM ingresos GROUP BY usuario_id, mes
) i ON u.id = i.usuario_id
LEFT JOIN (
    SELECT usuario_id, strftime('%Y-%m', fecha) AS mes, SUM(monto) AS total_gastos
    FROM gastos GROUP BY usuario_id, mes
) g ON u.id = g.usuario_id AND i.mes = g.mes
LEFT JOIN (
    SELECT usuario_id, strftime('%Y-%m', fecha) AS mes, SUM(monto) AS total_ahorros
    FROM ahorros GROUP BY usuario_id, mes
) a ON u.id = a.usuario_id AND i.mes = a.mes;
