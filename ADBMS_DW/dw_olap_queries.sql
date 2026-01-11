-- Roll-up (Yearly)
SELECT t.year, SUM(f.appointment_count)
FROM fact_appointments f
JOIN dim_time t ON f.time_id = t.time_id
GROUP BY t.year;

-- Drill-down (Monthly)
SELECT t.month, SUM(f.appointment_count)
FROM fact_appointments f
JOIN dim_time t ON f.time_id = t.time_id
GROUP BY t.month;

-- Slice (Doctor specialization)
SELECT d.specialization, SUM(f.appointment_count)
FROM fact_appointments f
JOIN dim_doctor d ON f.doctor_id = d.doctor_id
GROUP BY d.specialization;
