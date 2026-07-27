# StockRoom

A compact inventory-management API for small warehouses. Track products, group
them into categories, and record stock movements (receipts, shipments,
adjustments). On-hand quantities are derived from the movement ledger rather
than stored as a mutable counter, so the stock level is always auditable.

Built with **FastAPI**, **SQLAlchemy 2.0** (typed ORM), **Alembic** migrations
and **Pytest**.

## Why a movement ledger?

Instead of keeping a single `quantity` column that gets incremented and
decremented, every change is an immutable `StockMovement` row with a signed
delta. The current quantity is `SUM(quantity)` over a product's movements. This
means:

- You get a full history for free (who/what/when via `note` + `created_at`).
- There is a single source of truth — no drift between a counter and its log.
- Business rules (e.g. "never let stock go negative") are enforced in one place,
  [`app/services.py`](app/services.py).

## Diagnostic case study

The [negative-adjustment self-audit](docs/diagnostic-samples/negative-adjustments.md) shows a
reproducible API-contract defect, its root cause, impact, fix plan, and verification evidence. It is
a public technical-diagnosis sample, not a client-work claim.

## Project layout

```
app/
  main.py          # FastAPI app + router wiring
  config.py        # pydantic-settings configuration
  database.py      # engine, session, declarative Base
  models.py        # SQLAlchemy ORM models
  schemas.py       # Pydantic request/response models
  services.py      # stock business logic (on-hand, movements, low-stock)
  dependencies.py  # API-key guard for write endpoints
  routers/         # categories, products, stock
alembic/           # migration environment + versions
tests/             # pytest suite (in-memory SQLite)
```

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

cp .env.example .env
alembic upgrade head            # create tables (SQLite by default)
uvicorn app.main:app --reload   # http://127.0.0.1:8000
```

Interactive docs are served at **http://127.0.0.1:8000/docs**.

### With Docker (Postgres)

```bash
docker compose up --build       # API on :8000, Postgres on :5432
```

## Authentication

Write operations (`POST`/`PATCH`/`DELETE`) require an `X-API-Key` header that
matches the `API_KEY` setting. If `API_KEY` is empty the guard is disabled,
which keeps local development frictionless. Read endpoints are always open.

```bash
curl -X POST http://127.0.0.1:8000/products \
  -H "X-API-Key: local-dev-key" -H "Content-Type: application/json" \
  -d '{"sku":"BOLT-M6","name":"M6 bolt","unit_price":0.12,"reorder_level":200}'
```

## Endpoints

| Method   | Path                                | Notes                              |
| -------- | ----------------------------------- | ---------------------------------- |
| `GET`    | `/health`                           | Liveness + version                 |
| `GET`    | `/categories`                       | List categories                    |
| `POST`   | `/categories`                       | Create a category 🔒               |
| `GET`    | `/products`                         | List (filter: `category_id`, `search`) |
| `GET`    | `/products/low-stock`               | At/below reorder level             |
| `GET`    | `/products/{id}`                    | Product with `on_hand`             |
| `POST`   | `/products`                         | Create a product 🔒                |
| `PATCH`  | `/products/{id}`                    | Partial update 🔒                  |
| `DELETE` | `/products/{id}`                    | Delete 🔒                          |
| `GET`    | `/products/{id}/movements`          | Movement history                   |
| `POST`   | `/products/{id}/movements`          | Record a movement 🔒               |

🔒 = requires `X-API-Key`.

### Movement quantities

- `RECEIPT` and `SHIPMENT` use a positive magnitude. The service stores shipments as a negative
  ledger delta.
- `ADJUSTMENT` uses a signed, non-zero delta: positive for found stock and negative for breakage,
  shrinkage, or a downward cycle-count correction.
- No movement may reduce on-hand stock below zero.

## Development

```bash
ruff check .       # lint
pytest             # test suite
alembic check      # confirm models and migrations are in sync
```

CI runs lint, an `alembic check`, and the test suite on Python 3.11 and 3.12.

## License

MIT — see [LICENSE](LICENSE).
