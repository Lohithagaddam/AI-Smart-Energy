import sqlite3
import os
import pandas as pd
import numpy as np

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest
import joblib


DATABASE_PATH = "database/energy.db"
MODEL_FOLDER = "models"

FORECAST_MODEL_PATH = os.path.join(
    MODEL_FOLDER, "forecasting_model.pkl"
)

ANOMALY_MODEL_PATH = os.path.join(
    MODEL_FOLDER, "anomaly_model.pkl"
)


def get_energy_data():
    """Load energy consumption data from SQLite."""

    connection = sqlite3.connect(DATABASE_PATH)

    query = """
        SELECT
            e.date,
            e.hour,
            e.energy_kwh,
            d.device_name,
            d.device_type
        FROM energy_consumption e
        JOIN devices d
            ON e.device_id = d.device_id
        ORDER BY e.date, e.hour
    """

    dataframe = pd.read_sql_query(query, connection)

    connection.close()

    return dataframe


# ---------------------------------------------------------
# 1. ENERGY FORECASTING
# ---------------------------------------------------------

def train_forecasting_model():
    """
    Train a Linear Regression model to predict
    total hourly energy consumption.
    """

    dataframe = get_energy_data()

    # Aggregate consumption by date and hour
    hourly_data = (
        dataframe
        .groupby(["date", "hour"])["energy_kwh"]
        .sum()
        .reset_index()
    )

    # Convert date into datetime
    hourly_data["date"] = pd.to_datetime(hourly_data["date"])

    # Create useful time-based features
    hourly_data["day_number"] = (
        hourly_data["date"] - hourly_data["date"].min()
    ).dt.days

    hourly_data["day_of_week"] = (
        hourly_data["date"].dt.dayofweek
    )

    hourly_data["hour"] = hourly_data["hour"].astype(int)

    X = hourly_data[
        ["day_number", "day_of_week", "hour"]
    ]

    y = hourly_data["energy_kwh"]

    # Create model
    model = LinearRegression()

    # Train model
    model.fit(X, y)

    # Create models folder if necessary
    os.makedirs(MODEL_FOLDER, exist_ok=True)

    # Save trained model
    joblib.dump(model, FORECAST_MODEL_PATH)

    print("Forecasting model trained successfully!")
    print(f"Training records: {len(hourly_data)}")
    print(f"Model saved to: {FORECAST_MODEL_PATH}")

    return model


def forecast_next_hours(hours=24):
    """
    Predict energy consumption for the next number of hours.
    """

    dataframe = get_energy_data()

    hourly_data = (
        dataframe
        .groupby(["date", "hour"])["energy_kwh"]
        .sum()
        .reset_index()
    )

    hourly_data["date"] = pd.to_datetime(hourly_data["date"])

    last_date = hourly_data["date"].max()

    last_day_number = (
        last_date - hourly_data["date"].min()
    ).days

    # Load model if available
    if not os.path.exists(FORECAST_MODEL_PATH):
        model = train_forecasting_model()
    else:
        model = joblib.load(FORECAST_MODEL_PATH)

    predictions = []

    for i in range(1, hours + 1):

        total_hours = int(hourly_data.iloc[-1]["hour"]) + i

        future_day_offset = total_hours // 24
        future_hour = total_hours % 24

        future_date = (
            last_date +
            pd.Timedelta(days=future_day_offset)
        )

        future_day_number = (
            future_date - hourly_data["date"].min()
        ).days

        future_day_of_week = future_date.dayofweek

        X_future = pd.DataFrame([{
            "day_number": future_day_number,
            "day_of_week": future_day_of_week,
            "hour": future_hour
        }])

        prediction = model.predict(X_future)[0]

        # Prevent negative energy predictions
        prediction = max(0, prediction)

        predictions.append({
            "date": future_date.strftime("%Y-%m-%d"),
            "hour": future_hour,
            "predicted_energy_kwh": round(
                float(prediction), 2
            )
        })

    return predictions


# ---------------------------------------------------------
# 2. ANOMALY DETECTION
# ---------------------------------------------------------

def train_anomaly_model():
    """
    Train an Isolation Forest model to detect
    unusual energy consumption.
    """

    dataframe = get_energy_data()

    # Use energy consumption as the main feature
    X = dataframe[["energy_kwh"]]

    model = IsolationForest(
        contamination=0.01,
        random_state=42
    )

    model.fit(X)

    os.makedirs(MODEL_FOLDER, exist_ok=True)

    joblib.dump(model, ANOMALY_MODEL_PATH)

    print("Anomaly detection model trained successfully!")
    print(f"Training records: {len(dataframe)}")
    print(f"Model saved to: {ANOMALY_MODEL_PATH}")

    return model


def detect_anomalies():
    """
    Detect unusual energy consumption records.
    """

    dataframe = get_energy_data()

    if not os.path.exists(ANOMALY_MODEL_PATH):
        model = train_anomaly_model()
    else:
        model = joblib.load(ANOMALY_MODEL_PATH)

    X = dataframe[["energy_kwh"]]

    predictions = model.predict(X)
    scores = model.decision_function(X)

    dataframe["anomaly_prediction"] = predictions
    dataframe["anomaly_score"] = scores

    dataframe["status"] = np.where(
        dataframe["anomaly_prediction"] == -1,
        "Anomaly",
        "Normal"
    )

    anomalies = dataframe[
        dataframe["status"] == "Anomaly"
    ].copy()

    anomalies = anomalies.sort_values(
        "anomaly_score"
    )

    return anomalies


# ---------------------------------------------------------
# 3. MAIN PROGRAM
# ---------------------------------------------------------

if __name__ == "__main__":

    print("=" * 60)
    print("SMART ENERGY AI/ML ENGINE")
    print("=" * 60)

    # Train forecasting model
    print("\n[1] ENERGY FORECASTING")
    print("-" * 60)

    train_forecasting_model()

    print("\nForecast for next 24 hours:")

    forecasts = forecast_next_hours(24)

    for forecast in forecasts:
        print(
            f"{forecast['date']} "
            f"{forecast['hour']:02d}:00 → "
            f"{forecast['predicted_energy_kwh']} kWh"
        )

    # Train anomaly model
    print("\n[2] ANOMALY DETECTION")
    print("-" * 60)

    train_anomaly_model()

    anomalies = detect_anomalies()

    print(
        f"Anomalies detected: {len(anomalies)}"
    )

    if len(anomalies) > 0:

        print("\nTop detected anomalies:")

        print(
            anomalies[
                [
                    "date",
                    "hour",
                    "device_name",
                    "energy_kwh",
                    "anomaly_score",
                    "status"
                ]
            ]
            .head(10)
            .to_string(index=False)
        )

    print("\nAI/ML processing completed successfully!")