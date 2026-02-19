from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.database import create_tables

app = FastAPI(title="Freight Invoice Agent", version="1.0.0")

# Static files and templates
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.on_event("startup")
def startup():
    create_tables()


# Import and register routers
from app.routers import pages, clients, shipments, invoices, payments, dashboard, agent  # noqa: E402

app.include_router(pages.router)
app.include_router(clients.router)
app.include_router(shipments.router)
app.include_router(invoices.router)
app.include_router(payments.router)
app.include_router(dashboard.router)
app.include_router(agent.router)
