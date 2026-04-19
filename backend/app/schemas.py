from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class ProductoBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    descripcion: str | None = None
    categoria: str = Field(min_length=1, max_length=60)
    precio: Decimal = Field(ge=0)
    stock: int = Field(ge=0, default=0)
    disponible: bool = True


class ProductoCreate(ProductoBase):
    pass


class ProductoOut(ProductoBase):
    id: int


class PedidoItemIn(BaseModel):
    producto_id: int
    cantidad: int = Field(gt=0)


class PedidoCreate(BaseModel):
    cliente_nombre: str = Field(min_length=1, max_length=120)
    cliente_email: EmailStr | None = None
    items: list[PedidoItemIn] = Field(min_length=1)


class PedidoItemOut(BaseModel):
    producto_id: int
    nombre: str
    cantidad: int
    precio_unit: Decimal
    subtotal: Decimal


class PedidoOut(BaseModel):
    id: int
    cliente_nombre: str
    cliente_email: str | None
    total: Decimal
    estado: str
    created_at: datetime
    items: list[PedidoItemOut] = []
