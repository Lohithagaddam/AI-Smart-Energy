import sqlite3
import csv
import os

DATABASE_PATH = "database/energy.db"
CSV_PATH = "data/energy_data.csv"

# Device information
devices = [
    ("Air Conditioner", "HVAC", "Office", 2.5),
    ("Computer", "Electronics", "Computer Lab", 1.0),
    ("Lighting", "Lighting", "Office", 0.6),
    ("Refrigerator", "Appliance", "Kitchen", 1.2),
    ("Water Heater", "Appliance", "Kitchen", 2.0),
    ("Printer", "Electronics", "Office", 0.5),
    ("Server", "IT Equipment", "Server Room", 2.5)
]

# Connect to database
connection = sqlite3.connect(DATABASE_PATH)
cursor = connection.cursor()

# Enable foreign keys
cursor.execute("PRAGMA foreign_keys = ON")

# Clear old data if the script is run again
cursor.execute("DELETE FROM energy_consumption")
cursor.execute("DELETE FROM devices")

# Insert devices
device_ids = {}

for device in devices:
    cursor.execute("""
        INSERT INTO devices
        (device_name, device_type, location, rated_power, status)
        VALUES (?, ?, ?, ?, ?)
    """, (*device, "Active"))

    device_ids[device[0]] = cursor.lastrowid

# Read CSV and insert energy data
with open(CSV_PATH, "r", encoding="utf-8") as file:
    reader = csv.DictReader(file)

    count = 0

    for row in reader:

        device_name = row["device"]

        if device_name not in device_ids:
            continue

        cursor.execute("""
            INSERT INTO energy_consumption
            (device_id, date, hour, energy_kwh)
            VALUES (?, ?, ?, ?)
        """, (
            device_ids[device_name],
            row["date"],
            int(row["time"].split(":")[0]),
            float(row["energy_kwh"])
        ))

        count += 1

connection.commit()
connection.close()

print("Database seeded successfully!")
print(f"Devices inserted: {len(device_ids)}")
print(f"Energy records inserted: {count}")
print("Database is ready for analytics and AI.")