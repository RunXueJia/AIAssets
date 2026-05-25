import asyncio
from datetime import date

from app.integrations.amap import MockAmapClient
from app.integrations.realtime import MockRealtimeClient
from app.integrations.weather import MockWeatherClient
from app.schemas.generation import GenerateStreamRequest
from app.services.ai_planning import AiPlanningService
from app.services.amap import AmapService
from app.services.realtime import RealtimeService
from app.services.weather import WeatherService


class WaypointAmapClient(MockAmapClient):
    def __init__(self) -> None:
        super().__init__()
        self.route_waypoints: list[str] = []
        self.link_waypoints: list = []
        self.link_waypoint_calls: list[list] = []
        self.export_waypoints: list[str] = []

    async def search_places(self, *, keyword: str, city: str | None = None):
        if keyword == "西湖景区":
            return {
                "items": [
                    {
                        "name": "断桥残雪",
                        "address": "杭州西湖",
                        "location": "120.149000,30.260000",
                        "type": "风景名胜",
                        "province_name": "浙江省",
                        "city_name": "杭州市",
                        "adname": "西湖区",
                    },
                    {
                        "name": "苏堤春晓",
                        "address": "杭州西湖",
                        "location": "120.145000,30.245000",
                        "type": "风景名胜",
                        "province_name": "浙江省",
                        "city_name": "杭州市",
                        "adname": "西湖区",
                    },
                ],
                "source_updated_at": "2026-05-22T10:00:00+08:00",
                "mock": True,
                "provider": self.provider,
            }
        if "杭州东站" in keyword and "西湖景区" in keyword:
            return {
                "items": [
                    {
                        "name": "断桥残雪",
                        "address": "杭州西湖",
                        "location": "120.149000,30.260000",
                        "type": "风景名胜",
                        "province_name": "浙江省",
                        "city_name": "杭州市",
                        "adname": "西湖区",
                    },
                    {
                        "name": "苏堤春晓",
                        "address": "杭州西湖",
                        "location": "120.145000,30.245000",
                        "type": "风景名胜",
                        "province_name": "浙江省",
                        "city_name": "杭州市",
                        "adname": "西湖区",
                    },
                ],
                "source_updated_at": "2026-05-22T10:00:00+08:00",
                "mock": True,
                "provider": self.provider,
            }
        return await super().search_places(keyword=keyword, city=city)

    async def export_route_map(self, *, waypoints: list[str] | None = None, **kwargs):
        self.export_waypoints = waypoints or []
        return await super().export_route_map(waypoints=waypoints, **kwargs)

    async def calculate_route(self, *, waypoints: list[str], **kwargs):
        self.route_waypoints = waypoints
        data = await super().calculate_route(waypoints=waypoints, **kwargs)
        data["origin_location"] = "120.21201,30.29191"
        data["destination_location"] = "120.143222,30.236064"
        data["waypoints"] = waypoints
        data["requested_waypoints"] = waypoints
        data["route_waypoints_source"] = "requested" if waypoints else "none"
        return data

    async def create_route_link(self, *, waypoints: list | None = None, **kwargs):
        self.link_waypoints = waypoints or []
        self.link_waypoint_calls.append(self.link_waypoints)
        return await super().create_route_link(waypoints=waypoints, **kwargs)


