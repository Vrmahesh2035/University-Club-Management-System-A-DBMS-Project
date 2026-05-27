from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import mysql.connector
from mysql.connector import Error
from config import Config
from datetime import date

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# ── DB helper ────────────────────────────────────────────────────

def get_db():
    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
        return conn
    except Error as e:
        print(f"DB Error: {e}")
        return None

def query(sql, params=(), fetchone=False, commit=False):
    conn = get_db()
    if not conn:
        return None
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, params)
    if commit:
        conn.commit()
        result = cur.lastrowid
    elif fetchone:
        result = cur.fetchone()
    else:
        result = cur.fetchall()
    cur.close()
    conn.close()
    return result

# ────────────────────────────────────────────────────────────────
# DASHBOARD
# ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    stats = {
        "clubs":    (query("SELECT COUNT(*) AS c FROM clubs",    fetchone=True) or {}).get("c", 0),
        "students": (query("SELECT COUNT(*) AS c FROM students", fetchone=True) or {}).get("c", 0),
        "events":   (query("SELECT COUNT(*) AS c FROM events",   fetchone=True) or {}).get("c", 0),
        "members":  (query("SELECT COUNT(*) AS c FROM memberships WHERE status='active'", fetchone=True) or {}).get("c", 0),
    }
    upcoming = query("""
        SELECT e.event_name, e.event_date, e.event_time, c.club_name, v.venue_name
        FROM events e
        JOIN clubs c  ON e.club_id  = c.club_id
        JOIN venues v ON e.venue_id = v.venue_id
        WHERE e.status='upcoming'
        ORDER BY e.event_date ASC LIMIT 5
    """) or []
    popular_clubs = query("""
        SELECT c.club_name, COUNT(m.membership_id) AS member_count,
               cc.category_name
        FROM clubs c
        JOIN club_categories cc ON c.category_id = cc.category_id
        LEFT JOIN memberships m ON c.club_id = m.club_id AND m.status='active'
        GROUP BY c.club_id
        ORDER BY member_count DESC LIMIT 5
    """) or []
    return render_template("index.html", stats=stats, upcoming=upcoming, popular_clubs=popular_clubs)

# ────────────────────────────────────────────────────────────────
# CLUBS
# ────────────────────────────────────────────────────────────────

@app.route("/clubs")
def clubs():
    rows = query("""
        SELECT c.*, cc.category_name,
               COUNT(DISTINCT m.membership_id) AS member_count,
               COUNT(DISTINCT e.event_id)      AS event_count
        FROM clubs c
        JOIN club_categories cc ON c.category_id = cc.category_id
        LEFT JOIN memberships m ON c.club_id = m.club_id AND m.status='active'
        LEFT JOIN events e      ON c.club_id = e.club_id
        GROUP BY c.club_id
        ORDER BY c.club_name
    """) or []
    return render_template("clubs/list.html", clubs=rows)

@app.route("/clubs/<int:club_id>")
def club_detail(club_id):
    club = query("""
        SELECT c.*, cc.category_name
        FROM clubs c JOIN club_categories cc ON c.category_id=cc.category_id
        WHERE c.club_id=%s
    """, (club_id,), fetchone=True)
    if not club:
        flash("Club not found.", "danger"); return redirect(url_for("clubs"))

    members = query("""
        SELECT s.first_name, s.last_name, s.email, p.position_name,
               m.join_date, m.status, d.dept_name
        FROM memberships m
        JOIN students s    ON m.student_id  = s.student_id
        JOIN positions p   ON m.position_id = p.position_id
        JOIN departments d ON s.dept_id     = d.dept_id
        WHERE m.club_id=%s ORDER BY p.position_id, s.first_name
    """, (club_id,)) or []

    events = query("""
        SELECT e.*, v.venue_name,
               COUNT(er.registration_id) AS registrations
        FROM events e
        JOIN venues v ON e.venue_id=v.venue_id
        LEFT JOIN event_registrations er ON e.event_id=er.event_id
        WHERE e.club_id=%s
        GROUP BY e.event_id ORDER BY e.event_date DESC
    """, (club_id,)) or []

    advisors = query("""
        SELECT a.first_name, a.last_name, a.email, d.dept_name,
               ca.assigned_date
        FROM club_advisor_assignments ca
        JOIN advisors a    ON ca.advisor_id = a.advisor_id
        JOIN departments d ON a.dept_id     = d.dept_id
        WHERE ca.club_id=%s
    """, (club_id,)) or []

    return render_template("clubs/detail.html", club=club, members=members, events=events, advisors=advisors)

