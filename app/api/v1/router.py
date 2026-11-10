from fastapi import APIRouter

from app.api.v1.units import router as units_router

api_router = APIRouter()
api_router.include_router(units_router)

