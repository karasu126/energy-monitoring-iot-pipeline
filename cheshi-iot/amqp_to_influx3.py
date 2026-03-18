import json
import os
import sys

import pika
from dotenv import load_dotenv
from influxdb_client_3 import InfluxDBClient3, Point

load_dotenv()

CLOUDAMQP_URL = os.getenv("CLOUDAMQP_URL")
QUEUE_NAME = "iot_telemetry"

TOKEN    = os.getenv("INFLUX3_TOKEN")
ORG      = os.getenv("INFLUX3_ORG")
HOST     = os.getenv("INFLUX3_HOST")
DATABASE = os.getenv("INFLUX3_DATABASE")


def callback(ch, method, properties, body):
    del ch, method, properties

    try:
        data = json.loads(body.decode("utf-8"))

        # Perubahan dari versi agriculture:
        #   measurement : iot_telemetry        --> energy_telemetry
        #   fields lama : temperature, humidity, soil_moisture,
        #                 battery, signal_rssi  --> DIHAPUS
        #   fields baru : voltage, current, power,
        #                 energy, power_factor, frequency --> DITAMBAHKAN
        #   tags        : device_id, region, device_type  --> TIDAK BERUBAH
        point = (
            Point("energy_telemetry")
            .tag("device_id",   data["device_id"])
            .tag("region",      data["region"])
            .tag("device_type", data.get("device_type", "unknown"))
            .field("voltage",      float(data["voltage"]))
            .field("current",      float(data["current"]))
            .field("power",        float(data["power"]))
            .field("energy",       float(data["energy"]))
            .field("power_factor", float(data["power_factor"]))
            .field("frequency",    float(data["frequency"]))
        )

        client.write(database=DATABASE, record=point)
        print(f"[WRITE] {data['device_id']} -> InfluxDB 3 | "
              f"V={data['voltage']}V  I={data['current']}A  "
              f"P={data['power']}W  PF={data['power_factor']}")

    except KeyError as exc:
        print(f"[ERROR] Missing field in payload: {exc}")
    except Exception as exc:
        print("[ERROR]", exc)


def main() -> None:
    global client

    if not CLOUDAMQP_URL:
        raise RuntimeError("Missing CLOUDAMQP_URL in .env")
    if not all([TOKEN, ORG, HOST, DATABASE]):
        raise RuntimeError("Missing one or more InfluxDB 3 env vars in .env")

    client = InfluxDBClient3(host=HOST, token=TOKEN, org=ORG)

    params = pika.URLParameters(CLOUDAMQP_URL)
    params.socket_timeout = 5

    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=100)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)

    print("[OK] AMQP -> InfluxDB 3 service connected")
    print("[CONFIG] host     =", HOST)
    print("[CONFIG] org      =", ORG)
    print("[CONFIG] database =", DATABASE)
    print("[CONFIG] queue    =", QUEUE_NAME)
    print("[WAIT] Waiting for messages. Press CTRL+C to exit.")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("[STOP] Interrupted by user")
        try:
            connection.close()
        finally:
            sys.exit(0)


if __name__ == "__main__":
    client = None
    main()