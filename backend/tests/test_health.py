from fastapi.testclient import TestClient

from app.main import app


def test_health_check_returns_unified_response() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.headers["x-request-id"]
    assert response.json() == {
        "code": 200,
        "message": "成功",
        "data": {"status": "ok"},
    }
