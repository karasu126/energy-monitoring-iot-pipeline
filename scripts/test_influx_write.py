import os
import time

import pandas as pd
from dotenv import load_dotenv
from influxdb_client_3 import InfluxDBClient3, Point

load_dotenv()

TOKEN = os.getenv("INFLUX3_TOKEN")
ORG = os.getenv("INFLUX3_ORG")
HOST = os.getenv("INFLUX3_HOST")
DATABASE = os.getenv("INFLUX3_DATABASE")


def print_section(title: str) -> None:
    print(f"\n{'=' * 72}")
    print(title)
    print(f"{'=' * 72}")


def main() -> None:
    if not all([TOKEN, ORG, HOST, DATABASE]):
        raise RuntimeError("Missing one or more InfluxDB 3 env vars in .env")

    client = InfluxDBClient3(host=HOST, token=TOKEN, org=ORG)

    data = {
        "point1": {"location": "north", "metric": "devices", "count": 23},
        "point2": {"location": "south", "metric": "devices", "count": 30},
        "point3": {"location": "west", "metric": "devices", "count": 28},
    }

    print_section("STEP 1: Writing test points")

    for key, value in data.items():
        point = (
            Point("census")
            .tag("location", value["location"])
            .field(value["metric"], value["count"])
        )
        client.write(database=DATABASE, record=point)
        print(f"[WRITE] {key}: {value}")
        time.sleep(1)

    print("[OK] Write test complete")

    query = """
    SELECT
      time,
      location,
      devices
    FROM census
    ORDER BY time DESC
    LIMIT 10
    """

    print_section("STEP 2: Running query")
    print(query.strip())

    result = client.query(query=query, database=DATABASE, language="sql")

    print_section("STEP 3: Query results")

    try:
        df = result.to_pandas()

        if df.empty:
            print("[INFO] No rows returned")
            return

        # Make output cleaner for terminal viewing
        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"], errors="coerce")

        print(df.to_string(index=False))
        print(f"\n[OK] Returned {len(df)} row(s)")

    except Exception as exc:
        print(f"[ERROR] Failed to render query result: {exc}")
        print("[INFO] Raw result object:")
        print(result)

    print_section("STEP 4: Done")
    print("[OK] InfluxDB write + query test complete")


if __name__ == "__main__":
    main()