
---

# Energy Monitoring IoT Pipeline

A hands-on project demonstrating a **cloud-based IoT energy monitoring pipeline** using managed services and Python-based device simulation.

The project simulates a fleet of energy monitoring devices sending electrical telemetry to a cloud message broker, which is then ingested into a time-series database and visualized using Grafana.

---

# Architecture Overview

The system architecture:

```
Python Device Simulators
        │
        ▼
CloudAMQP (LavinMQ) Queue
        │
        ▼
Python Ingestion Service
        │
        ▼
InfluxDB 3 (Time-Series Database)
        │
        ▼
Grafana Dashboards
```

Pipeline flow:

```
Producer(s) → CloudAMQP Queue → Consumer → InfluxDB → Grafana
```

Each component has a clearly defined role:

| Component        | Role                                                        |
| ---------------- | ----------------------------------------------------------- |
| Python Producers | Simulated energy monitoring devices sending telemetry       |
| CloudAMQP        | Managed message broker buffering device data                |
| Python Consumer  | Reads queue messages and stores them                        |
| InfluxDB 3       | Time-series database for electrical telemetry               |
| Grafana          | Visualization dashboards for energy monitoring              |

---

# Project Structure

```
.
├── Flow Diagram.png
├── README.md
├── requirements.txt
├── .env
│
├── cheshi-iot/
│   ├── fleet_device_simulator.py
│   ├── amqp_to_influx3.py
│   ├── diagram.json
│   └── sketch.ino
│
└── scripts/
    ├── test_broker_connection.py
    └── test_influx_write.py
```

---

# Environment Setup

## 1 Install Python

Recommended:

```
Python 3.10+
```

Check version:

```bash
python --version
```

---

## 2 Create virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate
```

Windows:

```bash
venv\Scripts\activate
```

---

## 3 Install dependencies

```bash
pip install -r requirements.txt
```

Dependencies:

| Package          | Purpose                          |
| ---------------- | -------------------------------- |
| pika             | AMQP client for CloudAMQP        |
| influxdb3-python | InfluxDB client                  |
| python-dotenv    | Load environment variables       |
| pandas           | Used for query output formatting |

---

# Environment Configuration

Create a `.env` file at the project root.

```bash
touch .env
```

Edit `.env`:

```
CLOUDAMQP_URL=amqps://USERNAME:PASSWORD@dog.lmq.cloudamqp.com/VHOST

INFLUX3_HOST=https://us-east-1-1.aws.cloud2.influxdata.com
INFLUX3_ORG=Dev
INFLUX3_DATABASE=energy-monitoring
INFLUX3_TOKEN=YOUR_INFLUX_TOKEN
```

Required values:

| Variable         | Description                     |
| ---------------- | ------------------------------- |
| CLOUDAMQP_URL    | CloudAMQP broker connection URL |
| INFLUX3_HOST     | InfluxDB Cloud endpoint         |
| INFLUX3_ORG      | Influx organization             |
| INFLUX3_DATABASE | Database name                   |
| INFLUX3_TOKEN    | API token                       |

---

# Script Overview

## scripts/

### test_broker_connection.py

Purpose:

Test connectivity to CloudAMQP.

Steps performed:

1. connect to AMQP broker
2. declare queue
3. publish test message
4. close connection

Run:

```bash
python scripts/test_broker_connection.py
```

Expected output:

```
[OK] Queue declared
[OK] Test message published
```

---

### test_influx_write.py

Purpose:

Validate InfluxDB connectivity.

Functions:

* write sample points
* execute SQL query
* print query results

Run:

```bash
python scripts/test_influx_write.py
```

Expected output:

```
STEP 1: Writing test points
STEP 2: Running query
STEP 3: Query results
```

---

# Device Simulator

Simulates energy monitoring devices sending electrical telemetry.

Queue used:

```
iot_telemetry
```

---

## fleet_device_simulator.py

Simulates multiple energy monitoring devices concurrently.

Features:

* multiple device threads
* randomized electrical telemetry
* random publish intervals
* per-device accumulated energy (kWh)

Device types simulated:

```
smart-energy-meter
solar-inverter-monitor
ev-charging-monitor
```

Telemetry example:

```json
{
  "device_id": "meter-001",
  "region": "north",
  "device_type": "smart-energy-meter",
  "voltage": 230.5,
  "current": 4.2,
  "power": 967.3,
  "energy": 15.6,
  "power_factor": 0.94,
  "frequency": 50.0
}
```

Run:

```bash
python cheshi-iot/fleet_device_simulator.py
```

Default simulation:

```
20 devices
```

Example output:

```
[PUB] meter-005 -> {...}
[PUB] meter-012 -> {...}
```

---

# Ingestion Service

Consumes queue messages and writes them to InfluxDB.

---

## amqp_to_influx3.py

Full ingestion service for the energy monitoring pipeline.

Workflow:

```
Queue message
    ↓
JSON decode
    ↓
InfluxDB Point
    ↓
