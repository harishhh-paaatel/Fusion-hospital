CREATE TABLE dim_time (
    time_id INTEGER PRIMARY KEY,
    date TEXT,
    month TEXT,
    year INTEGER
);

CREATE TABLE dim_doctor (
    doctor_id INTEGER PRIMARY KEY,
    specialization TEXT
);

CREATE TABLE dim_patient (
    patient_id INTEGER PRIMARY KEY,
    gender TEXT,
    age_group TEXT
);

CREATE TABLE fact_appointments (
    fact_id INTEGER PRIMARY KEY,
    doctor_id INTEGER,
    patient_id INTEGER,
    time_id INTEGER,
    appointment_count INTEGER,
    FOREIGN KEY (doctor_id) REFERENCES dim_doctor(doctor_id),
    FOREIGN KEY (patient_id) REFERENCES dim_patient(patient_id),
    FOREIGN KEY (time_id) REFERENCES dim_time(time_id)
);
