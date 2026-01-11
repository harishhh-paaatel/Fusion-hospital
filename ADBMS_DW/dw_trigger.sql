CREATE TABLE dw_summary (
    total_appointments INTEGER
);

INSERT INTO dw_summary
SELECT 0
WHERE NOT EXISTS (SELECT 1 FROM dw_summary);

CREATE TRIGGER trg_update_summary
AFTER INSERT ON fact_appointments
FOR EACH ROW
BEGIN
    UPDATE dw_summary
    SET total_appointments = total_appointments + NEW.appointment_count;
END;
