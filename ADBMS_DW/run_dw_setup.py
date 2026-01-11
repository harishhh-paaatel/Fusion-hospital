import sqlite3

conn = sqlite3.connect("dw_hospital.db")
cur = conn.cursor()

# 1. STAR SCHEMA
cur.executescript("""
CREATE TABLE IF NOT EXISTS dim_time (
    time_id INTEGER PRIMARY KEY,
    date TEXT,
    month TEXT,
    year INTEGER
);

CREATE TABLE IF NOT EXISTS dim_doctor (
    doctor_id INTEGER PRIMARY KEY,
    specialization TEXT
);

CREATE TABLE IF NOT EXISTS dim_patient (
    patient_id INTEGER PRIMARY KEY,
    gender TEXT,
    age_group TEXT
);

CREATE TABLE IF NOT EXISTS fact_appointments (
    fact_id INTEGER PRIMARY KEY,
    doctor_id INTEGER,
    patient_id INTEGER,
    time_id INTEGER,
    appointment_count INTEGER
);
""")

# 2. SAMPLE DATA
cur.executescript("""
INSERT INTO dim_time VALUES (1,'2025-01-10','January',2025);
INSERT INTO dim_doctor VALUES (1,'Cardiology');
INSERT INTO dim_patient VALUES (1,'Male','40-50');
INSERT INTO fact_appointments VALUES (1,1,1,1,5);
""")

# 3. TRIGGER
cur.executescript("""
CREATE TABLE IF NOT EXISTS dw_summary (
    total_appointments INTEGER
);

INSERT INTO dw_summary
SELECT 0
WHERE NOT EXISTS (SELECT 1 FROM dw_summary);

CREATE TRIGGER IF NOT EXISTS trg_update_summary
AFTER INSERT ON fact_appointments
FOR EACH ROW
BEGIN
    UPDATE dw_summary
    SET total_appointments = total_appointments + NEW.appointment_count;
END;
""")

conn.commit()
conn.close()

print("✅ Data Warehouse setup completed successfully")
