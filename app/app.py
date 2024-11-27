import os
from logging.config import dictConfig
import psycopg
from datetime import datetime, time
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from psycopg.rows import namedtuple_row

# Database connection URL
DATABASE_URL = "postgres://db:db@postgres/db"

# Logging configuration
dictConfig({
    "version": 1,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] %(levelname)s in %(module)s:%(lineno)s - %(funcName)20s(): %(message)s",
        }
    },
    "handlers": {
        "wsgi": {
            "class": "logging.StreamHandler",
            "stream": "ext://flask.logging.wsgi_errors_stream",
            "formatter": "default",
        }
    },
    "root": {"level": "INFO", "handlers": ["wsgi"]},
})

# Flask app initialization
app = Flask(__name__)
app.config.from_prefixed_env()
log = app.logger

# Route to display all clients alphabetically
@app.route("/", methods=("GET",))
@app.route("/clients", methods=("GET",))
def client_index():
    """Show all clients in alphabetical order."""
    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            clients = cur.execute("""
                SELECT vat, name, birth_date, street, city, zip, gender
                FROM client
                ORDER BY name ASC;
            """).fetchall()
    return render_template("clients/clients.html", clients=clients)

# Route for dashboard statistics
@app.route("/dashboard", methods=("GET",))
def facts_consultations():
    """Display consultation statistics on the dashboard."""
    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            consultation_per_grouped_time = cur.execute("""
                SELECT dd.year, dd.month, dd.day, COUNT(*) AS total_consultation
                FROM facts_consultations fc
                JOIN dim_date dd ON fc.date = dd.date
                GROUP BY ROLLUP(dd.year, dd.month, dd.day)
                ORDER BY dd.year, dd.month, dd.day;
            """).fetchall()

            diagnostic_per_age_and_sex = cur.execute("""
                SELECT dc.age, dc.gender, SUM(fc.num_diagnostic_codes) AS total_diagnostic_codes
                FROM facts_consultations fc
                JOIN dim_client dc ON fc.vat = dc.vat
                GROUP BY CUBE(dc.age, dc.gender)
                ORDER BY dc.age, dc.gender;
            """).fetchall()

    return render_template(
        "dashboard.html",
        consultation_per_grouped_time=consultation_per_grouped_time,
        diagnostic_per_age_and_sex=diagnostic_per_age_and_sex
    )

# Route to show client information
@app.route("/clients/<vat>", methods=("GET",))
def client_info(vat):
    """Display information and appointments for a specific client."""
    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            client_appointments = cur.execute("""
                SELECT vat_doctor, date_timestamp, description
                FROM appointment
                WHERE vat_client = %(vat)s
                ORDER BY date_timestamp ASC;
            """, {"vat": vat}).fetchall()

            client_consultations = cur.execute("""
                SELECT c.vat_doctor, c.date_timestamp
                FROM consultation c
                JOIN appointment a ON c.vat_doctor = a.vat_doctor AND c.date_timestamp = a.date_timestamp
                WHERE a.vat_client = %(vat)s
                ORDER BY c.date_timestamp ASC;
            """, {"vat": vat}).fetchall()

    return render_template(
        "clients/informations.html",
        vat=vat,
        client_consultations=client_consultations,
        client_appointments=client_appointments
    )

# Route for consultation details
@app.route("/clients/<vat>/consultation/<vat_doctor>/<date_timestamp>", methods=("GET",))
def consultation_information(vat, vat_doctor, date_timestamp):
    """Retrieve and display detailed information about a consultation."""
    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            soap_notes = cur.execute("""
                SELECT soap_s, soap_o, soap_a, soap_p
                FROM consultation
                WHERE vat_doctor = %(vat_doctor)s AND date_timestamp = %(date_timestamp)s;
            """, {"vat_doctor": vat_doctor, "date_timestamp": date_timestamp}).fetchone()

            diagnostics = cur.execute("""
                SELECT cd.id
                FROM consultation_diagnostic cd
                WHERE cd.vat_doctor = %(vat_doctor)s AND cd.date_timestamp = %(date_timestamp)s;
            """, {"vat_doctor": vat_doctor, "date_timestamp": date_timestamp}).fetchall()

            prescriptions = cur.execute("""
                SELECT p.name, p.lab, p.dosage, p.description
                FROM prescription p
                WHERE p.vat_doctor = %(vat_doctor)s AND p.date_timestamp = %(date_timestamp)s;
            """, {"vat_doctor": vat_doctor, "date_timestamp": date_timestamp}).fetchall()

            assisting_nurse = cur.execute("""
                SELECT vat_nurse
                FROM consultation_assistant ca
                WHERE ca.vat_doctor = %(vat_doctor)s AND ca.date_timestamp = %(date_timestamp)s;
            """, {"vat_doctor": vat_doctor, "date_timestamp": date_timestamp}).fetchone()

    return render_template(
        "clients/consultation_informations.html",
        soap_notes=soap_notes,
        diagnostics=diagnostics,
        prescriptions=prescriptions,
        assisting_nurse=assisting_nurse,
        vat=vat,
        date_timestamp=date_timestamp,
        vat_doctor=vat_doctor
    )

