import csv
import random
from datetime import datetime, timedelta

# Number of days
DAYS = 30

# Output file
OUTPUT_FILE = "data/energy_data.csv"

# Devices and their normal hourly energy usage
devices = {
    "Air Conditioner": {
        "type": "HVAC",
        "location": "Office",
        "base": 2.2
    },
    "Computer": {
        "type": "Electronics",
        "location": "Computer Lab",
        "base": 0.8
    },
    "Lighting": {
        "type": "Lighting",
        "location": "Office",
        "base": 0.5
    },
    "Refrigerator": {
        "type": "Appliance",
        "location": "Kitchen",
        "base": 0.9
    },
    "Water Heater": {
        "type": "Appliance",
        "location": "Kitchen",
        "base": 1.6
    },
    "Printer": {
        "type": "Electronics",
        "location": "Office",
        "base": 0.35
    },
    "Server": {
        "type": "IT Equipment",
        "location": "Server Room",
        "base": 1.8
    }
}


def calculate_energy(device, hour):
    base = devices[device]["base"]

    # Working hours increase consumption
    if 9 <= hour <= 18:
        usage_factor = 1.20
    else:
        usage_factor = 0.65

    # Peak hours
    if 13 <= hour <= 17:
        usage_factor *= 1.15

    # Add natural variation
    variation = random.uniform(0.85, 1.15)

    energy = base * usage_factor * variation

    return round(energy, 3)


# Start date
start_date = datetime(2026, 9, 1)

rows = []

for day in range(DAYS):
    current_date = start_date + timedelta(days=day)

    for hour in range(24):

        for device in devices:

            energy = calculate_energy(device, hour)

            # Add a few abnormal readings
            if random.random() < 0.01:
                energy *= random.uniform(2.5, 4.0)

            rows.append([
                current_date.strftime("%Y-%m-%d"),
                f"{hour:02d}:00",
                device,
                devices[device]["type"],
                devices[device]["location"],
                round(energy, 3)
            ])


# Write CSV file
with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as file:

    writer = csv.writer(file)

    writer.writerow([
        "date",
        "time",
        "device",
        "device_type",
        "location",
        "energy_kwh"
    ])

    writer.writerows(rows)


print("Energy dataset generated successfully!")
print(f"Total records: {len(rows)}")
print(f"Devices: {len(devices)}")
print(f"Days: {DAYS}")
print(f"Saved to: {OUTPUT_FILE}")