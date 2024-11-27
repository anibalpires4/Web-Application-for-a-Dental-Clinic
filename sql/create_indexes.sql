-- JOIN between consultation and appointment INDEX --
CREATE INDEX idx_consultation_vat_doctor_date_timestamp
ON consultation(vat_doctor, date_timestamp);
CREATE INDEX idx_appointment_vat_doctor_date_timestamp
ON appointment(vat_doctor, date_timestamp);
-- JOIN between appointment and client INDEX --
CREATE INDEX idx_appointment_vat_client
ON appointment(vat_client);
CREATE INDEX idx_client_vat
ON client(vat);
-- JOIN between consultation and consultation diagnostic INDEX --
CREATE INDEX idx_consultation_diagnostic_vat_doctor_date_timestamp
ON consultation_diagnostic(vat_doctor, date_timestamp);
-- JOIN between consultation and procedure in consultation INDEX --
CREATE INDEX idx_procedure_in_consultation_vat_doctor_date_timestamp
ON procedure_in_consultation(vat_doctor, date_timestamp);
