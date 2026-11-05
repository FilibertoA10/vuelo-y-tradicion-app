# 🪶 Vuelo y Tradición

Plataforma web de **comercio justo** que conecta a artesanos del Totonacapan con compradores, sin intermediarios bancarios. El comprador arma su canasta y el pedido se cierra **directamente por WhatsApp** con el taller de origen.

> MVP · Frontend HTML5 + CSS3 + JavaScript nativo · Backend Python (FastAPI) · Base de datos MySQL

## ✨ Funcionalidades

| Requisito del MVP | Dónde está |
|---|---|
| **Directorio visual** de talleres con perfil, comunidad, historia y contacto directo | Sección «Nuestros talleres» (`index.html`) · `GET /api/artisans` |
| **Galería dinámica** con CRUD para el administrador (fotos, descripción, precio, existencias, visibilidad) | `admin.html` · `POST/PUT/DELETE /api/products` |
| **Búsqueda y filtros** por texto, categoría y taller | Buscador y chips del catálogo · `GET /api/products` |
| **Motor de pedidos por WhatsApp**: carrito sin pasarela de pagos; genera un enlace `wa.me` por cada taller del carrito | Botón «Mi pedido» · `POST /api/checkout/whatsapp` |
| Botón flotante de **contacto** y de **pedido** | `index.html` |
| Login de administrador con JWT y contraseñas con bcrypt | `/api/auth/login` |

## 🗂️ Estructura

```
vuelo-y-tradicion/
├── docker-compose.yml        # MySQL + API + sitio estático
├── .env.example              # plantilla de variables (copiar a .env)
├── database/
│   └── init.sql              # tablas users, artisans, products + datos de ejemplo
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt      # dependencias de la API
│   ├── requirements-dev.txt  # pytest + httpx
│   ├── app/
│   │   ├── main.py           # app FastAPI, CORS, arranque, estáticos /uploads
│   │   ├── config.py         # variables de entorno
│   │   ├── database.py       # conexión SQLAlchemy a MySQL
│   │   ├── models.py         # User, Artisan, Product
│   │   ├── schemas.py        # validación Pydantic
│   │   ├── security.py       # bcrypt + JWT
│   │   ├── whatsapp.py       # armado del mensaje y enlace wa.me
│   │   └── routers/          # auth · artisans · products · checkout · uploads
│   ├── tests/                # pruebas automáticas
│   └── uploads/              # fotos subidas (no se versionan)
└── frontend/
    ├── index.html            # tienda pública
    ├── admin.html            # panel de administrador
    ├── styles.css
    └── js/ config.js · common.js · app.js · admin.js
```

## 🚀 Opción A · Docker (recomendada)

