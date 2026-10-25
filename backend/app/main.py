import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database.database import init_db
from app.services.vector_store import vector_store
from app.api.documents import router as documents_router
from app.api.query import router as query_router
from app.api.health import router as health_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("TripQueryAI")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing TripQuery AI backend...")
    init_db()
    vector_store.load()
    logger.info("TripQuery AI backend ready.")
    yield
    # Shutdown
    logger.info("Shutting down TripQuery AI backend...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Intelligent RAG Travel Document Assistant API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware setup
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    settings.FRONTEND_URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Hackathon-friendly: allows localhost:5173 and any port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(documents_router, prefix=settings.API_PREFIX)
app.include_router(query_router, prefix=settings.API_PREFIX)
app.include_router(health_router, prefix=settings.API_PREFIX)

@app.get("/")
def root():
    return {
        "message": "Welcome to TripQuery AI Backend API",
        "docs": "/docs",
        "health": f"{settings.API_PREFIX}/health"
    }
