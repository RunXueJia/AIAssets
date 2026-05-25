import asyncio
from urllib.parse import parse_qs, unquote, urlparse

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints import amap
from app.core.auth import get_current_actor, require_admin_actor
from app.core.exceptions import register_exception_handlers
from app.integrations.amap import (
    AmapWebServiceClient,
    MockAmapClient,
    create_amap_client,
)
from app.integrations.amap.client import AmapClientError
from app.schemas.amap import (
    AmapExportRouteMapRequest,
    AmapReverseGeocodeRequest,
    AmapRouteLinkRequest,
    AmapRouteRequest,
)
from app.schemas.records import RecordActor
from app.services.amap import AmapService


def _client(*, authenticated: bool = True) -> tuple[TestClient, object]:
    app = FastAPI()
    register_exception_handlers(app)
    original_service = amap.service
    amap.service = AmapService(client=MockAmapClient())
    app.include_router(amap.router, prefix="/api/v1")
    if authenticated:
        app.dependency_overrides[require_admin_actor] = lambda: RecordActor(
            user_id=1,
            role="admin",
        )
        app.dependency_overrides[get_current_actor] = lambda: RecordActor(
            user_id=1,
            role="admin",
        )
    client = TestClient(app)
    return client, original_service


def test_create_amap_client_requires_key_and_uses_real_client_with_key() -> None:
    try:
        create_amap_client(api_key=None)
    except AmapClientError as exc:
        assert "BACKEND_AMAP_API_KEY" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected AmapClientError")
    assert isinstance(create_amap_client(api_key="test-key"), AmapWebServiceClient)


def test_mock_amap_client_supports_search_route_link_and_export_contracts() -> None:
    client = MockAmapClient()

    async def collect() -> dict:
        search = await client.search_places(keyword="西湖", city="杭州")
        route = await client.calculate_route(
            origin="120.21201,30.29191",
            destination="120.143222,30.236064",
            transport_mode="driving",
            waypoints=[],
        )
        link = await client.create_route_link(
            origin_name="杭州东站",
            origin="120.21201,30.29191",
            destination_name="西湖风景名胜区",
            destination="120.143222,30.236064",
            transport_mode="driving",
        )
        export = await client.export_route_map(
            record_id=101,
            route_snapshot_id=1,
            export_type="screenshot",
            origin="120.21201,30.29191",
            destination="120.143222,30.236064",
            size="750*500",
        )
        return {
            "search": search,
            "route": route,
            "link": link,
            "export": export,
        }

    data = asyncio.run(collect())

    assert data["search"]["items"][0]["location"] == "120.143222,30.236064"
    assert data["search"]["mock"] is True
    assert data["route"]["distance_m"] == 12800
    assert data["route"]["raw"]["provider"] == "mock"
    assert data["route"]["provider"] == "mock"
    assert data["link"]["amap_route_url"].startswith("https://uri.amap.com/navigation")
    assert "%E6%9D%AD%E5%B7%9E%E4%B8%9C%E7%AB%99" in data["link"]["amap_route_url"]
    assert "mode=car" in data["link"]["amap_route_url"]
    assert data["export"]["status"] == "completed"
    assert data["export"]["export_id"] == 1
    assert data["export"]["amap_route_url"]
    assert data["export"]["width"] == 750
    assert data["export"]["height"] == 500


def test_mock_amap_client_supports_reverse_geocode_contract() -> None:
    client = MockAmapClient()

    data = asyncio.run(client.reverse_geocode(location="120.21201,30.29191"))

    assert data["province"]
    assert data["city"]
    assert data["district"]
    assert data["province_city_district"]
    assert data["mock"] is True


