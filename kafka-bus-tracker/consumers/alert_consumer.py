"""
Alert consumer — group: alert-service

Flags events where speed_kmh exceeds SPEED_ALERT_KMPH or
status is "BREAKDOWN". Each alert is printed with a timestamp.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from kafka import KafkaConsumer
from config import KAFKA_BROKER, TOPIC_NAME, SPEED_ALERT_KMPH
from models import BusLocation

GROUP_ID = "alert-service"


def check_alerts(event: BusLocation) -> list[str]:
    alerts = []
    if event.speed_kmh > SPEED_ALERT_KMPH:
        alerts.append(
            f"SPEED ALERT  | {event.bus_id} on {event.route_id} "
            f"travelling at {event.speed_kmh} km/h  (limit {SPEED_ALERT_KMPH} km/h)"
        )
    if event.status == "BREAKDOWN":
        alerts.append(
            f"BREAKDOWN    | {event.bus_id} on {event.route_id} "
            f"reported BREAKDOWN at ({event.latitude}, {event.longitude})"
        )
    return alerts


def main():
    consumer = KafkaConsumer(
        TOPIC_NAME,
        bootstrap_servers=KAFKA_BROKER,
        group_id=GROUP_ID,
        auto_offset_reset="earliest",
        value_deserializer=lambda v: v.decode("utf-8"),
    )

    print(f"[alerts] Subscribed to '{TOPIC_NAME}' as group '{GROUP_ID}'.")
    print(f"[alerts] Speed threshold: {SPEED_ALERT_KMPH} km/h\n")

    try:
        for msg in consumer:
            event = BusLocation.from_json(msg.value)
            for alert in check_alerts(event):
                print(f"[{event.timestamp}] *** {alert}")
    except KeyboardInterrupt:
        print("\n[alerts] Stopped.")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
