-- Query to test facts_consultations view
SELECT vat, COUNT(*) AS num_consultations, SUM(num_procedures) AS total_procedures
FROM facts_consultations
GROUP BY vat
ORDER BY total_procedures;
