"""
Logger consumer — group: logger-service

Appends every incoming event as a newline-delimited JSON record to
logs/bus_events.ndjson (relative to the repo root, or wherever LOG_FILE
points). Demonstrates Kafka's durable offset tracking: stop and restart
this consumer and it will resume from where it left off.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from kafka import KafkaConsumer
from config import KAFKA_BROKER, TOPIC_NAME, LOG_FILE
from models import BusLocation

GROUP_ID = "logger-service"


def ensure_log_dir(path: str):
    log_dir = os.path.dirname(path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)


def main():
    # Resolve LOG_FILE relative to the project root (one level above consumers/)
    project_root = os.path.join(os.path.dirname(__file__), "..")
    log_path = os.path.normpath(os.path.join(project_root, LOG_FILE))
    ensure_log_dir(log_path)

    consumer = KafkaConsumer(
        TOPIC_NAME,
        bootstrap_servers=KAFKA_BROKER,
        group_id=GROUP_ID,
        auto_offset_reset="earliest",
        value_deserializer=lambda v: v.decode("utf-8"),
    )

    print(f"[logger] Subscribed to '{TOPIC_NAME}' as group '{GROUP_ID}'.")
    print(f"[logger] Writing events to: {log_path}\n")

    count = 0
    try:
        with open(log_path, "a", encoding="utf-8") as fh:
            for msg in consumer:
                event = BusLocation.from_json(msg.value)
                fh.write(event.to_json() + "\n")
                fh.flush()
                count += 1
                print(f"[logger] Logged event #{count}: {event.bus_id} @ {event.timestamp}")
    except KeyboardInterrupt:
        print(f"\n[logger] Stopped. Total events logged: {count}")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
