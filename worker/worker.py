import json
import os
import time
from prometheus_client import Counter, Gauge, Histogram, start_http_server
import redis
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
client = redis.from_url(REDIS_URL, decode_responses=True)

PROCESSED = Counter("cloudcart_worker_orders_processed_total", "Orders processed")
FAILED = Counter("cloudcart_worker_orders_failed_total", "Orders failed")
DURATION = Histogram("cloudcart_worker_processing_duration_seconds", "Processing time")
QUEUE = Gauge("cloudcart_worker_queue_depth", "Current queue depth")


def process(order_id: str) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE orders SET status='processing' WHERE id=:id"),
            {"id": order_id},
        )
    time.sleep(3)
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE orders SET status='completed' WHERE id=:id"),
            {"id": order_id},
        )


def main() -> None:
    start_http_server(9101)
    while True:
        try:
            QUEUE.set(client.llen("cloudcart:orders"))
            item = client.blpop("cloudcart:orders", timeout=5)
            if not item:
                continue
            payload = json.loads(item[1])
            started = time.perf_counter()
            process(payload["order_id"])
            DURATION.observe(time.perf_counter() - started)
            PROCESSED.inc()
        except Exception as exc:
            FAILED.inc()
            print(f"worker_error={exc}", flush=True)
            time.sleep(2)


if __name__ == "__main__":
    main()
