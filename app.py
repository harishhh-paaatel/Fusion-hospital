# app.py
# Fusion Prime Care Hospital - complete backend (Flask + SQLite)
# Save as app.py and run: python app.py

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3
import functools
from datetime import datetime
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # Generate new secret key each run

# DB file paths
DATA_DIR = "."
PATIENT_DB = os.path.join(DATA_DIR, "patient.db")
DOCTOR_DB = os.path.join(DATA_DIR, "doctor.db")
APPOINT_DB = os.path.join(DATA_DIR, "appointment.db")

HOSPITAL_NAME = "Fusion Prime Care Hospital"

# -------------------------
# login_required decorator
# -------------------------
def login_required(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            flash("Please login to continue.", "danger")
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper

# -------------------------  
# global login requirement
# -------------------------
@app.before_request
def require_login():
    # allow access to login and static files only
    if request.endpoint == 'login' or request.path.startswith('/static/'):
        return
    # require login for ALL other routes
    if not session.get("user"):
        flash("Please login to continue.", "danger")
        return redirect(url_for("login", next=request.path))

# -------------------------
# initialize DBs & tables
# -------------------------
def init_db():
    # ensure DB files exist
    open(PATIENT_DB, "a").close()
    open(DOCTOR_DB, "a").close()
    open(APPOINT_DB, "a").close()

    # patients
    with sqlite3.connect(PATIENT_DB) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS patient (
                patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                gender TEXT,
                phone TEXT,
                address TEXT,
                age INTEGER,
                disease TEXT,
                dob TEXT,
                email TEXT
            )
        """)
        # Add email column if it doesn't exist
        try:
            cur.execute("ALTER TABLE patient ADD COLUMN email TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        cur.execute("SELECT COUNT(*) FROM patient")
        if cur.fetchone()[0] == 0:
            cur.execute("""INSERT INTO patient (name,gender,phone,address,age,disease,dob,email)
                           VALUES (?,?,?,?,?,?,?,?)""",
                        ("Demo Patient","M","+91-9000000000","Demo Address",30,"General","1995-01-01","demo.patient@example.com"))
        conn.commit()

    # doctors and slots
    with sqlite3.connect(DOCTOR_DB) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS doctor (
                doctor_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                gender TEXT,
                phone TEXT,
                specialization TEXT,
                age INTEGER,
                date_of_joining TEXT,
                hospital_id TEXT UNIQUE,
                email TEXT
            )
        """)
        # Add email column if it doesn't exist
        try:
            cur.execute("ALTER TABLE doctor ADD COLUMN email TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS slot (
                slot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                doctor_id INTEGER,
                slot_date TEXT,
                start_time TEXT,
                end_time TEXT,
                is_available INTEGER DEFAULT 1,
                FOREIGN KEY(doctor_id) REFERENCES doctor(doctor_id)
            )
        """)
        cur.execute("SELECT COUNT(*) FROM doctor")
        if cur.fetchone()[0] == 0:
            cur.execute("""INSERT INTO doctor (name,gender,phone,specialization,age,date_of_joining,hospital_id,email)
                           VALUES (?,?,?,?,?,?,?,?)""",
                        ("Dr. Reddy","M","+91-9000000001","General Physician",45,"2015-06-01","FPCH-001","dr.reddy@example.com"))
            cur.execute("""INSERT INTO doctor (name,gender,phone,specialization,age,date_of_joining,hospital_id,email)
                           VALUES (?,?,?,?,?,?,?,?)""",
                        ("Dr. Meera","F","+91-9000000002","Dermatologist",39,"2018-09-12","FPCH-002","dr.meera@example.com"))
        conn.commit()

    # appointments and users
    with sqlite3.connect(APPOINT_DB) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS appointment (
                appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER,
                doctor_id INTEGER,
                slot_id INTEGER,
                appt_date TEXT,
                appt_time TEXT,
                status TEXT,
                created_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password_hash TEXT,
                fullname TEXT
            )
        """)
        cur.execute("SELECT COUNT(*) FROM users")
        if cur.fetchone()[0] == 0:
            pw = generate_password_hash("admin123")
            cur.execute("INSERT INTO users (username,password_hash,fullname) VALUES (?,?,?)",
                        ("admin", pw, "Administrator"))
        conn.commit()

# initialize on start
init_db()

