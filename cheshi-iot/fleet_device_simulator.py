import json
import os
import random
import signal
import threading
import time
from datetime import datetime, timezone

import pika
from dotenv import load_dotenv

load_dotenv()

CLOUDAMQP_URL = os.getenv("CLOUDAMQP_URL")
QUEUE_NAME = "iot_telemetry"

# --- Energy monitoring domain ---
REGIONS = ["north", "south", "west"]
DEVICE_TYPES = [
    "smart-energy-meter",
    "solar-inverter-monitor",
    "ev-charging-monitor",
]

RUNNING = True


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_payload(device_id: str, region: str, device_type: str, accumulated_energy: float) -> dict:
    """
    Bangun payload energy monitoring.

    Perubahan dari versi agriculture:
      - temperature, humidity, soil_moisture, battery, signal_rssi --> DIHAPUS
      - voltage, current, power, energy, power_factor, frequency   --> DITAMBAHKAN

    Range nilai mengacu standar PLN 220 V / 50 Hz:
      voltage      : 218 – 242 V  (toleransi ±5%)
      current      : 0.5 – 16 A   (beban rumah tangga / ringan industri)
      power_factor : 0.80 – 0.99
      frequency    : 49.8 – 50.2 Hz
      power        : dihitung dari P = V x I (sesuai PDF)
      energy       : akumulasi kWh, bertambah tiap siklus publish
    """
    voltage      = round(random.uniform(218.0, 242.0), 1)
    current      = round(random.uniform(0.5, 16.0), 2)
    power_factor = round(random.uniform(0.80, 0.99), 2)
    frequency    = round(random.uniform(49.8, 50.2), 1)

    # P = V x I — rumus dasar dari PDF
    power = round(voltage * current, 1)

    return {
        "device_id":    device_id,
        "region":       region,
        "device_type":  device_type,
        "voltage":      voltage,
        "current":      current,
        "power":        power,
        "energy":       round(accumulated_energy, 4),  # kWh
        "power_factor": power_factor,
        "frequency":    frequency,
        "ts":           now_iso(),
    }


def device_loop(
    device_id: str,
    region: str,
    device_type: str,
    interval_range: tuple = (2, 6),
) -> None:
    params = pika.URLParameters(CLOUDAMQP_URL)
    params.socket_timeout = 5

    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    # Setiap device punya akumulasi energy sendiri (simulasi kWh meter)
    accumulated_energy = 0.0

    try:
        while RUNNING:
            payload = make_payload(device_id, region, device_type, accumulated_energy)

            # Akumulasi E += P * dt (dt = interval detik / 3600 / 1000 → kWh)
            interval = random.uniform(*interval_range)
            accumulated_energy += payload["power"] * (interval / 3600.0 / 1000.0)

            body = json.dumps(payload)
            channel.basic_publish(exchange="", routing_key=QUEUE_NAME, body=body)
            print(f"[PUB] {device_id} -> {body}")

            time.sleep(interval)
    finally:
        connection.close()


def stop_handler(signum, frame) -> None:
    del signum, frame
    global RUNNING
    RUNNING = False


def main(num_devices: int = 20) -> None:
    if not CLOUDAMQP_URL:
        raise RuntimeError("Missing CLOUDAMQP_URL in .env")

    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)

    threads = []
    for i in range(1, num_devices + 1):
        device_id   = f"meter-{i:03d}"          # meter-001, meter-002, ...
        region      = random.choice(REGIONS)
        device_type = random.choice(DEVICE_TYPES)

        thread = threading.Thread(
            target=device_loop,
            args=(device_id, region, device_type),
            daemon=True,
        )
        thread.start()
        threads.append(thread)

    while RUNNING:
        time.sleep(1)

    for thread in threads:
        thread.join(timeout=1)


if __name__ == "__main__":
    main()