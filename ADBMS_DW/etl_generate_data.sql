INSERT INTO dim_time
SELECT rowid, 
       date('2025-01-01', '+' || rowid || ' day'),
       'Month-' || (rowid % 12),
       2025
FROM sqlite_master LIMIT 1000;

INSERT INTO fact_appointments
SELECT rowid, 1, 1, rowid, 1
FROM sqlite_master LIMIT 1000;
