
from flask import (
    Flask, render_template, jsonify,
    request, redirect, url_for, flash, session
)

import sqlite3

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from database import get_connection

from analytics import (
    get_summary,
    get_device_consumption,
    get_daily_consumption,
    get_peak_hour
)

from ai_model import (
    forecast_next_hours,
    detect_anomalies
)

from recommendations import generate_recommendations


app = Flask(__name__)
app.secret_key = "smart-energy-development-key-2026"


# ==============================
# USER REGISTRATION
# ==============================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("Please fill in all fields.")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password must contain at least 6 characters.")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)
        connection = get_connection()

        try:
            connection.execute(
                """
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
                """,
                (username, email, password_hash)
            )

            connection.commit()
            flash("Registration successful! Please login.")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            flash("This email is already registered.")
            return redirect(url_for("register"))

        finally:
            connection.close()

    return render_template("register.html")


# ==============================
# USER LOGIN
# ==============================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        connection = get_connection()

        try:
            user = connection.execute(
                "SELECT * FROM users WHERE email = ?",
                (email,)
            ).fetchone()

        finally:
            connection.close()

        if user and check_password_hash(
            user["password_hash"], password
        ):

            session.clear()
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]

            flash("Login successful!")

            return redirect(url_for("my_energy"))

        flash("Invalid email or password.")
        return redirect(url_for("login"))

    return render_template("login.html")


# ==============================
# USER LOGOUT
# ==============================

@app.route("/logout")
def logout():

    session.clear()
    flash("You have been logged out.")

    return redirect(url_for("login"))


# ==============================
# PERSONAL ENERGY ENTRY
# ==============================

@app.route("/add-energy-record", methods=["GET", "POST"])
def add_energy_record():

    if "user_id" not in session:
        flash("Please login first.")
        return redirect(url_for("login"))

    if request.method == "POST":

        device_name = request.form.get(
            "device_name", ""
        ).strip()

        try:
            rated_power = float(
                request.form.get("rated_power_watts", 0)
            )

            usage_hours = float(
                request.form.get("usage_hours_per_day", 0)
            )

            usage_days = int(
                request.form.get("usage_days", 0)
            )

            tariff = float(
                request.form.get("tariff", 0)
            )

            if (
                not device_name
                or rated_power <= 0
                or usage_hours <= 0
                or usage_hours > 24
                or usage_days < 1
                or usage_days > 31
                or tariff < 0
            ):
                raise ValueError

        except (ValueError, TypeError):
            flash("Please enter valid energy consumption details.")
            return redirect(url_for("add_energy_record"))

        energy_kwh = (
            (rated_power / 1000) * usage_hours * usage_days
        )

        estimated_cost = energy_kwh * tariff

        connection = get_connection()

        try:
            connection.execute(
                """
                INSERT INTO user_energy_records
                (
                    user_id,
                    device_name,
                    rated_power_watts,
                    usage_hours_per_day,
                    usage_days,
                    tariff,
                    energy_kwh,
                    estimated_cost
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session["user_id"],
                    device_name,
                    rated_power,
                    usage_hours,
                    usage_days,
                    tariff,
                    energy_kwh,
                    estimated_cost
                )
            )

            connection.commit()

        finally:
            connection.close()

        flash(
            f"Record saved! Consumption: {energy_kwh:.2f} kWh. "
            f"Estimated cost: Rs. {estimated_cost:.2f}"
        )

        # UPDATED: OPEN PERSONAL DASHBOARD AFTER SAVING
        return redirect(url_for("my_energy"))

    return render_template("energy_entry.html")


# ==============================
# MY PERSONAL ENERGY DASHBOARD
# ==============================

@app.route("/my-energy")
def my_energy():

    if "user_id" not in session:
        flash("Please login first.")
        return redirect(url_for("login"))

    connection = get_connection()

    try:
        records = connection.execute(
            """
            SELECT *
            FROM user_energy_records
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (session["user_id"],)
        ).fetchall()

        total_energy = sum(
            record["energy_kwh"] for record in records
        )

        total_cost = sum(
            record["estimated_cost"] for record in records
        )

    finally:
        connection.close()

    return render_template(
        "my_energy.html",
        records=records,
        total_energy=total_energy,
        total_cost=total_cost
    )


# ==============================
# EXISTING WEB PAGES - DATASET
# ==============================

@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/analytics")
def analytics():
    return render_template("analytics.html")


@app.route("/devices")
def devices():
    return render_template("devices.html")


@app.route("/forecast")
def forecast():
    return render_template("forecast.html")


@app.route("/anomalies")
def anomalies():
    return render_template("anomalies.html")