def test_amap_web_service_client_parses_poi_and_route_payloads() -> None:
    client = AmapWebServiceClient(api_key="test")
    poi_payload = {
        "status": "1",
        "pois": [
            {
                "name": "西湖风景名胜区",
                "address": "龙井路1号",
                "location": "120.143222,30.236064",
                "type": "风景名胜",
                "cityname": "杭州市",
            }
        ],
    }
    route_payload = {
        "status": "1",
        "route": {
            "paths": [
                {
                    "distance": "12800",
                    "duration": "2400",
                    "steps": [
                        {"polyline": "120.21201,30.29191;120.180000,30.270000"},
                        {"polyline": "120.180000,30.270000;120.143222,30.236064"},
                    ],
                }
            ]
        },
    }

    async def collect() -> dict:
        async def fake_request(scope, endpoint, params):  # noqa: ANN001
            return poi_payload if scope == "place" else route_payload

        client._cached_request = fake_request  # type: ignore[method-assign]
        return {
            "search": await client.search_places(keyword="西湖", city="杭州"),
            "route": await client.calculate_route(
                origin="120.21201,30.29191",
                destination="120.143222,30.236064",
                transport_mode="driving",
                waypoints=[],
            ),
        }

    data = asyncio.run(collect())

    assert data["search"]["items"][0]["name"] == "西湖风景名胜区"
    assert data["search"]["mock"] is False
    assert data["route"]["distance_m"] == 12800
    assert data["route"]["route_summary"] == "约12.8公里，预计40分钟"
    assert data["route"]["origin_location"] == "120.21201,30.29191"
    assert data["route"]["destination_location"] == "120.143222,30.236064"
    assert data["route"]["route_path_points"] == [
        "120.21201,30.29191",
        "120.180000,30.270000",
        "120.143222,30.236064",
    ]
    assert data["route"]["waypoints"] == ["120.180000,30.270000"]
    assert data["route"]["route_waypoints_source"] == "route_path"


def test_amap_web_service_client_parses_reverse_geocode_payload() -> None:
    client = AmapWebServiceClient(api_key="test")
    reverse_payload = {
        "status": "1",
        "regeocode": {
            "formatted_address": "浙江省杭州市西湖区",
            "addressComponent": {
                "province": "浙江省",
                "city": "杭州市",
                "district": "西湖区",
                "adcode": "330106",
                "citycode": "0571",
            },
        },
    }

    async def collect() -> dict:
        async def fake_request(scope, endpoint, params):  # noqa: ANN001
            return reverse_payload

        client._cached_request = fake_request  # type: ignore[method-assign]
        return await client.reverse_geocode(location="120.143222,30.236064")

    data = asyncio.run(collect())

    assert data["province"] == "浙江省"
    assert data["city"] == "杭州市"
    assert data["district"] == "西湖区"
    assert data["province_city_district"] == "浙江省 杭州市 西湖区"
    assert data["mock"] is False


def test_amap_web_service_client_resolves_place_names_before_route_request() -> None:
    client = AmapWebServiceClient(api_key="test")
    requested_params: list[dict] = []

    async def fake_request(scope, endpoint, params):  # noqa: ANN001
        requested_params.append(params)
        if scope == "place":
            keyword = params["keywords"]
            location = {
                "杭州东站": "120.21201,30.29191",
                "西湖景区": "120.143222,30.236064",
            }[keyword]
            return {
                "status": "1",
                "pois": [
                    {
                        "name": keyword,
                        "location": location,
                        "address": "",
                        "type": "",
                        "cityname": "杭州市",
                    }
                ],
            }
        return {"status": "1", "route": {"paths": [{"distance": "12800", "duration": "2400"}]}}

    async def collect() -> dict:
        client._cached_request = fake_request  # type: ignore[method-assign]
        return await client.calculate_route(
            origin="杭州东站",
            destination="西湖景区",
            transport_mode="driving",
            waypoints=[],
        )

    data = asyncio.run(collect())

    assert data["origin_location"] == "120.21201,30.29191"
    assert data["destination_location"] == "120.143222,30.236064"
    route_params = requested_params[-1]
    assert route_params["origin"] == "120.21201,30.29191"
    assert route_params["destination"] == "120.143222,30.236064"


