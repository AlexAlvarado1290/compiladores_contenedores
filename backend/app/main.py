from contextlib import asynccontextmanager
from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import get_pool
from .schemas import (
    PedidoCreate, PedidoItemOut, PedidoOut,
    ProductoCreate, ProductoOut,
)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_pool()
    yield


app = FastAPI(title="Pastelería API", version="1.0.0", lifespan=lifespan)


@app.get("/api/health")
def health():
    with get_pool().connection() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok"}


# ---------- PRODUCTOS ----------

@app.get("/api/productos", response_model=list[ProductoOut])
def list_productos(
    categoria: str | None = Query(default=None),
    solo_disponibles: bool = Query(default=False),
):
    sql = ("SELECT id, nombre, descripcion, categoria, precio, stock, disponible "
           "FROM productos")
    params: list = []
    where: list[str] = []
    if categoria:
        where.append("categoria = %s"); params.append(categoria)
    if solo_disponibles:
        where.append("disponible = TRUE AND stock > 0")
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY categoria, nombre"

    with get_pool().connection() as conn:
        rows = conn.execute(sql, params).fetchall()

    return [
        ProductoOut(
            id=r[0], nombre=r[1], descripcion=r[2], categoria=r[3],
            precio=r[4], stock=r[5], disponible=r[6],
        ) for r in rows
    ]


@app.post("/api/productos", response_model=ProductoOut, status_code=201)
def create_producto(p: ProductoCreate):
    sql = ("INSERT INTO productos (nombre, descripcion, categoria, precio, stock, disponible) "
           "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id")
    with get_pool().connection() as conn:
        row = conn.execute(sql, [
            p.nombre, p.descripcion, p.categoria, p.precio, p.stock, p.disponible,
        ]).fetchone()
    return ProductoOut(id=row[0], **p.model_dump())


@app.get("/api/productos/{pid}", response_model=ProductoOut)
def get_producto(pid: int):
    sql = ("SELECT id, nombre, descripcion, categoria, precio, stock, disponible "
           "FROM productos WHERE id = %s")
    with get_pool().connection() as conn:
        r = conn.execute(sql, [pid]).fetchone()
    if r is None:
        raise HTTPException(404, "Producto no encontrado")
    return ProductoOut(
        id=r[0], nombre=r[1], descripcion=r[2], categoria=r[3],
        precio=r[4], stock=r[5], disponible=r[6],
    )


@app.delete("/api/productos/{pid}", status_code=204)
def delete_producto(pid: int):
    with get_pool().connection() as conn:
        cur = conn.execute("DELETE FROM productos WHERE id = %s", [pid])
        if cur.rowcount == 0:
            raise HTTPException(404, "Producto no encontrado")


# ---------- PEDIDOS ----------

@app.post("/api/pedidos", response_model=PedidoOut, status_code=201)
def create_pedido(pedido: PedidoCreate):
    with get_pool().connection() as conn:
        with conn.transaction():
            ids = [i.producto_id for i in pedido.items]
            rows = conn.execute(
                "SELECT id, nombre, precio, stock, disponible "
                "FROM productos WHERE id = ANY(%s) FOR UPDATE",
                [ids],
            ).fetchall()
            prods = {r[0]: r for r in rows}

            total = Decimal("0")
            items_out: list[PedidoItemOut] = []
            for it in pedido.items:
                p = prods.get(it.producto_id)
                if p is None:
                    raise HTTPException(400, f"Producto {it.producto_id} no existe")
                _, nombre, precio, stock, disponible = p
                if not disponible:
                    raise HTTPException(400, f"'{nombre}' no está disponible")
                if stock < it.cantidad:
                    raise HTTPException(400, f"Stock insuficiente para '{nombre}' (quedan {stock})")
                subtotal = precio * it.cantidad
                total += subtotal
                items_out.append(PedidoItemOut(
                    producto_id=it.producto_id, nombre=nombre,
                    cantidad=it.cantidad, precio_unit=precio, subtotal=subtotal,
                ))

            pid_row = conn.execute(
                "INSERT INTO pedidos (cliente_nombre, cliente_email, total, estado) "
                "VALUES (%s, %s, %s, 'pendiente') RETURNING id, created_at, estado",
                [pedido.cliente_nombre, pedido.cliente_email, total],
            ).fetchone()
            pedido_id, created_at, estado = pid_row

            for it, out in zip(pedido.items, items_out):
                conn.execute(
                    "INSERT INTO pedido_items (pedido_id, producto_id, cantidad, precio_unit) "
                    "VALUES (%s, %s, %s, %s)",
                    [pedido_id, it.producto_id, it.cantidad, out.precio_unit],
                )
                conn.execute(
                    "UPDATE productos SET stock = stock - %s WHERE id = %s",
                    [it.cantidad, it.producto_id],
                )

    return PedidoOut(
        id=pedido_id,
        cliente_nombre=pedido.cliente_nombre,
        cliente_email=pedido.cliente_email,
        total=total,
        estado=estado,
        created_at=created_at,
        items=items_out,
    )


@app.get("/api/pedidos", response_model=list[PedidoOut])
def list_pedidos():
    with get_pool().connection() as conn:
        pedidos = conn.execute(
            "SELECT id, cliente_nombre, cliente_email, total, estado, created_at "
            "FROM pedidos ORDER BY created_at DESC"
        ).fetchall()
        items = conn.execute(
            "SELECT pi.pedido_id, pi.producto_id, p.nombre, pi.cantidad, pi.precio_unit "
            "FROM pedido_items pi JOIN productos p ON p.id = pi.producto_id"
        ).fetchall()

    by_pedido: dict[int, list[PedidoItemOut]] = {}
    for pedido_id, prod_id, nombre, cant, precio in items:
        by_pedido.setdefault(pedido_id, []).append(PedidoItemOut(
            producto_id=prod_id, nombre=nombre, cantidad=cant,
            precio_unit=precio, subtotal=precio * cant,
        ))

    return [
        PedidoOut(
            id=p[0], cliente_nombre=p[1], cliente_email=p[2], total=p[3],
            estado=p[4], created_at=p[5], items=by_pedido.get(p[0], []),
        ) for p in pedidos
    ]


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")
