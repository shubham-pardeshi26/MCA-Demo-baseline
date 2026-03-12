"""
Producer: simulates 5 buses emitting GPS telemetry events to Kafka.

Each bus interpolates between GPS waypoints on its assigned route and
publishes one BusLocation message every EMIT_INTERVAL_S seconds.
Message key = bus_id → consistent partition assignment per bus.
"""

import time
import math
import random
from datetime import datetime, timezone

from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError

from config import KAFKA_BROKER, TOPIC_NAME, NUM_PARTITIONS, EMIT_INTERVAL_S
from models import BusLocation

# ---------------------------------------------------------------------------
# Route definitions  (lat/lon waypoints)
# ---------------------------------------------------------------------------
ROUTES = {
    "ROUTE_A": [
        (18.5204, 73.8567),
        (18.5220, 73.8600),
        (18.5250, 73.8650),
        (18.5280, 73.8700),
        (18.5310, 73.8750),
        (18.5340, 73.8800),
    ],
    "ROUTE_B": [
        (18.5100, 73.8400),
        (18.5130, 73.8450),
        (18.5160, 73.8500),
        (18.5190, 73.8530),
        (18.5210, 73.8560),
    ],
    "ROUTE_C": [
        (18.5300, 73.8300),
        (18.5270, 73.8350),
        (18.5240, 73.8400),
        (18.5210, 73.8450),
        (18.5180, 73.8480),
        (18.5150, 73.8520),
    ],
}

# Bus-to-route mapping
BUSES = [
    {"bus_id": "BUS_001", "route_id": "ROUTE_A"},
    {"bus_id": "BUS_002", "route_id": "ROUTE_A"},
    {"bus_id": "BUS_003", "route_id": "ROUTE_B"},
    {"bus_id": "BUS_004", "route_id": "ROUTE_B"},
    {"bus_id": "BUS_005", "route_id": "ROUTE_C"},
]


# ---------------------------------------------------------------------------
# State per bus: current waypoint index + fractional progress between points
# ---------------------------------------------------------------------------
class BusState:
    def __init__(self, bus_id: str, route_id: str):
        self.bus_id = bus_id
        self.route_id = route_id
        self.waypoints = ROUTES[route_id]
        self.segment_idx = 0      # index of the "from" waypoint
        self.progress = 0.0       # 0..1 within current segment
        self.step = 0.05          # fraction advanced each tick
        self.passenger_count = random.randint(5, 40)

    def next_position(self) -> tuple[float, float, float, float]:
        """Return (lat, lon, speed_kmh, heading_degrees)."""
        wp = self.waypoints
        i = self.segment_idx
        lat0, lon0 = wp[i]
        lat1, lon1 = wp[(i + 1) % len(wp)]

        lat = lat0 + (lat1 - lat0) * self.progress
        lon = lon0 + (lon1 - lon0) * self.progress

        # Heading from current segment
        dlat = lat1 - lat0
        dlon = lon1 - lon0
        heading = (math.degrees(math.atan2(dlon, dlat)) + 360) % 360

        # Vary speed slightly around 40 km/h; occasionally spike for alerts
        base_speed = 40.0 + random.uniform(-10, 25)
        speed = round(base_speed, 1)

        # Advance progress
        self.progress += self.step + random.uniform(-0.01, 0.01)
        if self.progress >= 1.0:
            self.progress = 0.0
            self.segment_idx = (self.segment_idx + 1) % (len(wp) - 1)

        # Vary passenger count slightly
        self.passenger_count = max(0, min(60, self.passenger_count + random.randint(-3, 3)))

        return round(lat, 6), round(lon, 6), speed, round(heading, 1)

    def get_status(self, speed: float) -> str:
        if speed == 0:
            return "STOPPED"
        if random.random() < 0.01:   # 1% chance of simulated breakdown
            return "BREAKDOWN"
        return "ON_ROUTE"


# ---------------------------------------------------------------------------
# Kafka setup helpers
# ---------------------------------------------------------------------------
def ensure_topic(broker: str, topic: str, partitions: int):
    admin = KafkaAdminClient(bootstrap_servers=broker)
    try:
        admin.create_topics([NewTopic(topic, num_partitions=partitions, replication_factor=1)])
        print(f"[admin] Created topic '{topic}' with {partitions} partitions.")
    except TopicAlreadyExistsError:
        print(f"[admin] Topic '{topic}' already exists.")
    finally:
        admin.close()


def build_producer(broker: str) -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=broker,
        key_serializer=lambda k: k.encode("utf-8"),
        value_serializer=lambda v: v.encode("utf-8"),
    )


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def main():
    print(f"Connecting to Kafka at {KAFKA_BROKER} …")
    ensure_topic(KAFKA_BROKER, TOPIC_NAME, NUM_PARTITIONS)

    producer = build_producer(KAFKA_BROKER)
    bus_states = [BusState(b["bus_id"], b["route_id"]) for b in BUSES]

    print(f"Emitting events every {EMIT_INTERVAL_S}s. Press Ctrl+C to stop.\n")

    try:
        while True:
            for state in bus_states:
                lat, lon, speed, heading = state.next_position()
                status = state.get_status(speed)

                event = BusLocation(
                    bus_id=state.bus_id,
                    route_id=state.route_id,
                    latitude=lat,
                    longitude=lon,
                    speed_kmh=speed,
                    heading_degrees=heading,
                    passenger_count=state.passenger_count,
                    status=status,
                    timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                )

                producer.send(
                    TOPIC_NAME,
                    key=state.bus_id,
                    value=event.to_json(),
                )
                print(f"[producer] {state.bus_id} | lat={lat} lon={lon} "
                      f"speed={speed} km/h | status={status}")

            producer.flush()
            time.sleep(EMIT_INTERVAL_S)

    except KeyboardInterrupt:
        print("\n[producer] Stopped.")
    finally:
        producer.close()


if __name__ == "__main__":
    main()
