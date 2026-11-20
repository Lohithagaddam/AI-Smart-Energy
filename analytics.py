import sqlite3
import pandas as pd

DATABASE_PATH = "database/energy.db"


def get_data():
    """Load energy consumption data from the database."""

    connection = sqlite3.connect(DATABASE_PATH)

    query = """
        SELECT
            e.consumption_id,
            e.date,
            e.hour,
            e.energy_kwh,
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


def get_total_consumption():
    """Calculate total energy consumption."""

    dataframe = get_data()

    return round(dataframe["energy_kwh"].sum(), 2)


def get_daily_consumption():
    """Calculate energy consumption for each day."""

    dataframe = get_data()

    daily = (
        dataframe.groupby("date")["energy_kwh"]
        .sum()
        .reset_index()
    )

    daily["energy_kwh"] = daily["energy_kwh"].round(2)

    return daily


def get_device_consumption():
    """Calculate energy consumption by device."""

    dataframe = get_data()

    device_usage = (
        dataframe.groupby("device_name")["energy_kwh"]
        .sum()
        .reset_index()
        .sort_values("energy_kwh", ascending=False)
    )

    device_usage["energy_kwh"] = device_usage["energy_kwh"].round(2)

    return device_usage


def get_peak_hour():
    """Find the hour with the highest total energy consumption."""

    dataframe = get_data()

    hourly = (
        dataframe.groupby("hour")["energy_kwh"]
        .sum()
        .reset_index()
    )

    peak = hourly.loc[hourly["energy_kwh"].idxmax()]

    return {
        "hour": int(peak["hour"]),
        "energy_kwh": round(float(peak["energy_kwh"]), 2)
    }


def calculate_cost(tariff=8.0):
    """
    Estimate electricity cost.

    Default tariff:
    ₹8 per kWh
    """

    total_energy = get_total_consumption()

    cost = total_energy * tariff

    return round(cost, 2)


def calculate_efficiency_score():
    """
    Calculate an application-defined energy efficiency score.

    The score is based on the average hourly consumption.
    It is a project-defined indicator and is not an official
    electricity-provider efficiency rating.
    """

    dataframe = get_data()

    average_usage = dataframe["energy_kwh"].mean()

    if average_usage <= 0.8:
        score = 95
    elif average_usage <= 1.2:
        score = 85
    elif average_usage <= 1.6:
        score = 75
    elif average_usage <= 2.0:
        score = 65
    else:
        score = 55

    return score


def get_summary():
    """Return the main analytics summary."""

    total_energy = get_total_consumption()
    peak = get_peak_hour()
    cost = calculate_cost()
    efficiency = calculate_efficiency_score()

    return {
        "total_energy_kwh": total_energy,
        "estimated_cost": cost,
        "peak_hour": peak["hour"],
        "peak_hour_energy_kwh": peak["energy_kwh"],
        "efficiency_score": efficiency
    }


if __name__ == "__main__":

    print("=" * 50)
    print("SMART ENERGY ANALYTICS")
    print("=" * 50)

    summary = get_summary()

    print(f"Total Energy: {summary['total_energy_kwh']} kWh")
    print(f"Estimated Cost: ₹{summary['estimated_cost']}")
    print(
        f"Peak Hour: {summary['peak_hour']:02d}:00 "
        f"({summary['peak_hour_energy_kwh']} kWh)"
    )
    print(f"Energy Efficiency Score: {summary['efficiency_score']}/100")

    print("\nDevice-wise Consumption:")
    print(get_device_consumption().to_string(index=False))

    print("\nDaily Consumption:")
    print(get_daily_consumption().to_string(index=False))