@app.route("/advisor")
def advisor():
    return render_template("advisor.html")


@app.route("/reports")
def reports():
    return render_template("reports.html")


# ==========================================
# PERSONAL ENERGY DASHBOARD APIs
# ONLY USER-ENTERED SQLITE RECORDS
# ==========================================

@app.route("/api/my-energy/summary")
def api_my_energy_summary():

    if "user_id" not in session:
        return jsonify({"error": "Please login first"}), 401

    connection = get_connection()

    try:
        user_id = session["user_id"]

        summary = connection.execute(
            """
            SELECT
                COALESCE(SUM(energy_kwh), 0) AS total_energy,
                COALESCE(SUM(estimated_cost), 0) AS total_cost,
                COUNT(*) AS total_records,
                COUNT(DISTINCT device_name) AS total_devices
            FROM user_energy_records
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()

        top_device = connection.execute(
            """
            SELECT
                device_name,
                SUM(energy_kwh) AS energy
            FROM user_energy_records
            WHERE user_id = ?
            GROUP BY device_name
            ORDER BY energy DESC
            LIMIT 1
            """,
            (user_id,)
        ).fetchone()

        if top_device:
            insight = (
                f"{top_device['device_name']} has your highest "
                "recorded energy consumption. Consider reducing "
                "its usage."
            )
        else:
            insight = (
                "Add your appliance records to receive "
                "personal energy insights."
            )

        return jsonify({
            "total_energy_kwh": round(
                float(summary["total_energy"]), 2
            ),
            "estimated_cost": round(
                float(summary["total_cost"]), 2
            ),
            "total_records": summary["total_records"],
            "total_devices": summary["total_devices"],
            "peak_hour": None,
            "efficiency_score": None,
            "ai_insight": insight
        })

    finally:
        connection.close()


@app.route("/api/my-energy/daily-consumption")
def api_my_energy_daily_consumption():

    if "user_id" not in session:
        return jsonify({"error": "Please login first"}), 401

    connection = get_connection()

    try:
        records = connection.execute(
            """
            SELECT
                entry_date AS date,
                SUM(energy_kwh) AS energy_kwh
            FROM user_energy_records
            WHERE user_id = ?
            GROUP BY entry_date
            ORDER BY entry_date
            """,
            (session["user_id"],)
        ).fetchall()

        return jsonify([
            {
                "date": record["date"],
                "energy_kwh": round(
                    float(record["energy_kwh"]), 2
                )
            }
            for record in records
        ])

    finally:
        connection.close()


@app.route("/api/my-energy/device-consumption")
def api_my_energy_device_consumption():

    if "user_id" not in session:
        return jsonify({"error": "Please login first"}), 401

    connection = get_connection()

    try:
        records = connection.execute(
            """
            SELECT
                device_name,
                SUM(energy_kwh) AS energy_kwh
            FROM user_energy_records
            WHERE user_id = ?
            GROUP BY device_name
            ORDER BY energy_kwh DESC
            """,
            (session["user_id"],)
        ).fetchall()

        return jsonify([
            {
                "device_name": record["device_name"],
                "energy_kwh": round(
                    float(record["energy_kwh"]), 2
                )
            }
            for record in records
        ])

    finally:
        connection.close()


# ==============================
# EXISTING REST APIs - DATASET
# DO NOT MIX WITH PERSONAL APIs
# ==============================

@app.route("/api/summary")
def api_summary():
    return jsonify(get_summary())


@app.route("/api/device-consumption")
def api_device_consumption():

    dataframe = get_device_consumption()
    return jsonify(dataframe.to_dict(orient="records"))


@app.route("/api/daily-consumption")
def api_daily_consumption():

    dataframe = get_daily_consumption()
    return jsonify(dataframe.to_dict(orient="records"))


@app.route("/api/peak-hour")
def api_peak_hour():
    return jsonify(get_peak_hour())


@app.route("/api/forecast")
def api_forecast():
    return jsonify(forecast_next_hours(24))


@app.route("/api/anomalies")
def api_anomalies():

    dataframe = detect_anomalies()

    return jsonify(
        dataframe[
            [
                "date",
                "hour",
                "device_name",
                "energy_kwh",
                "anomaly_score",
                "status"
            ]
        ].to_dict(orient="records")
    )


@app.route("/api/recommendations")
def api_recommendations():
    return jsonify(generate_recommendations())


# ==============================
# APPLICATION START
# ==============================

if __name__ == "__main__":

    print("=" * 60)
    print("SMART ENERGY AI WEB APPLICATION")
    print("=" * 60)

    print("Starting Flask server...")
    print("Open your browser at:")
    print("http://127.0.0.1:5000")

    app.run(debug=True)
