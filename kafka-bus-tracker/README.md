# Real-Time Bus Tracking Simulation — Apache Kafka

A self-contained demo that simulates 5 buses emitting GPS telemetry and three independent consumer groups processing those events in real time. Illustrates core Kafka concepts: topics, partitions, consumer groups, and offset management.

---

## Architecture

```
[Producer]  ──►  Kafka topic: bus-locations (5 partitions)
                         │
               ┌─────────┼──────────┐
               ▼         ▼          ▼
        [Dashboard]  [Alerts]  [Logger]
        (group-1)   (group-2)  (group-3)
```

Each consumer group maintains its own independent offset, so all three receive every message regardless of which others have consumed it.

---

## Folder Layout

```
kafka-bus-tracker/
├── docker-compose.yml          # Kafka + Zookeeper (single-node)
├── config.py                   # Topic, broker, simulation constants
├── models.py                   # BusLocation dataclass + JSON helpers
├── producer.py                 # Simulates 5 buses emitting GPS events
├── consumers/
│   ├── __init__.py
│   ├── dashboard_consumer.py   # Group: dashboard-service  (live table)
│   ├── alert_consumer.py       # Group: alert-service      (speed/breakdown flags)
│   └── logger_consumer.py      # Group: logger-service     (NDJSON log file)
├── logs/                       # Created at runtime
├── requirements.txt
└── README.md
```

---

## Prerequisites

- vessel (macOS Secured Containers)
- Python 3.10+

---

## Quick Start

### 1. Start Kafka

`docker-compose.yml` is kept for reference. With vessel, start the two containers directly:

```bash
# Start Zookeeper (docker.io/ prefix pulls from Docker Hub, not docker.apple.com)
vessel run -d --name zookeeper \
  -p 2181:2181 \
  -e ZOOKEEPER_CLIENT_PORT=2181 \
  -e ZOOKEEPER_TICK_TIME=2000 \
  docker.io/confluentinc/cp-zookeeper:7.5.0

# Get Zookeeper's container IP  (vessel uses NAT; IP is under network.address)
vessel inspect zookeeper | grep '"address"'
```

Then start Kafka — use the one-liner below which extracts the IP automatically:

```bash
ZK_IP=$(vessel inspect zookeeper | python3 -c \
  "import sys,json; print(json.load(sys.stdin)['network']['address'])") && \
vessel run -d --name kafka \
  -p 9092:9092 \
  -e KAFKA_BROKER_ID=1 \
  -e KAFKA_ZOOKEEPER_CONNECT=${ZK_IP}:2181 \
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \
  -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 \
  -e KAFKA_AUTO_CREATE_TOPICS_ENABLE=false \
  -e "KAFKA_CREATE_TOPICS=bus-locations:5:1" \
  docker.io/confluentinc/cp-kafka:7.5.0
```

Wait ~15 seconds for Kafka to fully start. Verify:

```bash
vessel ps
```

Both `zookeeper` and `kafka` should appear in the list.

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the producer (Terminal 1)

```bash
python producer.py
```

Output:
```
[producer] BUS_001 | lat=18.5204 lon=73.8567 speed=42.3 km/h | status=ON_ROUTE
[producer] BUS_002 | lat=18.5220 lon=73.8600 speed=38.7 km/h | status=ON_ROUTE
...
```

### 4. Run consumers (separate terminals)

**Terminal 2 — Live dashboard:**
```bash
python consumers/dashboard_consumer.py
```

**Terminal 3 — Speed / breakdown alerts:**
```bash
python consumers/alert_consumer.py
```

**Terminal 4 — Event logger:**
```bash
python consumers/logger_consumer.py
```

Check the log file:
```bash
cat logs/bus_events.ndjson
```

---

## Consumer Group Behaviour

| Consumer | Group ID | `auto_offset_reset` | Purpose |
|---|---|---|---|
| `dashboard_consumer.py` | `dashboard-service` | `latest` | Live position table |
| `alert_consumer.py` | `alert-service` | `earliest` | Speed/breakdown alerts |
| `logger_consumer.py` | `logger-service` | `earliest` | Durable NDJSON log |

### Demonstrating offset durability

1. Stop `logger_consumer.py` (Ctrl+C).
2. Let the producer run for 30+ seconds.
3. Restart `logger_consumer.py`.

The logger resumes from the last committed offset — it catches up on all missed events, demonstrating Kafka's at-least-once delivery guarantee.

---

## Message Schema

```json
{
  "bus_id": "BUS_001",
  "route_id": "ROUTE_A",
  "latitude": 18.5204,
  "longitude": 73.8567,
  "speed_kmh": 42.3,
  "heading_degrees": 90.0,
  "passenger_count": 17,
  "status": "ON_ROUTE",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

Possible `status` values: `ON_ROUTE`, `STOPPED`, `BREAKDOWN`

---

## Configuration (`config.py`)

| Constant | Default | Description |
|---|---|---|
| `KAFKA_BROKER` | `localhost:9092` | Broker address |
| `TOPIC_NAME` | `bus-locations` | Topic name |
| `NUM_PARTITIONS` | `5` | One per bus for ordered delivery |
| `EMIT_INTERVAL_S` | `2` | Seconds between producer ticks |
| `SPEED_ALERT_KMPH` | `60` | Alert threshold for alert consumer |
| `LOG_FILE` | `logs/bus_events.ndjson` | Log output path |

---

## Stopping

```bash
# Stop all consumers with Ctrl+C in each terminal
# Stop and remove Kafka containers:
vessel stop kafka zookeeper
vessel rm kafka zookeeper
```

To also delete stored Kafka data (topics, offsets), remove any associated volumes:
```bash
vessel volume rm $(vessel volume ls -q)
```

---

## Key Kafka Concepts Demonstrated

| Concept | Where |
|---|---|
| **Topics & Partitions** | `bus-locations` topic with 5 partitions |
| **Message Keys** | `bus_id` as key → same partition per bus = ordered delivery |
| **Consumer Groups** | 3 independent groups each receive all messages |
| **Offset Management** | Stop/restart `logger_consumer` to see replay |
| **At-least-once delivery** | `earliest` reset on logger/alert consumers |
