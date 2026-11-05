-- =====================================================================
--  Vuelo y Tradición · Esquema MySQL 8 / MariaDB 10.4+ (XAMPP compatible)
--  Uso:  mysql -u root -p < database/init.sql
--  Con Docker se ejecuta solo la primera vez que se crea el volumen.
-- =====================================================================
CREATE DATABASE IF NOT EXISTS vuelo_y_tradicion
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE vuelo_y_tradicion;

-- 1. Usuarios (cuentas de acceso). El administrador inicial NO se inserta aquí:
--    la API lo crea al arrancar con ADMIN_EMAIL / ADMIN_PASSWORD (hash bcrypt).
CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    email         VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          ENUM('admin', 'artesano') NOT NULL DEFAULT 'artesano',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. Artesanos (perfil público del taller). user_id es opcional: el administrador
--    puede registrar talleres que aún no tienen cuenta propia.
CREATE TABLE IF NOT EXISTS artisans (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    user_id           INT NULL UNIQUE,
    full_name         VARCHAR(150) NOT NULL,
    workshop_name     VARCHAR(150) NOT NULL,
    community         VARCHAR(100) NOT NULL,        -- Ej. Papantla, Coxquihui, Espinal
    bio               TEXT NULL,
    phone_whatsapp    VARCHAR(20)  NOT NULL,        -- Solo dígitos con lada: 5217841234567
    profile_image_url VARCHAR(255) NULL,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_artisan_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 3. Productos (galería / inventario)
CREATE TABLE IF NOT EXISTS products (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    artisan_id  INT NOT NULL,
    title       VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    category    VARCHAR(60)  NOT NULL,              -- Ej. Textiles, Vainilla, Madera, Alfarería
    price       DECIMAL(10, 2) NOT NULL,
    stock       INT NOT NULL DEFAULT 1,
    image_url   VARCHAR(255) NOT NULL,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_product_artisan FOREIGN KEY (artisan_id)
        REFERENCES artisans(id) ON DELETE CASCADE,
    INDEX idx_category (category),
    INDEX idx_artisan (artisan_id),
    FULLTEXT INDEX idx_search (title, description)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
--  Datos de ejemplo (números y fotos ficticios: reemplázalos desde el panel admin)
-- ---------------------------------------------------------------------
INSERT INTO artisans (id, full_name, workshop_name, community, bio, phone_whatsapp, profile_image_url) VALUES
(1, 'Herminia García', 'Taller Textil Xaxti', 'Papantla, Veracruz',
   'Maestra tejedora en telar de cintura con técnicas tradicionales totonacas.',
   '5217840001122', 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=400&q=80'),
(2, 'Rogelio Tejeda', 'Vainilla Kuxi', 'Papantla, Veracruz',
   'Productor de vainilla de tercera generación; cura y procesa cada vaina de forma artesanal.',
   '5217840003344', 'https://placehold.co/400x400?text=Vainilla+Kuxi'),
(3, 'Marcelina Olarte', 'Barro y Fuego', 'Coxquihui, Veracruz',
   'Alfarera que moldea y quema sus piezas en horno de leña con diseños de la región.',
   '5217840005566', 'https://placehold.co/400x400?text=Barro+y+Fuego');

INSERT INTO products (artisan_id, title, description, category, price, stock, image_url) VALUES
(1, 'Blusa Bordada Cuello Cuadrado', 'Bordado fino tradicional en punto de cruz con motivos de la flora local.', 'Textiles', 850.00, 4,
   'https://images.unsplash.com/photo-1584917865442-de89df76afd3?auto=format&fit=crop&w=800&q=80'),
(1, 'Quechquémitl Tejido en Telar', 'Prenda ceremonial tejida a mano en telar de cintura con hilo de algodón.', 'Textiles', 1200.00, 2,
   'https://placehold.co/800x600?text=Quechqu%C3%A9mitl'),
(2, 'Extracto Artesanal de Vainilla de Papantla', 'Botella de 250 ml con denominación de origen curada artesanalmente.', 'Vainilla', 380.00, 15,
   'https://images.unsplash.com/photo-1598965675045-45c5e72c7d05?auto=format&fit=crop&w=800&q=80'),
(2, 'Vainas de Vainilla Beneficiada (10 pzas)', 'Vainas largas y aromáticas, curadas durante meses al sol y a la sombra.', 'Vainilla', 290.00, 20,
   'https://placehold.co/800x600?text=Vainas+de+Vainilla'),
(3, 'Olla de Barro para Mole', 'Olla de barro cocido, apta para fuego directo. Capacidad aproximada de 3 litros.', 'Alfarería', 450.00, 6,
   'https://placehold.co/800x600?text=Olla+de+Barro');
