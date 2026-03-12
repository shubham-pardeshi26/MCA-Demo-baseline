from dataclasses import dataclass, asdict
from typing import Optional
import json


@dataclass
class BusLocation:
    bus_id: str
    route_id: str
    latitude: float
    longitude: float
    speed_kmh: float
    heading_degrees: float
    passenger_count: int
    status: str
    timestamp: str

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> "BusLocation":
        return cls(
            bus_id=data["bus_id"],
            route_id=data["route_id"],
            latitude=data["latitude"],
            longitude=data["longitude"],
            speed_kmh=data["speed_kmh"],
            heading_degrees=data["heading_degrees"],
            passenger_count=data["passenger_count"],
            status=data["status"],
            timestamp=data["timestamp"],
        )

    @classmethod
    def from_json(cls, raw: str) -> "BusLocation":
        return cls.from_dict(json.loads(raw))