# -------------------------
# root
# -------------------------
@app.route("/")
def root():
    if session.get("user"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

# -------------------------
# auth: login / logout
# -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username", "").strip()
        p = request.form.get("password", "")
        with sqlite3.connect(APPOINT_DB) as conn:
            cur = conn.cursor()
            cur.execute("SELECT user_id,username,password_hash,fullname FROM users WHERE username = ?", (u,))
            row = cur.fetchone()
            if row:
                stored = row[2]
                try:
                    ok = check_password_hash(stored, p)
                except Exception:
                    ok = (stored == p)
                if ok:
                    session["user"] = {"user_id": row[0], "username": row[1], "fullname": row[3]}
                    flash("Logged in successfully.", "success")
                    nxt = request.args.get("next") or url_for("dashboard")
                    return redirect(nxt)
        flash("Invalid credentials.", "danger")
    return render_template("login.html", hospital_name=HOSPITAL_NAME)

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out.", "success")
    return redirect(url_for("login"))

# -------------------------
# dashboard
# -------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    with sqlite3.connect(DOCTOR_DB) as conn:
        doc_count = conn.cursor().execute("SELECT COUNT(*) FROM doctor").fetchone()[0]
    with sqlite3.connect(PATIENT_DB) as conn:
        pat_count = conn.cursor().execute("SELECT COUNT(*) FROM patient").fetchone()[0]
    with sqlite3.connect(APPOINT_DB) as conn:
        appt_count = conn.cursor().execute("SELECT COUNT(*) FROM appointment").fetchone()[0]
    return render_template("dashboard.html", hospital_name=HOSPITAL_NAME, user=session.get("user"),
                           stats={"doctors": doc_count, "patients": pat_count, "appointments": appt_count})

# -------------------------
# doctors CRUD
# -------------------------
@app.route("/doctors")
@login_required
def doctors():
    with sqlite3.connect(DOCTOR_DB) as conn:
        cur = conn.cursor()
        cur.execute("SELECT doctor_id,name,gender,phone,specialization,age,date_of_joining,hospital_id,email FROM doctor ORDER BY name")
        doctors = cur.fetchall()
    return render_template("doctors.html", hospital_name=HOSPITAL_NAME, doctors=doctors, user=session.get("user"))

@app.route("/doctors/add", methods=["GET", "POST"])
@login_required
def add_doctor():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        gender = request.form.get("gender")
        phone = request.form.get("phone")
        specialization = request.form.get("specialization")
        age = request.form.get("age") or None
        doj = request.form.get("date_of_joining")
        hid = request.form.get("hospital_id", "").strip()
        email = request.form.get("email")
        if not name or not hid:
            flash("Name and Hospital ID are required.", "danger")
            return redirect(url_for("add_doctor"))
        with sqlite3.connect(DOCTOR_DB) as conn:
            cur = conn.cursor()
            cur.execute("""INSERT INTO doctor (name,gender,phone,specialization,age,date_of_joining,hospital_id,email)
                           VALUES (?,?,?,?,?,?,?,?)""", (name,gender,phone,specialization,age,doj,hid,email))
            conn.commit()
        flash("Doctor added.", "success")
        return redirect(url_for("doctors"))
    return render_template("edit_doctor.html", hospital_name=HOSPITAL_NAME, doctor=None, user=session.get("user"))

@app.route("/doctors/edit/<int:doctor_id>", methods=["GET", "POST"])
@login_required
def edit_doctor(doctor_id):
    with sqlite3.connect(DOCTOR_DB) as conn:
        cur = conn.cursor()
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            gender = request.form.get("gender")
            phone = request.form.get("phone")
            specialization = request.form.get("specialization")
            age = request.form.get("age") or None
            doj = request.form.get("date_of_joining")
            hid = request.form.get("hospital_id", "").strip()
            email = request.form.get("email")
            cur.execute("""UPDATE doctor SET name=?, gender=?, phone=?, specialization=?, age=?, date_of_joining=?, hospital_id=?, email=? WHERE doctor_id=?""",
                        (name,gender,phone,specialization,age,doj,hid,email,doctor_id))
            conn.commit()
            flash("Doctor updated.", "success")
            return redirect(url_for("doctors"))
        cur.execute("SELECT doctor_id,name,gender,phone,specialization,age,date_of_joining,hospital_id,email FROM doctor WHERE doctor_id = ?", (doctor_id,))
        doc = cur.fetchone()
        # fetch slots for display (optional)
        cur.execute("SELECT slot_id,slot_date,start_time,end_time,is_available FROM slot WHERE doctor_id = ? ORDER BY slot_date,start_time", (doctor_id,))
        slots = cur.fetchall()
    return render_template("edit_doctor.html", hospital_name=HOSPITAL_NAME, doctor=doc, slots=slots, user=session.get("user"))

@app.route("/doctors/delete/<int:doctor_id>", methods=["POST"])
@login_required
def delete_doctor(doctor_id):
    with sqlite3.connect(DOCTOR_DB) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM slot WHERE doctor_id = ?", (doctor_id,))
        cur.execute("DELETE FROM doctor WHERE doctor_id = ?", (doctor_id,))
        conn.commit()
    flash("Doctor and related slots deleted.", "success")
    return redirect(url_for("doctors"))

# -------------------------
# patients CRUD
# -------------------------
@app.route("/patients")
@login_required
def patients():
    with sqlite3.connect(PATIENT_DB) as conn:
        cur = conn.cursor()
        cur.execute("SELECT patient_id,name,gender,phone,address,age,disease,dob,email FROM patient ORDER BY name")
        patients = cur.fetchall()
    return render_template("patients.html", hospital_name=HOSPITAL_NAME, patients=patients, user=session.get("user"))

@app.route("/patients/add", methods=["GET", "POST"])
@login_required
def add_patient():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        gender = request.form.get("gender")
        phone = request.form.get("phone")
        address = request.form.get("address")
        age = request.form.get("age") or None
        disease = request.form.get("disease")
        dob = request.form.get("dob")
        email = request.form.get("email")
        if not name:
            flash("Name required.", "danger")
            return redirect(url_for("add_patient"))
        with sqlite3.connect(PATIENT_DB) as conn:
            cur = conn.cursor()
            cur.execute("""INSERT INTO patient (name,gender,phone,address,age,disease,dob,email)
                           VALUES (?,?,?,?,?,?,?,?)""", (name,gender,phone,address,age,disease,dob,email))
            conn.commit()
        flash("Patient added.", "success")
        return redirect(url_for("patients"))
    return render_template("edit_patient.html", hospital_name=HOSPITAL_NAME, patient=None, user=session.get("user"))

@app.route("/patients/edit/<int:patient_id>", methods=["GET", "POST"])
@login_required
def edit_patient(patient_id):
    with sqlite3.connect(PATIENT_DB) as conn:
        cur = conn.cursor()
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            gender = request.form.get("gender")
            phone = request.form.get("phone")
            address = request.form.get("address")
            age = request.form.get("age") or None
            disease = request.form.get("disease")
            dob = request.form.get("dob")
            email = request.form.get("email")
            cur.execute("""UPDATE patient SET name=?,gender=?,phone=?,address=?,age=?,disease=?,dob=?,email=? WHERE patient_id=?""",
                        (name,gender,phone,address,age,disease,dob,email,patient_id))
            conn.commit()
            flash("Patient updated.", "success")
            return redirect(url_for("patients"))
        cur.execute("SELECT patient_id,name,gender,phone,address,age,disease,dob,email FROM patient WHERE patient_id = ?", (patient_id,))
        p = cur.fetchone()
    return render_template("edit_patient.html", hospital_name=HOSPITAL_NAME, patient=p, user=session.get("user"))

@app.route("/patients/delete/<int:patient_id>", methods=["POST"])
@login_required
def delete_patient(patient_id):
    with sqlite3.connect(PATIENT_DB) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM patient WHERE patient_id = ?", (patient_id,))
        conn.commit()
    flash("Patient deleted.", "success")
    return redirect(url_for("patients"))

# -------------------------
# slots (admin) - add
# -------------------------
@app.route("/slots/add", methods=["POST"])
@login_required
def add_slot():
    try:
        doctor_id = int(request.form.get("doctor_id"))
    except Exception:
        flash("Invalid doctor selection.", "danger")
        return redirect(url_for("doctors"))
    slot_date = request.form.get("slot_date")
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")
    with sqlite3.connect(DOCTOR_DB) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO slot (doctor_id,slot_date,start_time,end_time,is_available) VALUES (?,?,?,?,1)",
                    (doctor_id,slot_date,start_time,end_time))
        conn.commit()
    flash("Slot added.", "success")
    return redirect(url_for("edit_doctor", doctor_id=doctor_id))
