from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints import amap, realtime, weather
from app.core.auth import require_admin_actor
from app.core.exceptions import register_exception_handlers
from app.schemas.records import RecordActor


def _client(*, authenticated: bool = True) -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(amap.router, prefix="/api/v1")
    app.include_router(weather.router, prefix="/api/v1")
    app.include_router(realtime.router, prefix="/api/v1")
    if authenticated:
        app.dependency_overrides[require_admin_actor] = lambda: RecordActor(
            user_id=1,
            role="admin",
        )
    return TestClient(app)


def test_external_helper_routes_require_admin_authentication() -> None:
    client = _client(authenticated=False)

    response = client.get("/api/v1/amap/search_places?keyword=西湖&city=杭州")

    assert response.status_code == 401


def test_amap_real_routes_match_documented_contract() -> None:
    client = _client()

    search_response = client.get("/api/v1/amap/search_places?keyword=西湖&city=杭州")
    route_response = client.post(
        "/api/v1/amap/calculate_route",
        json={
            "origin": "120.21201,30.29191",
            "destination": "120.143222,30.236064",
            "transport_mode": "driving",
            "waypoints": [],
        },
    )
    link_response = client.post(
        "/api/v1/amap/create_route_link",
        json={
            "origin_name": "杭州东站",
            "origin": "120.21201,30.29191",
            "destination_name": "西湖风景名胜区",
            "destination": "120.143222,30.236064",
            "transport_mode": "driving",
        },
    )
    export_response = client.post(
        "/api/v1/amap/export_route_map",
        json={"record_id": 101, "route_snapshot_id": 1, "export_type": "screenshot"},
    )

    assert search_response.status_code == 200
    assert search_response.json()["data"]["items"][0]["location"]
    assert search_response.json()["data"]["mock"] is False
    assert route_response.status_code == 200
    assert route_response.json()["data"]["distance_m"] > 0
    assert route_response.json()["data"]["mock"] is False
    assert link_response.status_code == 200
    assert link_response.json()["data"]["amap_route_url"].startswith(
        "https://uri.amap.com/navigation"
    )
    assert export_response.status_code == 200
    assert export_response.json()["data"]["status"] == "completed"
    assert "restapi.amap.com/v3/staticmap" in export_response.json()["data"]["image_url"]


def test_weather_and_realtime_real_routes_match_documented_contract() -> None:
    client = _client()

    weather_response = client.get("/api/v1/weather/query?city=四川 成都 成华区")
    weather_batch_response = client.post(
        "/api/v1/weather/batch_summary",
        json={
            "destination_city": "四川 成都 成华区",
            "route_cities": ["四川 成都 双流区"],
        },
    )
    realtime_response = client.get(
        "/api/v1/realtime/search?keyword=杭州%20西湖%20交通管制&category=traffic"
    )

    assert weather_response.status_code == 200
    assert weather_response.json()["data"]["weather_summary"]
    assert weather_response.json()["data"]["mock"] is False
    assert weather_batch_response.status_code == 200
    assert weather_batch_response.json()["data"]["destination_city"] == "四川 成都 成华区"
    assert weather_batch_response.json()["data"]["route_city_names"] == ["四川 成都 双流区"]
    assert realtime_response.status_code == 200
    assert realtime_response.json()["data"]["category"] == "traffic"
    assert realtime_response.json()["data"]["mock"] is False
    assert realtime_response.json()["data"]["provider"] == "tavily"
