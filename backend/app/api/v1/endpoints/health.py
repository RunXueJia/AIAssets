from fastapi import APIRouter

from app.core.responses import ApiResponse, success_response

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=ApiResponse)
async def health_check() -> ApiResponse:
    return success_response(data={"status": "ok"})