# SOAP_S
@app.route("/clients/<vat>/consultation/<vat_doctor>/<date_timestamp>/soapS", methods=("GET",))
def modify_soap_s_view(vat, vat_doctor, date_timestamp):
    return render_template(
        "/clients/modify_soap_s.html",
        vat=vat,
        vat_doctor=vat_doctor,
        date_timestamp=date_timestamp
    )


@app.route("/clients/<vat>/consultation/<vat_doctor>/<date_timestamp>/soapS", methods=("POST",))
def modify_soap_s(vat, vat_doctor, date_timestamp):
    new_soap_s = request.form.get('soap_s', None)
    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            cur.execute(
                """
                UPDATE consultation
                SET soap_s = %(new_soap_s)s
                WHERE vat_doctor = %(vat_doctor)s
                AND date_timestamp = %(date_timestamp)s;
                """,
                {
                    "new_soap_s": new_soap_s,
                    "vat_doctor": vat_doctor,
                    "date_timestamp": date_timestamp,
                }
            )
            conn.commit()

    return redirect(url_for(
        "consultation_information",
        vat=vat,
        vat_doctor=vat_doctor,
        date_timestamp=date_timestamp
    ))

# SOAP_O
@app.route("/clients/<vat>/consultation/<vat_doctor>/<date_timestamp>/modify/soapO", methods=("GET",))
def modify_soap_o_view(vat, vat_doctor, date_timestamp):
    return render_template(
        "/clients/modify_soap_o.html",
        vat=vat,
        vat_doctor=vat_doctor,
        date_timestamp=date_timestamp
    )


@app.route("/clients/<vat>/consultation/<vat_doctor>/<date_timestamp>/modify/soapO", methods=("POST",))
def modify_soap_o(vat, vat_doctor, date_timestamp):
    new_soap_o = request.form.get('soap_o', None)
    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            cur.execute(
                """
                UPDATE consultation
                SET soap_o = %(new_soap_o)s
                WHERE vat_doctor = %(vat_doctor)s
                AND date_timestamp = %(date_timestamp)s;
                """,
                {
                    "new_soap_o": new_soap_o,
                    "vat_doctor": vat_doctor,
                    "date_timestamp": date_timestamp,
                }
            )
            conn.commit()

    return redirect(url_for(
        "consultation_information",
        vat=vat,
        vat_doctor=vat_doctor,
        date_timestamp=date_timestamp
    ))

# SOAP_A
@app.route("/clients/<vat>/consultation/<vat_doctor>/<date_timestamp>/modify/soapA", methods=("GET",))
def modify_soap_a_view(vat, vat_doctor, date_timestamp):
    return render_template(
        "/clients/modify_soap_a.html",
        vat=vat,
        vat_doctor=vat_doctor,
        date_timestamp=date_timestamp
    )


@app.route("/clients/<vat>/consultation/<vat_doctor>/<date_timestamp>/modify/soapA", methods=("POST",))
def modify_soap_a(vat, vat_doctor, date_timestamp):
    new_soap_a = request.form.get('soap_a', None)
    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            cur.execute(
                """
                UPDATE consultation
                SET soap_a = %(new_soap_a)s
                WHERE vat_doctor = %(vat_doctor)s
                AND date_timestamp = %(date_timestamp)s;
                """,
                {
                    "new_soap_a": new_soap_a,
                    "vat_doctor": vat_doctor,
                    "date_timestamp": date_timestamp,
                }
            )
            conn.commit()

    return redirect(url_for(
        "consultation_information",
        vat=vat,
        vat_doctor=vat_doctor,
        date_timestamp=date_timestamp
    ))

# SOAP_P
@app.route("/clients/<vat>/consultation/<vat_doctor>/<date_timestamp>/modify/soapP", methods=("GET",))
def modify_soap_p_view(vat, vat_doctor, date_timestamp):
    return render_template(
        "/clients/modify_soap_p.html",
        vat=vat,
        vat_doctor=vat_doctor,
        date_timestamp=date_timestamp
    )