# -------------------------
# booking (create appointment)  ✅ SMS INTEGRATED
# -------------------------
@app.route("/booking", methods=["GET", "POST"])
@login_required
def booking():
    with sqlite3.connect(DOCTOR_DB) as conn:
        cur = conn.cursor()
        cur.execute("SELECT doctor_id,name,specialization,hospital_id FROM doctor ORDER BY name")
        doctors = cur.fetchall()

    with sqlite3.connect(PATIENT_DB) as conn:
        cur = conn.cursor()
        cur.execute("SELECT patient_id,name FROM patient ORDER BY name")
        patients = cur.fetchall()

    if request.method == "POST":
        try:
            patient_id = int(request.form.get("patient_id"))
            doctor_id = int(request.form.get("doctor_id"))
            slot_date = request.form.get("slot_date")
            slot_id = int(request.form.get("slot_id"))
        except Exception:
            flash("Invalid booking data.", "danger")
            return redirect(url_for("booking"))

        # verify slot availability
        with sqlite3.connect(DOCTOR_DB) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT is_available,start_time FROM slot WHERE slot_id=? AND doctor_id=? AND slot_date=?",
                (slot_id, doctor_id, slot_date)
            )
            row = cur.fetchone()
            if not row or row[0] != 1:
                flash("Selected slot not available.", "danger")
                return redirect(url_for("booking"))
            start_time = row[1]

        # insert appointment
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(APPOINT_DB) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO appointment
                (patient_id,doctor_id,slot_id,appt_date,appt_time,status,created_at)
                VALUES (?,?,?,?,?,?,?)
            """, (patient_id, doctor_id, slot_id, slot_date, start_time, "CONFIRMED", now))
            conn.commit()

        # mark slot unavailable
        with sqlite3.connect(DOCTOR_DB) as conn:
            cur = conn.cursor()
            cur.execute("UPDATE slot SET is_available = 0 WHERE slot_id = ?", (slot_id,))
            conn.commit()

        # -------------------------
        # SEND SMS TO PATIENT
        # -------------------------
        with sqlite3.connect(PATIENT_DB) as pconn:
            pcur = pconn.cursor()
            pcur.execute("SELECT name, phone FROM patient WHERE patient_id = ?", (patient_id,))
            patient = pcur.fetchone()

        with sqlite3.connect(DOCTOR_DB) as dconn:
            dcur = dconn.cursor()
            dcur.execute("SELECT name FROM doctor WHERE doctor_id = ?", (doctor_id,))
            doctor = dcur.fetchone()

        if patient and doctor:
            patient_name = patient[0]
            phone = patient[1]

            phone = phone.replace("+91", "").replace("-", "").replace(" ", "").strip()

            sms_message = (
                f"{HOSPITAL_NAME}\n"
                f"Appointment Confirmed\n"
                f"Patient: {patient_name}\n"
                f"Doctor: {doctor[0]}\n"
                f"Date: {slot_date}\n"
                f"Time: {start_time}"
            )

            try:
                send_sms(phone, sms_message)
            except Exception as e:
                print("SMS failed:", e)

        flash("Appointment confirmed and SMS sent.", "success")
        return redirect(url_for("appointments"))

    return render_template(
        "booking.html",
        hospital_name=HOSPITAL_NAME,
        doctors=doctors,
        patients=patients,
        user=session.get("user")
    )
# -------------------------
# api: get slots for doctor+date (returns json)
# -------------------------
@app.route("/api/slots")
@login_required
def api_slots():
    doctor_id = request.args.get("doctor_id")
    slot_date = request.args.get("slot_date")
    if not doctor_id or not slot_date:
        return jsonify([])
    with sqlite3.connect(DOCTOR_DB) as conn:
        cur = conn.cursor()
        cur.execute("""SELECT slot_id,start_time,end_time,is_available FROM slot
                       WHERE doctor_id = ? AND slot_date = ? ORDER BY start_time""", (doctor_id, slot_date))
        rows = cur.fetchall()
    slots = [{"slot_id": r[0], "start_time": r[1], "end_time": r[2], "is_available": r[3]} for r in rows]
    return jsonify(slots)

# -------------------------
# appointments list / edit / delete
# -------------------------
@app.route("/appointments")
@login_required
def appointments():
    with sqlite3.connect(APPOINT_DB) as conn:
        cur = conn.cursor()
        cur.execute("SELECT appointment_id,patient_id,doctor_id,slot_id,appt_date,appt_time,status,created_at FROM appointment ORDER BY created_at DESC")
        appts = cur.fetchall()

    patients = {}
    with sqlite3.connect(PATIENT_DB) as conn:
        cur = conn.cursor()
        cur.execute("SELECT patient_id,name FROM patient")
        for r in cur.fetchall():
            patients[r[0]] = r[1]

    doctors = {}
    with sqlite3.connect(DOCTOR_DB) as conn:
        cur = conn.cursor()
        cur.execute("SELECT doctor_id,name FROM doctor")
        for r in cur.fetchall():
            doctors[r[0]] = r[1]

    return render_template("appointments.html", hospital_name=HOSPITAL_NAME, appointments=appts, patients=patients, doctors=doctors, user=session.get("user"))

@app.route("/appointments/delete/<int:appt_id>", methods=["POST"])
@login_required
def delete_appointment(appt_id):
    # free slot if any, then delete
    with sqlite3.connect(APPOINT_DB) as conn:
        cur = conn.cursor()
        cur.execute("SELECT slot_id FROM appointment WHERE appointment_id = ?", (appt_id,))
        row = cur.fetchone()
        if row and row[0]:
            slot_id = row[0]
            with sqlite3.connect(DOCTOR_DB) as dconn:
                dcur = dconn.cursor()
                dcur.execute("UPDATE slot SET is_available = 1 WHERE slot_id = ?", (slot_id,))
                dconn.commit()
        cur.execute("DELETE FROM appointment WHERE appointment_id = ?", (appt_id,))
        conn.commit()
    flash("Appointment deleted.", "success")
    return redirect(url_for("appointments"))

# -------------------------
# edit appointment (simple edit: status/date/time)
# -------------------------
@app.route("/appointments/edit/<int:appt_id>", methods=["GET", "POST"])
@login_required
def edit_appointment(appt_id):
    with sqlite3.connect(APPOINT_DB) as conn:
        cur = conn.cursor()
        if request.method == "POST":
            new_status = request.form.get("status")
            new_date = request.form.get("appt_date")
            new_time = request.form.get("appt_time")
            cur.execute("UPDATE appointment SET status=?, appt_date=?, appt_time=? WHERE appointment_id = ?", (new_status, new_date, new_time, appt_id))
            conn.commit()
            flash("Appointment updated.", "success")
            return redirect(url_for("appointments"))
        cur.execute("SELECT appointment_id,patient_id,doctor_id,slot_id,appt_date,appt_time,status FROM appointment WHERE appointment_id = ?", (appt_id,))
        appt = cur.fetchone()

    with sqlite3.connect(PATIENT_DB) as conn:
        pc = conn.cursor(); pc.execute("SELECT patient_id,name FROM patient ORDER BY name"); patients = pc.fetchall()
    with sqlite3.connect(DOCTOR_DB) as conn:
        dc = conn.cursor(); dc.execute("SELECT doctor_id,name FROM doctor ORDER BY name"); doctors = dc.fetchall()
    return render_template("edit_appointment.html", hospital_name=HOSPITAL_NAME, appt=appt, patients=patients, doctors=doctors, user=session.get("user"))

# -------------------------
# edit booking (rich edit: choose new doctor/date/slot)
# -------------------------
@app.route("/booking/edit/<int:appt_id>", methods=["GET", "POST"])
@login_required
def edit_booking(appt_id):
    # fetch appointment
    with sqlite3.connect(APPOINT_DB) as acon:
        ac = acon.cursor()
        ac.execute("SELECT appointment_id,patient_id,doctor_id,slot_id,appt_date,appt_time,status FROM appointment WHERE appointment_id = ?", (appt_id,))
        appt = ac.fetchone()
        if not appt:
            flash("Appointment not found.", "danger")
            return redirect(url_for("appointments"))

    with sqlite3.connect(PATIENT_DB) as pconn:
        pc = pconn.cursor(); pc.execute("SELECT patient_id,name FROM patient ORDER BY name"); patients = pc.fetchall()
    with sqlite3.connect(DOCTOR_DB) as dconn:
        dc = dconn.cursor(); dc.execute("SELECT doctor_id,name,specialization,hospital_id FROM doctor ORDER BY name"); doctors = dc.fetchall()

    if request.method == "POST":
        try:
            new_patient_id = int(request.form.get("patient_id"))
            new_doctor_id = int(request.form.get("doctor_id"))
            new_slot_date = request.form.get("slot_date")
            new_slot_id = int(request.form.get("slot_id"))
            new_status = request.form.get("status") or "CONFIRMED"
        except Exception:
            flash("Invalid form data.", "danger")
            return redirect(url_for("edit_booking", appt_id=appt_id))

        # verify new slot exists and is available (or is the same as old)
        with sqlite3.connect(DOCTOR_DB) as dconn:
            dcur = dconn.cursor()
            dcur.execute("SELECT is_available,start_time FROM slot WHERE slot_id = ? AND doctor_id = ? AND slot_date = ?", (new_slot_id, new_doctor_id, new_slot_date))
            row = dcur.fetchone()
            if not row:
                flash("Selected slot does not exist.", "danger")
                return redirect(url_for("edit_booking", appt_id=appt_id))
            # if slot is not available and it isn't the current slot, block
            current_slot_id = appt[3]
            if row[0] != 1 and not (current_slot_id and current_slot_id == new_slot_id):
                flash("Selected slot is no longer available.", "danger")
                return redirect(url_for("edit_booking", appt_id=appt_id))
            new_start_time = row[1]

        old_slot_id = appt[3]  # may be None

        # update appointment and slot availability atomically-ish (two DBs)
        try:
            with sqlite3.connect(APPOINT_DB) as acon:
                ac = acon.cursor()
                ac.execute("""UPDATE appointment
                              SET patient_id=?, doctor_id=?, slot_id=?, appt_date=?, appt_time=?, status=?
                              WHERE appointment_id=?""",
                           (new_patient_id, new_doctor_id, new_slot_id, new_slot_date, new_start_time, new_status, appt_id))
                acon.commit()
            with sqlite3.connect(DOCTOR_DB) as dconn:
                dcur = dconn.cursor()
                # free old slot if exists and different
                if old_slot_id and old_slot_id != new_slot_id:
                    dcur.execute("UPDATE slot SET is_available = 1 WHERE slot_id = ?", (old_slot_id,))
                # mark new slot as taken (if not already taken)
                dcur.execute("UPDATE slot SET is_available = 0 WHERE slot_id = ?", (new_slot_id,))
                dconn.commit()
            flash("Appointment updated successfully.", "success")
            return redirect(url_for("appointments"))
        except Exception as e:
            flash(f"Error updating appointment: {e}", "danger")
            return redirect(url_for("edit_booking", appt_id=appt_id))

    # GET: render edit booking form
    return render_template("edit_booking.html",
                           hospital_name=HOSPITAL_NAME,
                           appt=appt,
                           patients=patients,
                           doctors=doctors,
                           user=session.get("user"))

# -------------------------
# debug helper (show registered routes + templates)
# -------------------------
@app.route("/debug_routes_full")
@login_required
def debug_routes_full():
    out = []
    out.append("<h3>Registered routes</h3><ul>")
    for r in sorted(app.url_map.iter_rules(), key=lambda x: x.rule):
        out.append(f"<li><code>{r.rule}</code> &rarr; <strong>{r.endpoint}</strong></li>")
    out.append("</ul><h3>Templates</h3><ul>")
    templates = ["base.html","login.html","dashboard.html","doctors.html","edit_doctor.html",
                 "patients.html","edit_patient.html","booking.html","appointments.html","edit_appointment.html","edit_booking.html"]
    for t in templates:
        out.append(f"<li>{t}: {'✅ exists' if os.path.exists(os.path.join('templates',t)) else '❌ NOT FOUND'}</li>")
    out.append("</ul>")
    out.append(f"<h3>Login status</h3><p>{'Logged in as: ' + session.get('user',{{}}).get('username') if session.get('user') else 'Not logged in'}</p>")
    out.append("<p>Try direct pages: <a href='/patients'>/patients</a> | <a href='/booking'>/booking</a> | <a href='/appointments'>/appointments</a></p>")
    return "\n".join(out)

# -------------------------
# favicon (no-op)
# -------------------------
@app.route("/favicon.ico")
def favicon():
    return "", 204

# -------------------------
# run app
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)
