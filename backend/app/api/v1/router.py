from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin_records,
    admin_users,
    amap,
    auth,
    generation,
    health,
    llm_configs,
    planning_records,
    realtime,
    weather,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(generation.router)
api_router.include_router(planning_records.router)
api_router.include_router(admin_records.router)
api_router.include_router(admin_users.router)
api_router.include_router(llm_configs.router)
api_router.include_router(amap.router)
api_router.include_router(weather.router)
api_router.include_router(realtime.router)
