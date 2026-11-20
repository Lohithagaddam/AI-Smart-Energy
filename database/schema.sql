-- AI-Assisted Smart Energy Consumption and Power Management System
-- Database Schema

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS devices (
    device_id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_name TEXT NOT NULL UNIQUE,
    device_type TEXT NOT NULL,
    location TEXT,
    rated_power REAL,
    status TEXT DEFAULT 'Active'
);

CREATE TABLE IF NOT EXISTS energy_consumption (
    consumption_id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    hour INTEGER NOT NULL,
    energy_kwh REAL NOT NULL CHECK (energy_kwh >= 0),
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);

CREATE TABLE IF NOT EXISTS energy_cost (
    cost_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    total_energy_kwh REAL NOT NULL,
    tariff REAL NOT NULL,
    total_cost REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS forecasts (
    forecast_id INTEGER PRIMARY KEY AUTOINCREMENT,
    forecast_date TEXT NOT NULL,
    forecast_hour INTEGER NOT NULL,
    predicted_energy_kwh REAL NOT NULL,
    model_name TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS anomalies (
    anomaly_id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER,
    date TEXT NOT NULL,
    hour INTEGER,
    energy_kwh REAL NOT NULL,
    anomaly_score REAL,
    status TEXT,
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);

CREATE TABLE IF NOT EXISTS alerts (
    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER,
    alert_type TEXT NOT NULL,
    message TEXT NOT NULL,
    severity TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    is_read INTEGER DEFAULT 0,
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);

CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    potential_saving_kwh REAL,
    priority TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);

-- 8. USERS TABLE

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 9. USER ENERGY RECORDS TABLE

CREATE TABLE IF NOT EXISTS user_energy_records (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    device_name TEXT NOT NULL,
    rated_power_watts REAL NOT NULL,
    usage_hours_per_day REAL NOT NULL,
    usage_days INTEGER NOT NULL,
    tariff REAL NOT NULL,
    energy_kwh REAL NOT NULL,
    estimated_cost REAL NOT NULL,
    entry_date TEXT DEFAULT CURRENT_DATE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CHECK (rated_power_watts > 0),
    CHECK (usage_hours_per_day > 0 AND usage_hours_per_day <= 24),
    CHECK (usage_days > 0 AND usage_days <= 31),
    CHECK (tariff >= 0),
    CHECK (energy_kwh >= 0),
    CHECK (estimated_cost >= 0)
);

