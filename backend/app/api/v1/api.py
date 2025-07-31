"""API v1 router configuration."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    currencies,
    health,
    pensions,
    portfolios,
    settings,
    stocks,
    transactions,
)

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(currencies.router, tags=["currencies"])
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["portfolios"])
api_router.include_router(pensions.router, tags=["pensions"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
api_router.include_router(transactions.router, tags=["transactions"])