@app.route("/clients/<vat>/consultation/<vat_doctor>/<date_timestamp>/modify/soapP", methods=("POST",))
def modify_soap_p(vat, vat_doctor, date_timestamp):
    new_soap_p = request.form.get('soap_p', None)

    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            cur.execute(
                """
                UPDATE consultation
                SET soap_p = %(new_soap_p)s
                WHERE vat_doctor = %(vat_doctor)s
                AND date_timestamp = %(date_timestamp)s;
                """,
                {
                    "new_soap_p": new_soap_p,
                    "vat_doctor": vat_doctor,
                    "date_timestamp": date_timestamp,
                }
            )
            conn.commit()

    return redirect(url_for(
        "consultation_information",
        vat=vat,
        vat_doctor=vat_doctor,
        date_timestamp=date_timestamp
    ))

# Assisting nurse
@app.route("/clients/<vat>/consultation/<vat_doctor>/<date_timestamp>/modify/nurse", methods=("GET",))
def modify_nurse_view(vat, vat_doctor, date_timestamp):
    """Display available nurses to assign to the consultation."""
    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            nurses = cur.execute("""
                SELECT vat FROM nurse;
            """).fetchall()
    return render_template("/clients/modify_nurse.html", vat=vat, vat_doctor=vat_doctor, date_timestamp=date_timestamp, nurses=nurses)

@app.route("/clients/<vat>/consultation/<vat_doctor>/<date_timestamp>/modify/nurse", methods=("POST",))
def modify_nurse(vat, vat_doctor, date_timestamp):
    """Update the assisting nurse for a consultation."""
    new_nurse = request.form.get('nurse')
    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            cur.execute("""
                UPDATE consultation_assistant
                SET vat_nurse = %(new_nurse)s
                WHERE vat_doctor = %(vat_doctor)s AND date_timestamp = %(date_timestamp)s;
            """, {"new_nurse": new_nurse, "vat_doctor": vat_doctor, "date_timestamp": date_timestamp})
            conn.commit()
    return redirect(url_for("consultation_information", vat=vat, vat_doctor=vat_doctor, date_timestamp=date_timestamp))

# Add diagnostic code
@app.route("/clients/<vat>/consultation/<vat_doctor>/<date_timestamp>/add/diagnostic", methods=("GET",))
def add_diagnostic_view(vat, vat_doctor, date_timestamp):
    """Display available diagnostics to add."""
    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            diagnostics = cur.execute("""
                SELECT id FROM diagnostic_code;
            """).fetchall()
    return render_template("/clients/add_diagnostic.html", vat=vat, vat_doctor=vat_doctor, date_timestamp=date_timestamp, diagnostics=diagnostics)

@app.route("/clients/<vat>/consultation/<vat_doctor>/<date_timestamp>/add/diagnostic", methods=("POST",))
def add_diagnostic(vat, vat_doctor, date_timestamp):
    """Add a diagnostic code to the consultation."""
    new_diagnostic = request.form.get('diagnostic')
    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            cur.execute("""
                INSERT INTO consultation_diagnostic (vat_doctor, date_timestamp, id)
                VALUES (%(vat_doctor)s, %(date_timestamp)s, %(new_diagnostic)s);
            """, {"vat_doctor": vat_doctor, "date_timestamp": date_timestamp, "new_diagnostic": new_diagnostic})
            conn.commit()
    return redirect(url_for("consultation_information", vat=vat, vat_doctor=vat_doctor, date_timestamp=date_timestamp))

# Add prescription
@app.route("/clients/<vat>/consultation/<vat_doctor>/<date_timestamp>/add/prescription", methods=("GET",))
def add_prescription_view(vat, vat_doctor, date_timestamp):
    """Display form to add a prescription."""
    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            medications = cur.execute("""
                SELECT name, lab FROM medication;
            """).fetchall()
            diagnostics = cur.execute("""
                SELECT id FROM consultation_diagnostic
                WHERE vat_doctor = %(vat_doctor)s AND date_timestamp = %(date_timestamp)s;
            """, {"vat_doctor": vat_doctor, "date_timestamp": date_timestamp}).fetchall()
    return render_template("/clients/add_prescription.html", vat=vat, vat_doctor=vat_doctor, date_timestamp=date_timestamp, medications=medications, diagnostics=diagnostics)

