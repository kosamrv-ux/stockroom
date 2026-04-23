from fastapi import FastAPI

from . import __version__
from .routers import categories, products, stock

app = FastAPI(
    title="StockRoom API",
    version=__version__,
    description="Track products and stock movements, with on-hand quantities and low-stock alerts.",
)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


app.include_router(categories.router)
app.include_router(products.router)
app.include_router(stock.router)
