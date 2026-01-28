from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import datetime

# --- Initialization ---
app = Flask(__name__)
CORS(app)

# --- Database Configuration ---
db_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'Manohar@15',
    'database': 'manohar'
}

# --- Helper Function to Get DB Connection ---
def get_db_connection():
    return mysql.connector.connect(**db_config)

# --- Routes ---
@app.route("/")
def index():
    return "<h1>Attendance System Backend with MySQL is Running!</h1>"

@app.route("/register", methods=['POST'])
def register_student():
    data = request.get_json()
    required_fields = ['student_id', 'student_name', 'email', 'enrollment_date']

    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required data"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            INSERT INTO students (
                student_id, name, email, date_of_birth, phone_number,
                address, city, enrollment_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            data['student_id'],
            data['student_name'],
            data['email'],
            data.get('date_of_birth') or None,
            data.get('phone_number') or None,
            data.get('address') or None,
            data.get('city', 'Rajkot'),
            data['enrollment_date']
        )

        cursor.execute(sql, values)
        conn.commit()

        return jsonify({"message": "Student registered successfully!"}), 201

    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err.msg}"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

@app.route("/attendance", methods=['GET'])
def get_attendance_dashboard():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        today_str = str(datetime.date.today())

        sql = """
            SELECT s.student_id as id, s.name, a.status
            FROM students s
            LEFT JOIN attendance a ON s.student_id = a.student_id AND a.attendance_date = %s
            ORDER BY s.name
        """
        cursor.execute(sql, (today_str,))
        results = cursor.fetchall()

        for row in results:
            if row['status'] is None:
                row['status'] = 'Not Marked'

        return jsonify(results), 200

    except mysql.connector.Error as err:
        return jsonify({"error": "Could not fetch attendance data"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

@app.route("/mark_attendance", methods=['POST'])
def mark_attendance():
    data = request.get_json()
    if not data or 'student_id' not in data:
        return jsonify({"error": "student_id is required"}), 400

    student_id = data['student_id']
    today_str = str(datetime.date.today())

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM students WHERE student_id = %s", (student_id,))
        if cursor.fetchone() is None:
            return jsonify({"error": "Student ID not found."}), 404

        sql = """
            INSERT INTO attendance (student_id, attendance_date, status)
            VALUES (%s, %s, 'Present')
            ON DUPLICATE KEY UPDATE status = 'Present'
        """
        cursor.execute(sql, (student_id, today_str))
        conn.commit()

        return jsonify({"message": f"Attendance marked for {student_id}"}), 200

    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {err.msg}"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

# --- Main Execution ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)