class DestinationNearbyAmapClient(WaypointAmapClient):
    async def search_places(self, *, keyword: str, city: str | None = None):
        if keyword == "合肥岸上草原":
            return {
                "items": [
                    {
                        "name": "合肥岸上草原",
                        "location": "117.304312,31.688760",
                        "type": "风景名胜",
                    },
                    {
                        "name": "合肥岸上草原停车场",
                        "location": "117.303108,31.690192",
                        "type": "停车场",
                    },
                    {
                        "name": "沿途休息点",
                        "location": "117.318000,31.701000",
                        "type": "推荐途经点",
                    },
                ],
                "source_updated_at": "2026-05-22T10:00:00+08:00",
                "mock": True,
                "provider": self.provider,
            }
        if "合肥市渡江战役纪念馆" in keyword and "合肥岸上草原" in keyword:
            return {
                "items": [
                    {
                        "name": "合肥岸上草原",
                        "location": "117.304312,31.688760",
                        "type": "风景名胜",
                    },
                    {
                        "name": "合肥岸上草原停车场",
                        "location": "117.303108,31.690192",
                        "type": "停车场",
                    },
                    {
                        "name": "沿途观景台",
                        "location": "117.318000,31.701000",
                        "type": "风景名胜;观景点",
                    },
                    {
                        "name": "沿途服务区",
                        "location": "117.316000,31.698000",
                        "type": "道路附属设施;服务区",
                    },
                ],
                "source_updated_at": "2026-05-22T10:00:00+08:00",
                "mock": True,
                "provider": self.provider,
            }
        return await super().search_places(keyword=keyword, city=city)

    async def calculate_route(self, *, waypoints: list[str], **kwargs):
        self.route_waypoints = waypoints
        data = await super().calculate_route(waypoints=waypoints, **kwargs)
        data["origin_location"] = "117.330016,31.709623"
        data["destination_location"] = "117.304312,31.688760"
        data["route_path_points"] = [
            "117.330016,31.709623",
            "117.322000,31.704000",
            "117.315000,31.696000",
            "117.304312,31.688760",
        ]
        data["waypoints"] = ["117.322000,31.704000", "117.315000,31.696000"]
        data["requested_waypoints"] = waypoints
        data["route_waypoints_source"] = "route_path"
        return data


class WebWaypointAmapClient(WaypointAmapClient):
    async def search_places(self, *, keyword: str, city: str | None = None):
        if "南京南站" in keyword and "玄武湖景区" in keyword:
            return {
                "items": [],
                "source_updated_at": "2026-05-22T10:00:00+08:00",
                "mock": True,
                "provider": self.provider,
            }
        if keyword == "明城墙台城景区":
            return {
                "items": [
                    {
                        "name": "明城墙台城景区",
                        "address": "南京市玄武区",
                        "location": "118.796500,32.061900",
                        "type": "风景名胜;景点",
                        "province_name": "江苏省",
                        "city_name": "南京市",
                        "adname": "玄武区",
                    }
                ],
                "source_updated_at": "2026-05-22T10:05:00+08:00",
                "mock": True,
                "provider": self.provider,
            }
        return await super().search_places(keyword=keyword, city=city)


class WebWaypointRealtimeClient(MockRealtimeClient):
    async def search(self, *, keyword: str, category: str, limit: int):
        if category == "guide" and "南京南站" in keyword and "玄武湖景区" in keyword:
            return [
                {
                    "title": "南京南站到玄武湖顺路点",
                    "url": "https://example.com/nanjing-route",
                    "source": "example.com",
                    "published_at": "2026-05-22T09:00:00+08:00",
                    "summary": "建议途径明城墙台城景区再进入玄武湖景区。",
                    "raw": {"waypoint_candidates": ["明城墙台城景区"]},
                }
            ][:limit]
        return await super().search(keyword=keyword, category=category, limit=limit)


class IntercityAmapClient(WaypointAmapClient):
    async def search_places(self, *, keyword: str, city: str | None = None):
        if keyword == "合肥":
            return {
                "items": [
                    {
                        "name": "合肥市",
                        "location": "117.227239,31.820586",
                        "type": "地名地址信息",
                        "city_name": "合肥市",
                    }
                ],
                "source_updated_at": "2026-05-22T10:00:00+08:00",
                "mock": True,
                "provider": self.provider,
            }
        if keyword == "南京":
            return {
                "items": [
                    {
                        "name": "南京市",
                        "location": "118.796877,32.060255",
                        "type": "地名地址信息",
                        "city_name": "南京市",
                    }
                ],
                "source_updated_at": "2026-05-22T10:00:00+08:00",
                "mock": True,
                "provider": self.provider,
            }
        if keyword in {"巢湖", "和县", "来安"}:
            locations = {
                "巢湖": "117.880490,31.608733",
                "和县": "118.351405,31.741794",
                "来安": "118.435718,32.452199",
            }
            return {
                "items": [
                    {
                        "name": keyword,
                        "location": locations[keyword],
                        "type": "风景名胜;沿途途径点",
                        "address": f"{keyword}沿途停靠点",
                        "city_name": "",
                    }
                ],
                "source_updated_at": "2026-05-22T10:00:00+08:00",
                "mock": True,
                "provider": self.provider,
            }
        if "合肥" in keyword and "南京" in keyword:
            return {
                "items": [
                    {
                        "name": "玄武湖景区",
                        "location": "118.796500,32.071200",
                        "type": "风景名胜;景区",
                        "address": "南京市玄武区玄武巷",
                        "city_name": "南京市",
                        "adname": "玄武区",
                    },
                    {
                        "name": "总统府",
                        "location": "118.792400,32.043900",
                        "type": "风景名胜;纪念馆",
                        "address": "南京市玄武区长江路",
                        "city_name": "南京市",
                        "adname": "玄武区",
                    },
                    {
                        "name": "夫子庙秦淮风光带",
                        "location": "118.788500,32.020900",
                        "type": "风景名胜;景区",
                        "address": "南京市秦淮区",
                        "city_name": "南京市",
                        "adname": "秦淮区",
                    },
                ],
                "source_updated_at": "2026-05-22T10:00:00+08:00",
                "mock": True,
                "provider": self.provider,
            }
        return await super().search_places(keyword=keyword, city=city)

    async def calculate_route(self, *, waypoints: list[str], **kwargs):
        self.route_waypoints = waypoints
        data = await super().calculate_route(waypoints=waypoints, **kwargs)
        data["origin_location"] = "117.227239,31.820586"
        data["destination_location"] = "118.796877,32.060255"
        data["distance_m"] = 250000
        data["duration_s"] = 21600
        data["route_summary"] = "约250.0公里，预计360分钟"
        data["route_path_points"] = []
        data["route_waypoints_source"] = "route_path"
        data["requested_waypoints"] = waypoints
        return data


