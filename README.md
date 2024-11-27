# Web Application for a Dental Clinic

This project is a **web-based application** designed to manage and streamline the operations of a dental clinic. It includes functionalities for scheduling appointments, managing client data, viewing consultations, and generating analytics dashboards. The backend uses **PostgreSQL** for the database, and the application is built with **Flask**, with HTML, CSS, and Python for the front-end.

---

## Features
- **Client Management**:
  - Add new clients.
  - View client details, including appointments and consultations.
  - Filter clients based on various criteria (e.g., name, VAT, city).
- **Appointment Scheduling**:
  - Schedule appointments with available doctors.
  - View and modify scheduled appointments.
- **Consultation Details**:
  - View SOAP notes, diagnostics, and prescriptions, and assist nurses with each consultation.
  - Add or modify consultation data.
- **Dashboard**:
  - Visualize total consultations by year, month, and day.
  - Analyze diagnostics by age and gender.
- **Optimized Queries**:
  - Utilizes PostgreSQL views and B+Tree indexes for efficient data retrieval.

---

## Database Design
The database employs normalized tables to ensure data integrity and consistency. Key components:
- **Views**:
  - `dim_date`: Extracts date components for analytics.
  - `dim_client`: Combines client attributes like VAT, gender, and age.
  - `facts_consultations`: Aggregates consultation data for dashboards.
- **Indexes**:
  - Optimized joins and aggregations using B+Tree indexes for faster query execution.

---

## Technologies Used
- **Backend**: Flask (Python)
- **Database**: PostgreSQL
- **Frontend**: HTML, CSS, Jinja2 Templates
- **Deployment**: Docker, Fly.io

---

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/dental-clinic-web-app.git
   cd dental-clinic-web-app