Write to database
```

Stored fields:

| Tag         | Field        |
| ----------- | ------------ |
| device_id   | voltage      |
| region      | current      |
| device_type | power        |
|             | energy       |
|             | power_factor |
|             | frequency    |

Run:

```bash
python cheshi-iot/amqp_to_influx3.py
```

Output:

```
[WRITE] meter-004 -> InfluxDB | V=230.5V  I=4.2A  P=967.3W  PF=0.94
```

---

# Running the End-to-End Demo

Open two terminals.

---

## Terminal 1

Start ingestion service.

```bash
python cheshi-iot/amqp_to_influx3.py
```

---

## Terminal 2

Start fleet simulator.

```bash
python cheshi-iot/fleet_device_simulator.py
```

---

## Expected behavior

Producer output:

```
[PUB] meter-003 -> {...}
```

Consumer output:

```
[WRITE] meter-003 -> InfluxDB
```

CloudAMQP:

```
Queue activity visible
```

InfluxDB:

```
Rows increasing
```

---

# Querying Data in InfluxDB

Example SQL queries.

---

## Latest telemetry

```sql
SELECT *
FROM energy_telemetry
ORDER BY time DESC
LIMIT 20;
```

---

## Average power consumption by region

```sql
SELECT
  region,
  AVG(power)
FROM energy_telemetry
GROUP BY region;
```

---

## Energy consumption per device

```sql
SELECT
  device_id,
  MAX(energy) AS total_energy_kwh
FROM energy_telemetry
GROUP BY device_id;
```

---

## Voltage stability monitoring

```sql
SELECT
  time,
  device_id,
  voltage
FROM energy_telemetry
ORDER BY time DESC
LIMIT 20;
```

---

# Grafana Dashboards

Recommended panels.

---

## Voltage monitoring over time

```
time series chart
```

Query:

```sql
SELECT time, device_id, voltage
FROM energy_telemetry
ORDER BY time DESC
```

---

## Active power per device

```
time series chart
```

Query:

```sql
SELECT time, device_id, power
FROM energy_telemetry
ORDER BY time DESC
```

---

## Energy consumption per device

```
bar chart
```

Query:

```sql
SELECT device_id, MAX(energy) AS total_energy_kwh
FROM energy_telemetry
GROUP BY device_id
```

---

## Power factor efficiency

```
gauge
```

Query:

```sql
SELECT device_id, AVG(power_factor) AS avg_power_factor
FROM energy_telemetry
GROUP BY device_id
```

---

## Grid frequency stability

```
time series chart
```

Query:

```sql
SELECT time, AVG(frequency) AS avg_frequency
FROM energy_telemetry
GROUP BY time
ORDER BY time DESC
```

---

# Grafana Setup (Self-Hosted)

Grafana is deployed locally using Docker Compose.

```bash
cd grafana
docker compose up -d
```

Access:

```
http://localhost:3000
```

Configure datasource:

* Type: **Flight SQL**
* Host: InfluxDB Cloud host (without `https://`)
* Port: `443`
* Auth Type: token
* Token: `INFLUX3_TOKEN`
* Require TLS/SSL: enabled
* Metadata key: `database` → value: `INFLUX3_DATABASE`

> InfluxDB 3 uses the Apache Arrow Flight SQL protocol. Use the
> `influxdata-flightsql-datasource` plugin, not the standard InfluxDB datasource.

---

# Troubleshooting

## Broker connection fails

Check:

* CLOUDAMQP_URL
* network connectivity
* TLS port

Test with:

```bash
python scripts/test_broker_connection.py
```

---

## Influx authentication error

Error example:

```
401 unauthorized
```

Solution:

* regenerate API token
* confirm org name
* verify database name

Test with:

```bash
python scripts/test_influx_write.py
```

---

## Queue receives no messages

Check:

* producer running
* queue name matches
* broker dashboard

---

# Electrical Telemetry Reference

## Telemetry fields

| Field        | Description                        | Unit |
| ------------ | ---------------------------------- | ---- |
| voltage      | Electrical voltage                 | V    |
| current      | Electrical current                 | A    |
| power        | Active power consumption (P = V×I) | W    |
| energy       | Accumulated energy usage           | kWh  |
| power_factor | Efficiency of electrical load      | —    |
| frequency    | Grid frequency                     | Hz   |

## Power formula

```
P = V × I
```

Where P = Power (Watts), V = Voltage (Volts), I = Current (Amperes).

## Simulated value ranges (PLN 220V / 50Hz standard)

| Field        | Min   | Max   |
| ------------ | ----- | ----- |
| voltage      | 218 V | 242 V |
| current      | 0.5 A | 16 A  |
| power_factor | 0.80  | 0.99  |
| frequency    | 49.8  | 50.2  |

---

# Summary

This project demonstrates a scalable IoT energy monitoring pipeline using:

* Python device simulation
* managed AMQP messaging
* time-series storage
* real-time dashboards

Key concept demonstrated:

```
Decoupled cloud ingestion using message queues
```

---