class IntercityRealtimeClient(MockRealtimeClient):
    async def search(self, *, keyword: str, category: str, limit: int):
        if category == "guide" and "合肥" in keyword and "南京" in keyword:
            return [
                {
                    "title": "合肥到南京摩托小众风光线",
                    "url": "https://example.com/hefei-nanjing",
                    "source": "example.com",
                    "published_at": "2026-05-22T09:00:00+08:00",
                    "summary": "推荐合肥经巢湖、和县、来安再进入南京，避开主城拥堵。",
                    "raw": {"waypoint_candidates": ["巢湖", "和县", "来安"]},
                }
            ][:limit]
        return await super().search(keyword=keyword, category=category, limit=limit)


class FailingAmapClient(MockAmapClient):
    async def calculate_route(self, **_kwargs):  # noqa: ANN003
        raise RuntimeError("RESULTS_ARE_EMPTY")

    async def create_route_link(self, **_kwargs):  # noqa: ANN003
        raise RuntimeError("RESULTS_ARE_EMPTY")


def _service() -> AiPlanningService:
    return AiPlanningService(
        weather_service=WeatherService(client=MockWeatherClient()),
        amap_service=AmapService(client=MockAmapClient()),
        realtime_service=RealtimeService(client=MockRealtimeClient()),
    )


def test_ai_planning_builds_prompt_context_and_result() -> None:
    service = _service()
    request = GenerateStreamRequest(
        origin="杭州东站",
        destination="西湖景区",
        range="一天，步行少一点",
        transport_mode="mixed",
        travel_date=date(2026, 6, 1),
        people_count=2,
        preferences=["自然风光", "低强度"],
        avoidances=["少换乘"],
    )

    result = asyncio.run(service.build_result(101, request))

    assert "杭州东站" in result.context.prompt
    assert result.context.weather["city_name"] == "示例省 西湖景区 示例区"
    assert result.context.route["route_summary"]
    assert result.context.transport["transport_summary"]
    assert result.context.attractions["items"]
    assert result.context.realtime["news_traffic"]
    assert result.context.realtime["realtime_info_summary"].startswith("1. ")
    assert "\n2. " in result.context.realtime["realtime_info_summary"]
    assert result.risk_summary
    assert result.final_markdown.startswith("## 杭州东站到西湖景区规划草案")
    assert result.result_json["record_id"] == 101
    assert result.snapshots["summary"]["final_markdown"] == result.final_markdown


def test_ai_planning_maps_stage_snapshots_and_output_payload() -> None:
    service = _service()
    request = GenerateStreamRequest(origin="A", destination="B", range="一天")
    result = asyncio.run(service.build_result(1, request))

    route_snapshot = service.snapshot_for_stage(result, "route")
    realtime_snapshot = service.snapshot_for_stage(result, "realtime")
    output = service.output_payload(result)

    assert route_snapshot is not None
    assert route_snapshot[0] == "route"
    assert route_snapshot[1]["route_summary"]
    assert realtime_snapshot is not None
    assert realtime_snapshot[1]["realtime_info_summary"]
    assert realtime_snapshot[1]["realtime_info_summary"].startswith("1. ")
    assert output["final_markdown"]
    assert output["result_json"]["summary_title"]