@app.route("/clubs/add", methods=["GET", "POST"])
def add_club():
    categories = query("SELECT * FROM club_categories ORDER BY category_name") or []
    if request.method == "POST":
        try:
            query("""
                INSERT INTO clubs (club_name,category_id,description,founded_year,room_number,budget)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (request.form["club_name"], request.form["category_id"],
                  request.form["description"], request.form["founded_year"],
                  request.form["room_number"], request.form["budget"] or 0), commit=True)
            flash("Club added successfully!", "success")
            return redirect(url_for("clubs"))
        except Error as e:
            flash(f"Error: {e}", "danger")
    return render_template("clubs/add.html", categories=categories)

@app.route("/clubs/<int:club_id>/edit", methods=["GET","POST"])
def edit_club(club_id):
    club = query("SELECT * FROM clubs WHERE club_id=%s", (club_id,), fetchone=True)
    if not club:
        flash("Club not found.","danger"); return redirect(url_for("clubs"))
    categories = query("SELECT * FROM club_categories ORDER BY category_name") or []
    if request.method == "POST":
        try:
            query("""
                UPDATE clubs SET club_name=%s, category_id=%s, description=%s,
                founded_year=%s, room_number=%s, budget=%s WHERE club_id=%s
            """, (request.form["club_name"], request.form["category_id"],
                  request.form["description"], request.form["founded_year"],
                  request.form["room_number"], request.form["budget"] or 0, club_id), commit=True)
            flash("Club updated!", "success")
            return redirect(url_for("club_detail", club_id=club_id))
        except Error as e:
            flash(f"Error: {e}", "danger")
    return render_template("clubs/add.html", club=club, categories=categories, edit=True)

@app.route("/clubs/<int:club_id>/delete", methods=["POST"])
def delete_club(club_id):
    query("DELETE FROM clubs WHERE club_id=%s", (club_id,), commit=True)
    flash("Club deleted.", "info")
    return redirect(url_for("clubs"))

# ────────────────────────────────────────────────────────────────
# STUDENTS
# ────────────────────────────────────────────────────────────────

@app.route("/students")
def students():
    rows = query("""
        SELECT s.*, d.dept_name, d.dept_code,
               COUNT(m.membership_id) AS club_count
        FROM students s
        JOIN departments d ON s.dept_id=d.dept_id
        LEFT JOIN memberships m ON s.student_id=m.student_id AND m.status='active'
        GROUP BY s.student_id ORDER BY s.first_name
    """) or []
    return render_template("members/list.html", students=rows)

@app.route("/students/<int:student_id>")
def student_detail(student_id):
    student = query("""
        SELECT s.*, d.dept_name, d.dept_code, d.faculty_dean
        FROM students s JOIN departments d ON s.dept_id=d.dept_id
        WHERE s.student_id=%s
    """, (student_id,), fetchone=True)
    if not student:
        flash("Student not found.","danger"); return redirect(url_for("students"))

    memberships = query("""
        SELECT c.club_name, c.club_id, p.position_name,
               m.join_date, m.status, cc.category_name
        FROM memberships m
        JOIN clubs c            ON m.club_id    = c.club_id
        JOIN positions p        ON m.position_id= p.position_id
        JOIN club_categories cc ON c.category_id= cc.category_id
        WHERE m.student_id=%s ORDER BY m.join_date DESC
    """, (student_id,)) or []

    regs = query("""
        SELECT e.event_name, e.event_date, c.club_name,
               er.attendance_status, v.venue_name
        FROM event_registrations er
        JOIN events e  ON er.event_id  = e.event_id
        JOIN clubs c   ON e.club_id    = c.club_id
        JOIN venues v  ON e.venue_id   = v.venue_id
        WHERE er.student_id=%s ORDER BY e.event_date DESC
    """, (student_id,)) or []

    return render_template("members/detail.html", student=student, memberships=memberships, registrations=regs)

@app.route("/students/add", methods=["GET","POST"])
def add_student():
    depts = query("SELECT * FROM departments ORDER BY dept_name") or []
    if request.method == "POST":
        try:
            query("""
                INSERT INTO students (first_name,last_name,email,phone,dept_id,enrollment_year)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (request.form["first_name"], request.form["last_name"],
                  request.form["email"], request.form["phone"] or None,
                  request.form["dept_id"], request.form["enrollment_year"]), commit=True)
            flash("Student added!", "success")
            return redirect(url_for("students"))
        except Error as e:
            flash(f"Error: {e}", "danger")
    return render_template("members/add.html", departments=depts)

@app.route("/students/<int:student_id>/delete", methods=["POST"])
def delete_student(student_id):
    query("DELETE FROM students WHERE student_id=%s", (student_id,), commit=True)
    flash("Student deleted.", "info")
    return redirect(url_for("students"))

