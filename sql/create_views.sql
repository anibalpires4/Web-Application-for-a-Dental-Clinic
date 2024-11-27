DROP VIEW IF EXISTS dim_date;
DROP VIEW IF EXISTS dim_client;
DROP VIEW IF EXISTS dim_location;
DROP VIEW IF EXISTS facts_consultations;
-- view for dim_date --
CREATE VIEW dim_date(date, day, month, year)
AS (
SELECT DISTINCT(date_timestamp) AS date, EXTRACT(DAY FROM
date_timestamp) AS day, EXTRACT(MONTH FROM date_timestamp) AS
month, EXTRACT(YEAR FROM date_timestamp) AS year
FROM consultation
);
-- view for dim_client --
CREATE VIEW dim_client(vat, gender, age)
AS (
SELECT vat, gender, EXTRACT(YEAR FROM AGE(NOW(), birth_date)) AS age
FROM client
);
-- view for dim_location --
CREATE VIEW dim_location(zip, city)
AS (
SELECT zip, city
FROM client
);
-- view for facts_consultations --
CREATE VIEW facts_consultations(vat, date, zip, num_diagnostic_codes,
num_procedures)
AS (
SELECT a.vat_client, c.date_timestamp, cl.zip, COUNT(cd.id) AS
num_diagnostic_codes, COUNT(pic.name) as num_procedures
FROM consultation c
JOIN appointment a
ON c.vat_doctor = a.vat_doctor
AND c.date_timestamp = a.date_timestamp
JOIN client cl
ON a.vat_client = cl.vat
LEFT OUTER JOIN consultation_diagnostic cd
ON c.vat_doctor = cd.vat_doctor
AND c.date_timestamp = cd.date_timestamp
LEFT OUTER JOIN procedure_in_consultation pic
ON cd.vat_doctor = pic.vat_doctor
AND cd.date_timestamp = pic.date_timestamp
GROUP BY (a.vat_client, c.date_timestamp, cl.zip)
ORDER BY a.vat_client, c.date_timestamp
);