def test_amap_web_service_client_uses_v5_route_endpoints_and_transport_modes() -> None:
    client = AmapWebServiceClient(api_key="test")
    requested: list[tuple[str, str, dict]] = []

    async def fake_request(scope, endpoint, params):  # noqa: ANN001
        requested.append((scope, endpoint, params))
        return {
            "status": "1",
            "route": {"paths": [{"distance": "6000", "cost": {"duration": "1200"}}]},
        }

    async def collect() -> None:
        client._cached_request = fake_request  # type: ignore[method-assign]
        for mode in ["driving", "walking", "cycling", "motorcycle"]:
            await client.calculate_route(
                origin="120.21201,30.29191",
                destination="120.143222,30.236064",
                transport_mode=mode,
                waypoints=["120.160000,30.250000"],
            )

    asyncio.run(collect())

    route_calls = requested
    assert route_calls[0][1].endswith("/v5/direction/driving")
    assert route_calls[0][2]["waypoints"] == "120.160000,30.250000"
    assert route_calls[1][1].endswith("/v5/direction/walking")
    assert "waypoints" not in route_calls[1][2]
    assert route_calls[2][1].endswith("/v5/direction/bicycling")
    assert route_calls[3][1].endswith("/v5/direction/electrobike")


def test_amap_web_service_client_builds_multi_via_route_link() -> None:
    client = AmapWebServiceClient(api_key="test")

    link = asyncio.run(
        client.create_route_link(
            origin_name="杭州东站",
            origin="120.21201,30.29191",
            destination_name="西湖风景名胜区",
            destination="120.143222,30.236064",
            transport_mode="driving",
            waypoints=["120.160000,30.250000", "120.170000,30.260000"],
        )
    )

    url = link["amap_route_url"]
    assert url.startswith("https://act.amap.com/activity/2020CommonLanding/index.html")
    query = parse_qs(urlparse(url).query)
    assert query["whiteList"] == ["amap.com"]
    schema = query["schema"][0]
    schema_query = parse_qs(urlparse(schema).query)
    assert schema.startswith("amapuri://drive/multiViaPointPlan")
    assert schema_query["slon"] == ["120.21201"]
    assert schema_query["slat"] == ["30.29191"]
    assert schema_query["dlon"] == ["120.143222"]
    assert schema_query["dlat"] == ["30.236064"]
    assert schema_query["vian"] == ["2"]
    assert schema_query["vialons"] == ["120.160000|120.170000"]
    assert schema_query["vialats"] == ["30.250000|30.260000"]
    assert schema_query["vianames"] == ["途径点1|途径点2"]


def test_amap_web_service_client_builds_multi_via_route_link_for_motorcycle() -> None:
    client = AmapWebServiceClient(api_key="test")

    link = asyncio.run(
        client.create_route_link(
            origin_name="杭州东站",
            origin="120.21201,30.29191",
            destination_name="西湖风景名胜区",
            destination="120.143222,30.236064",
            transport_mode="motorcycle",
            waypoints=["120.160000,30.250000"],
        )
    )

    query = parse_qs(urlparse(link["amap_route_url"]).query)
    schema = query["schema"][0]
    schema_query = parse_qs(urlparse(schema).query)
    assert schema.startswith("amapuri://drive/multiViaPointPlan")
    assert schema_query["vian"] == ["1"]
    assert schema_query["vialons"] == ["120.160000"]
    assert schema_query["vialats"] == ["30.250000"]


def test_amap_web_service_client_builds_multi_via_route_link_with_waypoint_names() -> None:
    client = AmapWebServiceClient(api_key="test")

    link = asyncio.run(
        client.create_route_link(
            origin_name="杭州东站",
            origin="120.21201,30.29191",
            destination_name="西湖风景名胜区",
            destination="120.143222,30.236064",
            transport_mode="driving",
            waypoints=[
                {"name": "断桥残雪", "location": "120.160000,30.250000"},
                {"name": "苏堤春晓", "location": "120.170000,30.260000"},
            ],
        )
    )

    query = parse_qs(urlparse(link["amap_route_url"]).query)
    schema_query = parse_qs(urlparse(query["schema"][0]).query)
    assert schema_query["vialons"] == ["120.160000|120.170000"]
    assert schema_query["vialats"] == ["30.250000|30.260000"]
    assert unquote(schema_query["vianames"][0]) == "断桥残雪|苏堤春晓"