def test_ai_planning_accepts_motorcycle_transport_mode() -> None:
    service = _service()
    request = GenerateStreamRequest(
        origin="杭州东站",
        destination="西湖景区",
        range="半天",
        transport_mode="motorcycle",
    )

    result = asyncio.run(service.build_result(102, request))

    assert result.context.transport["transport_mode"] == "motorcycle"
    assert "摩托车" in result.context.transport["transport_summary"]
    assert result.context.map_export["amap_route_url"]


def test_ai_planning_passes_attraction_waypoints_to_route_link() -> None:
    amap_client = WaypointAmapClient()
    service = AiPlanningService(
        weather_service=WeatherService(client=MockWeatherClient()),
        amap_service=AmapService(client=amap_client),
        realtime_service=RealtimeService(client=MockRealtimeClient()),
    )
    request = GenerateStreamRequest(
        origin="杭州东站",
        destination="西湖景区",
        range="一天",
        transport_mode="driving",
    )

    result = asyncio.run(service.build_result(104, request))

    expected_locations = ["120.149000,30.260000", "120.145000,30.245000"]
    assert amap_client.route_waypoints == expected_locations
    navigation_link_waypoints = amap_client.link_waypoint_calls[0]
    assert [item["location"] for item in navigation_link_waypoints] == expected_locations
    assert [item["name"] for item in navigation_link_waypoints] == ["断桥残雪", "苏堤春晓"]
    assert result.context.route["waypoints"] == amap_client.route_waypoints
    assert result.context.route["recommended_waypoint_source"] == "route_waypoint_search"
    assert result.context.map_export["navigation_waypoints"] == expected_locations
    assert amap_client.export_waypoints == expected_locations
    assert result.context.map_export["amap_route_url"]


def test_ai_planning_passes_motorcycle_attraction_waypoints_to_route_link() -> None:
    amap_client = WaypointAmapClient()
    service = AiPlanningService(
        weather_service=WeatherService(client=MockWeatherClient()),
        amap_service=AmapService(client=amap_client),
        realtime_service=RealtimeService(client=MockRealtimeClient()),
    )
    request = GenerateStreamRequest(
        origin="杭州东站",
        destination="西湖景区",
        range="半天",
        transport_mode="motorcycle",
    )

    result = asyncio.run(service.build_result(105, request))

    expected_locations = ["120.149000,30.260000", "120.145000,30.245000"]
    assert amap_client.route_waypoints == expected_locations
    navigation_link_waypoints = amap_client.link_waypoint_calls[0]
    assert [item["location"] for item in navigation_link_waypoints] == expected_locations
    assert [item["name"] for item in navigation_link_waypoints] == ["断桥残雪", "苏堤春晓"]
    assert result.context.route["transport_mode"] == "motorcycle"
    assert result.context.route["waypoints"] == amap_client.route_waypoints
    assert result.context.map_export["navigation_waypoints"] == expected_locations
    assert amap_client.export_waypoints == expected_locations
    assert "multiViaPointPlan" in result.context.map_export["amap_route_url"]


def test_ai_planning_filters_destination_nearby_pois_from_navigation_waypoints() -> None:
    amap_client = DestinationNearbyAmapClient()
    service = AiPlanningService(
        weather_service=WeatherService(client=MockWeatherClient()),
        amap_service=AmapService(client=amap_client),
        realtime_service=RealtimeService(client=MockRealtimeClient()),
    )
    request = GenerateStreamRequest(
        origin="合肥市渡江战役纪念馆",
        destination="合肥岸上草原",
        range="半天",
        transport_mode="motorcycle",
    )

    result = asyncio.run(service.build_result(106, request))

    assert result.context.route["route_waypoints_source"] == "route_path"
    assert result.context.route["waypoints"] == [
        "117.322000,31.704000",
        "117.315000,31.696000",
    ]
    assert amap_client.route_waypoints == ["117.318000,31.701000"]
    assert amap_client.link_waypoint_calls[0] == [
        {"name": "沿途观景台", "location": "117.318000,31.701000"}
    ]
    assert result.context.map_export["navigation_waypoints"] == ["117.318000,31.701000"]
    assert result.context.map_export["navigation_waypoint_items"][0]["name"] == "沿途观景台"
    assert result.context.map_export["waypoint_search"]["source"] == "route_waypoint_search"
    assert result.context.map_export["route_waypoints"] == result.context.route["waypoints"]
    assert amap_client.export_waypoints == ["117.318000,31.701000"]


