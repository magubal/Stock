from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .config import settings
from .database import engine
from .models import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Stock Research ONE API starting up...")
    # Create database tables
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown
    print("Stock Research ONE API shutting down...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI 기반 주식 리서치 자동화 솔루션 API",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
from .api import news, reports, dashboard, context_analysis, liquidity_stress
app.include_router(news.router)
app.include_router(reports.router)
app.include_router(dashboard.router)
app.include_router(context_analysis.router)
app.include_router(liquidity_stress.router)
from .api import ideas, daily_work, insights, collab, cross_module, signals
app.include_router(ideas.router)
app.include_router(daily_work.router)
app.include_router(insights.router)
app.include_router(collab.router)
app.include_router(cross_module.router)
app.include_router(signals.router)
from .api import monitoring, moat_dashboard
app.include_router(monitoring.router)
app.include_router(moat_dashboard.router)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Stock Research ONE API",
        "version": settings.APP_VERSION,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