def test_amap_web_service_client_builds_static_map_url_with_route_path() -> None:
    client = AmapWebServiceClient(api_key="test-key")

    export = asyncio.run(
        client.export_route_map(
            record_id=101,
            route_snapshot_id=1,
            export_type="static",
            origin="120.21201,30.29191",
            destination="120.143222,30.236064",
            waypoints=["120.160000,30.250000"],
            size="750*500",
            zoom=12,
        )
    )

    assert export["image_url"].startswith("https://restapi.amap.com/v3/staticmap?")
    assert "key=test-key" in export["image_url"]
    assert "location=120." in export["image_url"]
    assert "paths=" in export["image_url"]
    assert "markers=" in export["image_url"]
    assert "%3A120.21201%2C30.29191" in export["image_url"]
    assert "multiViaPointPlan" in export["amap_route_url"]
    assert export["width"] == 750
    assert export["height"] == 500


def test_amap_service_normalizes_mock_client_payloads() -> None:
    service = AmapService(client=MockAmapClient())

    async def collect() -> dict:
        return {
            "search": await service.search_places(keyword="西湖", city=" "),
            "route": await service.calculate_route(
                AmapRouteRequest(
                    origin="120.21201,30.29191",
                    destination="120.143222,30.236064",
                    transport_mode="driving",
                )
            ),
            "link": await service.create_route_link(
                AmapRouteLinkRequest(
                    origin_name="杭州东站",
                    origin="120.21201,30.29191",
                    destination_name="西湖风景名胜区",
                    destination="120.143222,30.236064",
                    transport_mode="driving",
                    waypoints=["120.160000,30.250000"],
                )
            ),
            "export": await service.export_route_map(
                AmapExportRouteMapRequest(
                    record_id=101,
                    export_type="screenshot",
                    origin="120.21201,30.29191",
                    destination="120.143222,30.236064",
                )
            ),
        }

    data = asyncio.run(collect())

    assert data["search"]["items"][0]["address"] == "示例城市示例地址"
    assert data["route"]["raw"]["waypoints"] == []
    assert data["route"]["waypoints"] == []
    assert data["route"]["route_path_points"] == []
    assert data["link"]["mock"] is True
    assert data["export"]["export_id"] == 101


def test_amap_api_contract_uses_service_layer() -> None:
    client, original_service = _client()
    try:
        search_response = client.get("/api/v1/amap/search_places?keyword=西湖&city=杭州")
        reverse_response = client.post(
            "/api/v1/amap/reverse_geocode",
            json={"location": "120.21201,30.29191"},
        )
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
        assert search_response.json()["data"]["provider"] == "mock"
        assert reverse_response.status_code == 200
        assert reverse_response.json()["data"]["province"] == "浙江省"
        assert reverse_response.json()["data"]["city"] == "杭州市"
        assert route_response.status_code == 200
        assert route_response.json()["data"]["distance_m"] == 12800
        assert link_response.status_code == 200
        assert link_response.json()["data"]["amap_route_url"].startswith(
            "https://uri.amap.com/navigation"
        )
        assert export_response.status_code == 200
        assert export_response.json()["data"]["status"] == "completed"
    finally:
        amap.service = original_service


def test_amap_api_requires_admin_authentication() -> None:
    client, original_service = _client(authenticated=False)
    try:
        response = client.get("/api/v1/amap/search_places?keyword=西湖&city=杭州")
        reverse_response = client.post(
            "/api/v1/amap/reverse_geocode",
            json={"location": "120.21201,30.29191"},
        )

        assert response.status_code == 401
        assert reverse_response.status_code == 401
    finally:
        amap.service = original_service