def test_ai_planning_merges_web_search_waypoints_into_navigation_export() -> None:
    amap_client = WebWaypointAmapClient()
    service = AiPlanningService(
        weather_service=WeatherService(client=MockWeatherClient()),
        amap_service=AmapService(client=amap_client),
        realtime_service=RealtimeService(client=WebWaypointRealtimeClient()),
    )
    request = GenerateStreamRequest(
        origin="南京南站",
        destination="玄武湖景区",
        range="一天",
        transport_mode="driving",
        preferences=["人文历史"],
    )

    result = asyncio.run(service.build_result(107, request))

    expected_location = "118.796500,32.061900"
    assert amap_client.route_waypoints == [expected_location]
    assert result.context.route["waypoint_search"]["source_types"] == [
        "amap_poi",
        "web_search",
    ]
    web_items = [
        item
        for item in result.context.route["waypoint_search"]["items"]
        if item.get("source") == "web_search"
    ]
    assert web_items[0]["name"] == "明城墙台城景区"
    assert result.result_json["route"]["waypoint_search"]["items"] == (
        result.context.route["waypoint_search"]["items"]
    )
    assert result.context.map_export["navigation_waypoints"] == [expected_location]
    assert result.context.map_export["navigation_waypoint_items"][0]["source"] == "web_search"
    assert result.context.map_export["navigation_waypoint_items"][0]["source_url"] == (
        "https://example.com/nanjing-route"
    )
    assert amap_client.link_waypoint_calls[0] == [
        {"name": "明城墙台城景区", "location": expected_location}
    ]
    assert amap_client.export_waypoints == [expected_location]
    assert "导航途径点：明城墙台城景区（全网）。" in result.final_markdown


def test_ai_planning_prefers_intercity_web_waypoints_over_destination_city_pois() -> None:
    amap_client = IntercityAmapClient()
    service = AiPlanningService(
        weather_service=WeatherService(client=MockWeatherClient()),
        amap_service=AmapService(client=amap_client),
        realtime_service=RealtimeService(client=IntercityRealtimeClient()),
    )
    request = GenerateStreamRequest(
        origin="合肥",
        destination="南京",
        range="一天",
        transport_mode="motorcycle",
        preferences=["自然风光", "小众路线"],
    )

    result = asyncio.run(service.build_result(108, request))

    expected_locations = [
        "117.880490,31.608733",
        "118.351405,31.741794",
        "118.435718,32.452199",
    ]
    assert amap_client.route_waypoints == expected_locations
    assert result.context.map_export["navigation_waypoints"] == expected_locations
    assert [item["name"] for item in result.context.map_export["navigation_waypoint_items"]] == [
        "巢湖",
        "和县",
        "来安",
    ]
    assert {item["source"] for item in result.context.map_export["navigation_waypoint_items"]} == {
        "web_search"
    }
    navigation_names = [item["name"] for item in amap_client.link_waypoint_calls[0]]
    assert navigation_names == ["巢湖", "和县", "来安"]
    assert "玄武湖景区" not in navigation_names
    assert "总统府" not in navigation_names
    assert "夫子庙秦淮风光带" not in navigation_names
    assert amap_client.export_waypoints == expected_locations
    assert "导航途径点：巢湖（全网）、和县（全网）、来安（全网）。" in result.final_markdown


def test_ai_planning_degrades_when_amap_route_is_empty() -> None:
    service = AiPlanningService(
        weather_service=WeatherService(client=MockWeatherClient()),
        amap_service=AmapService(client=FailingAmapClient()),
        realtime_service=RealtimeService(client=MockRealtimeClient()),
    )
    request = GenerateStreamRequest(
        origin="巢湖",
        destination="拉萨",
        range="30天",
        transport_mode="motorcycle",
    )

    result = asyncio.run(service.build_result(103, request))

    assert result.context.route["distance_m"] == 0
    assert result.context.route["fallback_reason"] == "RESULTS_ARE_EMPTY"
    assert result.context.map_export["fallback_reason"] == "RESULTS_ARE_EMPTY"
    assert "部分外部数据已降级" in result.risk_summary
    assert result.final_markdown.startswith("## 巢湖到拉萨规划草案")