# ────────────────────────────────────────────────────────────────
# MEMBERSHIPS
# ────────────────────────────────────────────────────────────────

@app.route("/memberships/add", methods=["GET","POST"])
def add_membership():
    students_list = query("SELECT student_id, CONCAT(first_name,' ',last_name) AS name FROM students ORDER BY first_name") or []
    clubs_list    = query("SELECT club_id, club_name FROM clubs ORDER BY club_name") or []
    positions_list= query("SELECT position_id, position_name FROM positions ORDER BY position_id") or []
    if request.method == "POST":
        try:
            query("""
                INSERT INTO memberships (student_id,club_id,position_id,join_date,status)
                VALUES (%s,%s,%s,%s,'active')
            """, (request.form["student_id"], request.form["club_id"],
                  request.form["position_id"], request.form["join_date"] or date.today()), commit=True)
            flash("Membership added!", "success")
            return redirect(url_for("clubs"))
        except Error as e:
            flash(f"Error: {e}", "danger")
    return render_template("members/membership.html",
                           students=students_list, clubs=clubs_list, positions=positions_list)

# ────────────────────────────────────────────────────────────────
# EVENTS
# ────────────────────────────────────────────────────────────────

@app.route("/events")
def events():
    rows = query("""
        SELECT e.*, c.club_name, v.venue_name, v.capacity,
               COUNT(er.registration_id) AS registrations
        FROM events e
        JOIN clubs c  ON e.club_id  = c.club_id
        JOIN venues v ON e.venue_id = v.venue_id
        LEFT JOIN event_registrations er ON e.event_id=er.event_id
        GROUP BY e.event_id ORDER BY e.event_date DESC
    """) or []
    return render_template("events/list.html", events=rows)

@app.route("/events/<int:event_id>")
def event_detail(event_id):
    event = query("""
        SELECT e.*, c.club_name, v.venue_name, v.capacity, v.location AS venue_location
        FROM events e
        JOIN clubs c  ON e.club_id  = c.club_id
        JOIN venues v ON e.venue_id = v.venue_id
        WHERE e.event_id=%s
    """, (event_id,), fetchone=True)
    if not event:
        flash("Event not found.","danger"); return redirect(url_for("events"))

    registrations = query("""
        SELECT s.first_name, s.last_name, s.email, d.dept_name,
               er.registration_date, er.attendance_status
        FROM event_registrations er
        JOIN students s    ON er.student_id = s.student_id
        JOIN departments d ON s.dept_id     = d.dept_id
        WHERE er.event_id=%s ORDER BY er.registration_date
    """, (event_id,)) or []

    return render_template("events/detail.html", event=event, registrations=registrations)

@app.route("/events/add", methods=["GET","POST"])
def add_event():
    clubs_list  = query("SELECT club_id, club_name FROM clubs ORDER BY club_name") or []
    venues_list = query("SELECT venue_id, venue_name, capacity FROM venues ORDER BY venue_name") or []
    if request.method == "POST":
        try:
            query("""
                INSERT INTO events
                (event_name,event_date,event_time,club_id,venue_id,description,max_participants,status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,'upcoming')
            """, (request.form["event_name"], request.form["event_date"],
                  request.form["event_time"], request.form["club_id"],
                  request.form["venue_id"], request.form["description"],
                  request.form["max_participants"] or 50), commit=True)
            flash("Event created!", "success")
            return redirect(url_for("events"))
        except Error as e:
            flash(f"Error: {e}", "danger")
    return render_template("events/add.html", clubs=clubs_list, venues=venues_list)

@app.route("/events/<int:event_id>/register", methods=["POST"])
def register_event(event_id):
    student_id = request.form.get("student_id")
    if not student_id:
        flash("Select a student.","warning")
        return redirect(url_for("event_detail", event_id=event_id))
    try:
        query("""
            INSERT INTO event_registrations (event_id, student_id, registration_date)
            VALUES (%s,%s,%s)
        """, (event_id, student_id, date.today()), commit=True)
        flash("Registered successfully!", "success")
    except Error as e:
        flash(f"Error: {e}", "danger")
    return redirect(url_for("event_detail", event_id=event_id))

@app.route("/events/<int:event_id>/delete", methods=["POST"])
def delete_event(event_id):
    query("DELETE FROM events WHERE event_id=%s", (event_id,), commit=True)
    flash("Event deleted.", "info")
    return redirect(url_for("events"))

# ────────────────────────────────────────────────────────────────
# DEPARTMENTS
# ────────────────────────────────────────────────────────────────