@app.route("/clients/<vat>/consultation/<vat_doctor>/<date_timestamp>/add/prescription", methods=("POST",))
def add_prescription(vat, vat_doctor, date_timestamp):
    """Insert a prescription for a consultation."""
    prescription_data = {
        "vat_doctor": vat_doctor,
        "date_timestamp": date_timestamp,
        "id": request.form.get('id'),
        "name": request.form.get('name'),
        "lab": request.form.get('brand'),
        "dosage": request.form.get('dosage'),
        "description": request.form.get('description'),
    }
    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            cur.execute("""
                INSERT INTO prescription (vat_doctor, date_timestamp, id, name, lab, dosage, description)
                VALUES (%(vat_doctor)s, %(date_timestamp)s, %(id)s, %(name)s, %(lab)s, %(dosage)s, %(description)s);
            """, prescription_data)
            conn.commit()
    return redirect(url_for("consultation_information", vat=vat, vat_doctor=vat_doctor, date_timestamp=date_timestamp))

# Add schedule appointments
@app.route("/clients/<vat>/schedule", methods=("GET",))
def schedule_appointment_view(vat):
    """Display the form for scheduling an appointment."""
    return render_template("clients/schedule_appointment.html", vat=vat)

@app.route("/client/<vat>/schedule", methods=("GET",))
def search_doctors(vat):
    """Search available doctors for a specific date and time."""
    date = request.args.get('date')
    time = request.args.get('time')
    date_timestamp = f"{date} {time}:00"
    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            available_doctors = cur.execute("""
                SELECT e.name, e.vat
                FROM employee e
                JOIN doctor d ON e.vat = d.vat
                WHERE NOT EXISTS (
                    SELECT vat_doctor FROM appointment
                    WHERE date_timestamp = %(date_timestamp)s AND vat_doctor = e.vat
                );
            """, {"date_timestamp": date_timestamp}).fetchall()
    return render_template("clients/schedule_appointment.html", vat=vat, available_doctors=available_doctors)

@app.route("/client/<vat>/schedule", methods=("POST",))
def add_appointment(vat):
    """Add a new appointment to the database."""
    appointment_data = {
        "vat_doctor": request.form.get('doctor'),
        "date_timestamp": f"{request.form.get('date')} {request.form.get('time')}:00",
        "vat_client": vat,
        "description": request.form.get('description', ''),
    }
    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            cur.execute("""
                INSERT INTO appointment (vat_doctor, date_timestamp, vat_client, description)
                VALUES (%(vat_doctor)s, %(date_timestamp)s, %(vat_client)s, %(description)s);
            """, appointment_data)
            conn.commit()
    return redirect(url_for("client_index"))

# Route to filter clients
@app.route("/clients/filter", methods=("GET",))
def client_filter():
    """Filter clients based on multiple criteria."""
    vat_filter = request.args.get('vat', None)
    name_filter = request.args.get('name', None)
    street_filter = request.args.get('street', None)
    city_filter = request.args.get('city', None)
    zip_filter = request.args.get('zip', None)

    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            client_filter = cur.execute("""
                SELECT vat, name, street, city, zip, gender
                FROM client
                WHERE CAST(vat AS TEXT) LIKE %(vat)s
                AND name ILIKE %(name)s
                AND street ILIKE %(street)s
                AND city ILIKE %(city)s
                AND zip ILIKE %(zip)s
                ORDER BY name ASC;
            """, {
                "vat": "%" + vat_filter + "%" if vat_filter else "%",
                "name": "%" + name_filter + "%" if name_filter else "%",
                "street": "%" + street_filter + "%" if street_filter else "%",
                "city": "%" + city_filter + "%" if city_filter else "%",
                "zip": "%" + zip_filter + "%" if zip_filter else "%"
            }).fetchall()

    return render_template("clients/filter.html", client_filter=client_filter)

# Route to add a new client
@app.route("/clients/add", methods=("GET",))
def add_client_view():
    """Display form for adding a new client."""
    return render_template("/clients/add.html")

@app.route("/clients/add", methods=("POST",))
def add_client_db():
    """Insert a new client into the database."""
    vat = request.form.get('vat')
    name = request.form.get('name')
    birthdate = request.form.get('birthdate')
    street = request.form.get('street')
    city = request.form.get('city')
    zip = request.form.get('zip')
    gender = request.form.get('gender')

    with psycopg.connect(conninfo=DATABASE_URL) as conn:
        with conn.cursor(row_factory=namedtuple_row) as cur:
            cur.execute("""
                INSERT INTO client (vat, name, birth_date, street, city, zip, gender)
                VALUES (%(vat)s, %(name)s, %(birthdate)s, %(street)s, %(city)s, %(zip)s, %(gender)s);
            """, {
                "vat": vat, "name": name, "birthdate": birthdate,
                "street": street, "city": city, "zip": zip, "gender": gender
            })
            conn.commit()

    return redirect(url_for("client_index"))

# Main application runner
if __name__ == "__main__":
    app.run(debug=True)
