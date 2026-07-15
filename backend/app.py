import json
import os
import time
import uuid
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Generator

import redis
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, Field
from sqlalchemy import Integer, Numeric, String, create_engine, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://cloudcart:cloudcart@localhost:5432/cloudcart",
)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

REQUESTS = Counter(
    "cloudcart_http_requests_total",
    "HTTP requests",
    ["method", "path", "status"],
)
LATENCY = Histogram(
    "cloudcart_http_request_duration_seconds",
    "HTTP request duration",
    ["method", "path"],
)
ORDERS = Counter("cloudcart_orders_created_total", "Orders created")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    stock: Mapped[int] = mapped_column(Integer, default=0)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    customer_name: Mapped[str] = mapped_column(String(120))
    product_id: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))


class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    price: Decimal = Field(gt=0)
    stock: int = Field(ge=0)


class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=120)
    product_id: int
    quantity: int = Field(gt=0, le=100)


def db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def seed(session: Session) -> None:
    if session.scalar(select(Product).limit(1)) is None:
        session.add_all(
            [
                Product(name="Mechanical Keyboard", price=Decimal("4999"), stock=25),
                Product(name="Wireless Mouse", price=Decimal("1999"), stock=40),
                Product(name="USB-C Dock", price=Decimal("7999"), stock=15),
            ]
        )
        session.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    for attempt in range(20):
        try:
            Base.metadata.create_all(engine)
            with SessionLocal() as session:
                seed(session)
            break
        except Exception:
            if attempt == 19:
                raise
            time.sleep(2)
    yield


app = FastAPI(title="CloudCart API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    path = request.url.path
    REQUESTS.labels(request.method, path, str(response.status_code)).inc()
    LATENCY.labels(request.method, path).observe(time.perf_counter() - start)
    response.headers["X-Correlation-ID"] = request.headers.get(
        "X-Correlation-ID", str(uuid.uuid4())
    )
    return response


@app.get("/health/live")
def live():
    return {"status": "alive"}


@app.get("/health/ready")
def ready(session: Session = Depends(db_session)):
    session.execute(text("SELECT 1"))
    redis_client.ping()
    return {"status": "ready"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/products")
def list_products(session: Session = Depends(db_session)):
    return [
        {"id": p.id, "name": p.name, "price": float(p.price), "stock": p.stock}
        for p in session.scalars(select(Product).order_by(Product.id)).all()
    ]


@app.post("/api/products", status_code=201)
def create_product(payload: ProductCreate, session: Session = Depends(db_session)):
    product = Product(**payload.model_dump())
    session.add(product)
    session.commit()
    session.refresh(product)
    return {"id": product.id, **payload.model_dump()}


@app.get("/api/orders")
def list_orders(session: Session = Depends(db_session)):
    return [
        {
            "id": o.id,
            "customer_name": o.customer_name,
            "product_id": o.product_id,
            "quantity": o.quantity,
            "status": o.status,
            "total_amount": float(o.total_amount),
        }
        for o in session.scalars(select(Order).order_by(Order.id.desc())).all()
    ]


@app.post("/api/orders", status_code=201)
def create_order(payload: OrderCreate, session: Session = Depends(db_session)):
    product = session.get(Product, payload.product_id)
    if product is None:
        raise HTTPException(404, "Product not found")
    if product.stock < payload.quantity:
        raise HTTPException(409, "Insufficient stock")

    order_id = f"ORD-{uuid.uuid4().hex[:10].upper()}"
    order = Order(
        id=order_id,
        customer_name=payload.customer_name,
        product_id=payload.product_id,
        quantity=payload.quantity,
        status="pending",
        total_amount=product.price * payload.quantity,
    )
    product.stock -= payload.quantity
    session.add(order)
    session.commit()

    redis_client.rpush("cloudcart:orders", json.dumps({"order_id": order_id}))
    ORDERS.inc()
    return {"id": order_id, "status": "pending"}


@app.get("/api/orders/{order_id}")
def get_order(order_id: str, session: Session = Depends(db_session)):
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(404, "Order not found")
    return {
        "id": order.id,
        "customer_name": order.customer_name,
        "product_id": order.product_id,
        "quantity": order.quantity,
        "status": order.status,
        "total_amount": float(order.total_amount),
    }
