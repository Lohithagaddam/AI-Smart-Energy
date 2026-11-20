import sqlite3
import pandas as pd

DATABASE_PATH = "database/energy.db"


def get_energy_data():
    """Load energy data with device information."""

    connection = sqlite3.connect(DATABASE_PATH)

    query = """
        SELECT
            e.date,
            e.hour,
            e.energy_kwh,
            d.device_id,
            d.device_name,
            d.device_type,
            d.location,
            d.rated_power
        FROM energy_consumption e
        JOIN devices d
            ON e.device_id = d.device_id
        ORDER BY e.date, e.hour
    """

    dataframe = pd.read_sql_query(query, connection)

    connection.close()

    return dataframe


def get_device_analysis():
    """Calculate device-level energy statistics."""

    dataframe = get_energy_data()

    analysis = (
        dataframe
        .groupby(["device_id", "device_name", "device_type"])
        .agg(
            total_energy_kwh=("energy_kwh", "sum"),
            average_energy_kwh=("energy_kwh", "mean"),
            maximum_energy_kwh=("energy_kwh", "max")
        )
        .reset_index()
    )

    return analysis


def generate_recommendations():
    """Generate intelligent energy-saving recommendations."""

    dataframe = get_energy_data()

    recommendations = []

    # --------------------------------------------------
    # Recommendation 1: Highest consuming device
    # --------------------------------------------------

    device_analysis = get_device_analysis()

    highest_device = device_analysis.loc[
        device_analysis["total_energy_kwh"].idxmax()
    ]

    recommendations.append({
        "type": "High Consumption",
        "priority": "High",
        "device": highest_device["device_name"],
        "title": "Highest Energy Consuming Device",
        "message": (
            f"{highest_device['device_name']} has the highest "
            f"energy consumption at "
            f"{highest_device['total_energy_kwh']:.2f} kWh. "
            f"Consider reducing its operating duration or "
            f"optimizing its usage during peak hours."
        )
    })

    # --------------------------------------------------
    # Recommendation 2: Peak-hour usage
    # --------------------------------------------------

    hourly_usage = (
        dataframe
        .groupby("hour")["energy_kwh"]
        .sum()
        .reset_index()
    )

    peak_hour = hourly_usage.loc[
        hourly_usage["energy_kwh"].idxmax()
    ]

    recommendations.append({
        "type": "Peak Usage",
        "priority": "Medium",
        "device": "All Devices",
        "title": "Peak Consumption Period",
        "message": (
            f"Peak energy consumption occurs around "
            f"{int(peak_hour['hour']):02d}:00. "
            f"Consider shifting non-essential activities "
            f"away from this period."
        )
    })

    # --------------------------------------------------
    # Recommendation 3: Air Conditioner
    # --------------------------------------------------

    ac_data = dataframe[
        dataframe["device_name"] == "Air Conditioner"
    ]

    if not ac_data.empty:

        ac_total = ac_data["energy_kwh"].sum()

        recommendations.append({
            "type": "Energy Saving",
            "priority": "High",
            "device": "Air Conditioner",
            "title": "Optimize Air Conditioner Usage",
            "message": (
                f"The Air Conditioner consumed "
                f"{ac_total:.2f} kWh during the monitored period. "
                f"Using a slightly higher temperature setting, "
                f"maintaining filters, and avoiding unnecessary "
                f"operation can reduce energy consumption."
            )
        })

    # --------------------------------------------------
    # Recommendation 4: Water Heater
    # --------------------------------------------------

    heater_data = dataframe[
        dataframe["device_name"] == "Water Heater"
    ]

    if not heater_data.empty:

        heater_average = heater_data["energy_kwh"].mean()

        recommendations.append({
            "type": "Energy Saving",
            "priority": "Medium",
            "device": "Water Heater",
            "title": "Optimize Water Heater Usage",
            "message": (
                f"The Water Heater has an average consumption "
                f"of {heater_average:.2f} kWh per reading. "
                f"Use scheduled operation and avoid keeping "
                f"the heater running unnecessarily."
            )
        })

    # --------------------------------------------------
    # Recommendation 5: Lighting
    # --------------------------------------------------

    lighting_data = dataframe[
        dataframe["device_name"] == "Lighting"
    ]

    if not lighting_data.empty:

        recommendations.append({
            "type": "Energy Saving",
            "priority": "Low",
            "device": "Lighting",
            "title": "Reduce Unnecessary Lighting",
            "message": (
                "Turn off lights in unoccupied areas and "
                "consider LED lighting for improved efficiency."
            )
        })

    # --------------------------------------------------
    # Recommendation 6: General energy saving
    # --------------------------------------------------

    recommendations.append({
        "type": "General",
        "priority": "Medium",
        "device": "All Devices",
        "title": "Monitor High-Usage Periods",
        "message": (
            "Review the daily energy trends regularly and "
            "investigate sudden increases in consumption."
        )
    })

    return recommendations


def save_recommendations_to_database():
    """Save generated recommendations into SQLite."""

    recommendations = generate_recommendations()

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    # Clear previous generated recommendations
    cursor.execute("DELETE FROM recommendations")

    for recommendation in recommendations:

        device_id = None

        if recommendation["device"] != "All Devices":

            result = cursor.execute(
                """
                SELECT device_id
                FROM devices
                WHERE device_name = ?
                """,
                (recommendation["device"],)
            ).fetchone()

            if result:
                device_id = result[0]

        cursor.execute(
            """
            INSERT INTO recommendations
            (
                device_id,
                title,
                message,
                potential_saving_kwh,
                priority
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                device_id,
                recommendation["title"],
                recommendation["message"],
                None,
                recommendation["priority"]
            )
        )

    connection.commit()
    connection.close()

    print(
        f"{len(recommendations)} recommendations "
        "saved to database."
    )


if __name__ == "__main__":

    print("=" * 60)
    print("AI ENERGY ADVISOR")
    print("=" * 60)

    recommendations = generate_recommendations()

    for index, recommendation in enumerate(
        recommendations, start=1
    ):

        print(f"\n[{index}] {recommendation['title']}")
        print(f"Priority: {recommendation['priority']}")
        print(f"Device: {recommendation['device']}")
        print(f"→ {recommendation['message']}")

    print("\nSaving recommendations to database...")

    save_recommendations_to_database()

    print("\nAI Energy Advisor completed successfully!")