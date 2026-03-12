"""
Dashboard consumer — group: dashboard-service

Maintains an in-memory dict of the latest position for every bus and
re-renders a live table in the terminal on every incoming message.
"""

import os
import sys

# Allow running from any working directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from kafka import KafkaConsumer
from config import KAFKA_BROKER, TOPIC_NAME
from models import BusLocation

GROUP_ID = "dashboard-service"

HEADER = (
    f"{'BUS':<10} {'ROUTE':<10} {'LAT':>10} {'LON':>10} "
    f"{'SPEED':>8} {'HDG':>6} {'PAX':>5} {'STATUS':<12} {'TIMESTAMP'}"
)
SEP = "-" * len(HEADER)


def render_table(bus_data: dict[str, BusLocation]):
    os.system("clear" if os.name == "posix" else "cls")
    print("=== LIVE BUS DASHBOARD ===")
    print(HEADER)
    print(SEP)
    for bus_id in sorted(bus_data):
        b = bus_data[bus_id]
        print(
            f"{b.bus_id:<10} {b.route_id:<10} {b.latitude:>10.6f} {b.longitude:>10.6f} "
            f"{b.speed_kmh:>7.1f}k {b.heading_degrees:>5.1f}° {b.passenger_count:>5} "
            f"{b.status:<12} {b.timestamp}"
        )
    print(SEP)
    print(f"Tracking {len(bus_data)} bus(es).  Press Ctrl+C to stop.")


def main():
    consumer = KafkaConsumer(
        TOPIC_NAME,
        bootstrap_servers=KAFKA_BROKER,
        group_id=GROUP_ID,
        auto_offset_reset="latest",
        value_deserializer=lambda v: v.decode("utf-8"),
    )

    print(f"[dashboard] Subscribed to '{TOPIC_NAME}' as group '{GROUP_ID}'.")
    bus_data: dict[str, BusLocation] = {}

    try:
        for msg in consumer:
            event = BusLocation.from_json(msg.value)
            bus_data[event.bus_id] = event
            render_table(bus_data)
    except KeyboardInterrupt:
        print("\n[dashboard] Stopped.")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