@app.route("/departments")
def departments():
    rows = query("""
        SELECT d.*, COUNT(DISTINCT s.student_id) AS student_count
        FROM departments d
        LEFT JOIN students s ON d.dept_id=s.dept_id
        GROUP BY d.dept_id ORDER BY d.dept_name
    """) or []
    return render_template("departments/list.html", departments=rows)

@app.route("/departments/add", methods=["GET","POST"])
def add_department():
    if request.method == "POST":
        try:
            query("""
                INSERT INTO departments (dept_name, dept_code, faculty_dean)
                VALUES (%s,%s,%s)
            """, (request.form["dept_name"], request.form["dept_code"],
                  request.form["faculty_dean"]), commit=True)
            flash("Department added!", "success")
            return redirect(url_for("departments"))
        except Error as e:
            flash(f"Error: {e}", "danger")
    return render_template("departments/add.html")

# ────────────────────────────────────────────────────────────────
# NORMALIZATION INFO PAGE
# ────────────────────────────────────────────────────────────────

@app.route("/normalization")
def normalization():
    return render_template("normalization.html")

# ────────────────────────────────────────────────────────────────
# REPORTS / ANALYTICS
# ────────────────────────────────────────────────────────────────

@app.route("/reports")
def reports():
    selected_student_id = request.args.get("student_id", type=int)

    dept_dist = query("""
        SELECT d.dept_name, COUNT(s.student_id) AS cnt
        FROM departments d LEFT JOIN students s ON d.dept_id=s.dept_id
        GROUP BY d.dept_id ORDER BY cnt DESC
    """) or []

    club_members = query("""
        SELECT c.club_name, COUNT(m.membership_id) AS cnt
        FROM clubs c LEFT JOIN memberships m ON c.club_id=m.club_id AND m.status='active'
        GROUP BY c.club_id ORDER BY cnt DESC
    """) or []

    event_reg = query("""
        SELECT e.event_name, COUNT(er.registration_id) AS cnt
        FROM events e LEFT JOIN event_registrations er ON e.event_id=er.event_id
        GROUP BY e.event_id ORDER BY cnt DESC LIMIT 8
    """) or []

    cat_dist = query("""
        SELECT cc.category_name, COUNT(c.club_id) AS cnt
        FROM club_categories cc LEFT JOIN clubs c ON cc.category_id=c.category_id
        GROUP BY cc.category_id
    """) or []

    students_list = query("""
        SELECT student_id, CONCAT(first_name, ' ', last_name) AS name, email
        FROM students
        ORDER BY first_name, last_name
    """) or []

    selected_student = None
    student_memberships = []
    student_registrations = []
    student_summary = None

    if selected_student_id:
        selected_student = query("""
            SELECT s.*, d.dept_name, d.dept_code, d.faculty_dean
            FROM students s JOIN departments d ON s.dept_id=d.dept_id
            WHERE s.student_id=%s
        """, (selected_student_id,), fetchone=True)

        if selected_student:
            student_memberships = query("""
                SELECT c.club_name, c.club_id, p.position_name,
                       m.join_date, m.status, cc.category_name
                FROM memberships m
                JOIN clubs c            ON m.club_id     = c.club_id
                JOIN positions p        ON m.position_id = p.position_id
                JOIN club_categories cc ON c.category_id = cc.category_id
                WHERE m.student_id=%s ORDER BY m.join_date DESC
            """, (selected_student_id,)) or []

            student_registrations = query("""
                SELECT e.event_name, e.event_date, c.club_name,
                       er.registration_date, er.attendance_status, v.venue_name
                FROM event_registrations er
                JOIN events e ON er.event_id = e.event_id
                JOIN clubs c  ON e.club_id   = c.club_id
                JOIN venues v ON e.venue_id  = v.venue_id
                WHERE er.student_id=%s ORDER BY e.event_date DESC
            """, (selected_student_id,)) or []

            attended_count = sum(1 for r in student_registrations if r["attendance_status"] == "attended")
            student_summary = {
                "clubs": len(student_memberships),
                "active_clubs": sum(1 for m in student_memberships if m["status"] == "active"),
                "events": len(student_registrations),
                "attended": attended_count,
            }
        else:
            flash("Selected student was not found.", "warning")

    return render_template("reports.html",
                           dept_dist=dept_dist, club_members=club_members,
                           event_reg=event_reg, cat_dist=cat_dist,
                           students=students_list,
                           selected_student_id=selected_student_id,
                           selected_student=selected_student,
                           student_memberships=student_memberships,
                           student_registrations=student_registrations,
                           student_summary=student_summary)

if __name__ == "__main__":
    app.run(debug=True)
