# 🧁 Dulce Aroma — Pastelería Dockerizada

Aplicación web para gestionar el catálogo y los pedidos de una pastelería
artesanal. Compuesta por tres contenedores independientes orquestados con
Docker Compose.

## Demostración en video

Grabación del levantamiento del sistema, carga inicial de datos, consulta
del catálogo, creación de pedidos, verificación de persistencia tras un
reinicio y detención limpia de los contenedores:

[Ver video en Google Drive](https://drive.google.com/file/d/1YVQ5YELhiDoxnnCVa9jvZTKDYdbDGs9E/view?usp=sharing)

| Servicio   | Tecnología               | Rol                                      |
| ---------- | ------------------------ | ---------------------------------------- |
| `db`       | PostgreSQL 16            | Persistencia de productos y pedidos      |
| `backend`  | Python + FastAPI         | API REST + frontend HTML                 |
| `proxy`    | Nginx                    | Proxy reverso, único punto de entrada    |

## Arquitectura

```
 Navegador ─▶ Nginx (:8080) ─▶ FastAPI (backend:8000) ─▶ PostgreSQL (db:5432)
                                                              │
                                                       volumen db_data
```

- Red interna definida por el usuario: `pasteleria_net` (driver bridge).
- Sólo el proxy expone puerto al host; `backend` y `db` quedan aislados.
- Volúmenes nombrados: `pasteleria_db_data` y `pasteleria_proxy_logs`.
- Seeding automático (`db/init.sql`) con 10 productos de ejemplo.

## Uso

```bash
cp .env.example .env           # ajustar credenciales si se desea
docker compose up --build -d
```

Abrir en el navegador: <http://localhost:8080>

Detener (conservando datos):

```bash
docker compose down
```

Detener y borrar datos:

```bash
docker compose down -v
```

## API REST

Base: `http://localhost:8080/api`

### Productos

| Método | Ruta               | Descripción                              |
| ------ | ------------------ | ---------------------------------------- |
| GET    | `/productos`       | Lista productos (filtros opcionales)     |
| GET    | `/productos/{id}`  | Obtiene un producto                      |
| POST   | `/productos`       | Crea un producto                         |
| DELETE | `/productos/{id}`  | Elimina un producto                      |

Filtros: `?categoria=tortas`, `?solo_disponibles=true`.

### Pedidos

| Método | Ruta               | Descripción                              |
| ------ | ------------------ | ---------------------------------------- |
| GET    | `/pedidos`         | Lista los pedidos con sus items          |
| POST   | `/pedidos`         | Crea un pedido (descuenta stock)         |

Ejemplo crear pedido:

```bash
curl -X POST http://localhost:8080/api/pedidos \
  -H 'Content-Type: application/json' \
  -d '{
    "cliente_nombre": "Ana",
    "cliente_email": "ana@test.com",
    "items": [{"producto_id":1,"cantidad":2},{"producto_id":4,"cantidad":3}]
  }'
```

Swagger UI: <http://localhost:8080/docs>

## Variables de entorno (`.env`)

| Variable            | Descripción                                  |
| ------------------- | -------------------------------------------- |
| `POSTGRES_USER`     | Usuario de la base de datos                  |
| `POSTGRES_PASSWORD` | Contraseña                                   |
| `POSTGRES_DB`       | Nombre de la base                            |
| `PROXY_PORT`        | Puerto publicado por Nginx (default 8080)    |

## Seguridad y buenas prácticas

- Secretos fuera del repo (`.env` en `.gitignore`; sólo `.env.example` versionado).
- Contenedor backend corre como usuario no-root (`app`).
- Ni `db` ni `backend` publican puertos al host — sólo el proxy.
- Validación con Pydantic (precios, cantidades, longitudes).
- Consultas parametrizadas (psycopg) — evita inyección SQL.
- Creación de pedido atómica: `BEGIN`/`COMMIT` con `SELECT ... FOR UPDATE`
  sobre los productos, de modo que el descuento de stock sea consistente
  bajo concurrencia.

## Estructura

```
pasteleria/
├── docker-compose.yml
├── .env.example
├── .env
├── README.md
├── db/init.sql
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   └── schemas.py
│   └── static/index.html
└── proxy/nginx.conf
```
