from fastapi import APIRouter

from app.api.v1.endpoints import auth, configuration, content, llm, operations

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(configuration.router)
api_router.include_router(llm.router)
api_router.include_router(content.router)
api_router.include_router(operations.router)