Requiere [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
cp .env.example .env        # en Windows: copy .env.example .env
# Edita .env: contraseñas de MySQL, SECRET_KEY, ADMIN_EMAIL y ADMIN_PASSWORD
docker compose up --build
```

| Servicio | URL |
|---|---|
| Tienda | http://localhost:3000 |
| Panel de administrador | http://localhost:3000/admin.html |
| API + documentación Swagger | http://localhost:8000/docs |

La base de datos se crea sola con `database/init.sql` la primera vez. Para reiniciarla desde cero: `docker compose down -v`.

## 🧰 Opción B · XAMPP (sin Docker)

1. **MySQL:** inicia MySQL desde XAMPP e importa `database/init.sql` (phpMyAdmin → *Importar*, o `mysql -u root -p < database/init.sql`).
2. **Backend** (Python 3.10 o superior):
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate            # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
   Define las variables y arranca la API:
   ```bash
   export DATABASE_URL="mysql+pymysql://root:@localhost:3306/vuelo_y_tradicion"
   export SECRET_KEY="una-clave-larga-y-aleatoria"
   export ADMIN_EMAIL="tu-correo@ejemplo.mx"
   export ADMIN_PASSWORD="una-contraseña-segura"   # mínimo 8 caracteres
   uvicorn app.main:app --reload --port 8000
   ```
   En Windows (PowerShell) usa `$env:SECRET_KEY="..."` en lugar de `export`.
3. **Frontend:** sirve la carpeta `frontend/` por HTTP (no abras el archivo con doble clic):
   ```bash
   cd frontend && python3 -m http.server 3000
   ```
   o usa *Live Server* de VS Code (puerto 5500). Abre http://localhost:3000.

Si publicas la API en otra dirección, cambia `API_ORIGIN` en `frontend/js/config.js` y agrega el dominio del frontend a `CORS_ORIGINS`.

## 🔐 Uso del panel de administrador

1. Entra a `/admin.html` con el correo y contraseña definidos en `ADMIN_EMAIL` / `ADMIN_PASSWORD`.
2. Pestaña **Talleres**: crea los perfiles (nombre, comunidad, historia, foto y WhatsApp con lada).
3. Pestaña **Inventario**: crea, edita, oculta o elimina piezas y sube sus fotografías (JPG, PNG o WEBP, máx. 5 MB).
4. Cambia el número del botón flotante de contacto en `frontend/js/config.js` (`CONTACT_WHATSAPP`).

> Los talleres, números y fotos incluidos en `init.sql` son **datos de ejemplo**: reemplázalos antes de publicar.

## 🔌 API principal

| Método | Ruta | Acceso | Descripción |
|---|---|---|---|
| GET | `/api/artisans` · `/api/artisans/{id}` | Público | Directorio y perfil con sus piezas |
| GET | `/api/products?search=&category=&artisan_id=` | Público | Catálogo con búsqueda y filtros |
| GET | `/api/categories` | Público | Categorías con piezas activas |
| POST | `/api/checkout/whatsapp` | Público | Valida existencias y devuelve un enlace de WhatsApp por taller |
| POST | `/api/auth/login` | Público | Devuelve un token JWT |
| POST · PUT · DELETE | `/api/products` · `/api/products/{id}` | Admin | CRUD de piezas |
| GET | `/api/admin/products` | Admin | Inventario completo, incluidas piezas ocultas |
| POST · PUT · DELETE | `/api/artisans` · `/api/artisans/{id}` | Admin | CRUD de talleres (borrar un taller borra sus piezas) |
| POST | `/api/admin/uploads` | Admin | Subida de fotografías |

Documentación interactiva completa en `/docs`.

## ✅ Pruebas

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
pytest
```
Las pruebas usan SQLite temporal, no necesitan MySQL.

## 🛡️ Seguridad incluida

- Contraseñas con **bcrypt** y sesiones con **JWT**; las rutas de escritura son solo para el administrador.
- Credenciales y claves **fuera del código** (`.env`, ignorado por Git).
- CORS limitado a los dominios del frontend.
- Texto de usuarios escapado en el frontend (protección contra XSS).
- Subidas validadas por la firma real del archivo y con límite de tamaño.
- El pedido valida existencias, piezas activas y agrupa por taller.

Antes de producción: usa HTTPS, una `SECRET_KEY` propia y contraseñas fuertes, y considera limitar los intentos de login (por ejemplo con un proxy inverso).

## 🌐 Subir el proyecto a GitHub

```bash
cd vuelo-y-tradicion
git init
git add .
git status                      # verifica que NO aparezca .env
git commit -m "MVP Vuelo y Tradición"
git branch -M main
```
Crea un repositorio vacío en https://github.com/new (sin README) y conéctalo:
```bash
git remote add origin https://github.com/TU_USUARIO/vuelo-y-tradicion.git
git push -u origin main
```
Para agregar compañeros: repositorio → **Settings → Collaborators → Add people**.

## 👥 Colaboradores

> Reemplaza los datos de ejemplo por los de tu equipo.

| Nombre | Rol | GitHub |
|---|---|---|
| Nombre Apellido | Desarrollo Full-Stack | [@usuario](https://github.com/usuario) |
| Nombre Apellido | Backend / Base de datos | [@usuario](https://github.com/usuario) |
| Nombre Apellido | Frontend / Diseño | [@usuario](https://github.com/usuario) |

## 📄 Licencia

Proyecto académico. Define la licencia que corresponda antes de publicarlo.
