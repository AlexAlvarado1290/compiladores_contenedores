CREATE TABLE IF NOT EXISTS productos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    descripcion TEXT,
    categoria VARCHAR(60) NOT NULL,
    precio NUMERIC(10,2) NOT NULL CHECK (precio >= 0),
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    disponible BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos (categoria);

CREATE TABLE IF NOT EXISTS pedidos (
    id SERIAL PRIMARY KEY,
    cliente_nombre VARCHAR(120) NOT NULL,
    cliente_email  VARCHAR(120),
    total NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (total >= 0),
    estado VARCHAR(30) NOT NULL DEFAULT 'pendiente',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pedido_items (
    id SERIAL PRIMARY KEY,
    pedido_id   INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    producto_id INTEGER NOT NULL REFERENCES productos(id),
    cantidad    INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unit NUMERIC(10,2) NOT NULL CHECK (precio_unit >= 0)
);

CREATE INDEX IF NOT EXISTS idx_pedido_items_pedido ON pedido_items (pedido_id);

INSERT INTO productos (nombre, descripcion, categoria, precio, stock) VALUES
('Torta de Chocolate',        'Bizcocho húmedo de cacao con ganache',     'tortas',    45.00, 12),
('Cheesecake de Frutos Rojos','Base de galleta, queso crema y frutos',    'tortas',    52.00,  8),
('Tres Leches',               'Clásica esponja bañada en tres leches',    'tortas',    38.00, 10),
('Croissant de Mantequilla',  'Hojaldre francés recién horneado',         'panaderia',  6.50, 40),
('Pan de Yema',               'Pan dulce tradicional con yema y azúcar',  'panaderia',  3.00, 60),
('Macaron de Pistacho',       'Galleta de almendra rellena de ganache',   'galletas',   5.50, 30),
('Galleta de Avena y Pasas',  'Crujiente por fuera, suave por dentro',    'galletas',   4.00, 50),
('Brownie Nuez',              'Brownie denso con nueces tostadas',        'galletas',   7.50, 25),
('Café Americano',            'Café de especialidad 8oz',                 'bebidas',    8.00, 100),
('Chocolate Caliente',        'Cacao puro con leche de la casa',          'bebidas',   10.00, 80);
