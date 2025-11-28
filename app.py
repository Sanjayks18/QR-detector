from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
import pandas as pd
import datetime
import os
import base64
import qrcode
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'your-secret-key-2025-change-this-in-production'  # Required for sessions

scanned_today = set()
ADMIN_PASSWORD = "admin123"  # Change this password securely

def get_today_attendance_file():
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    return f"attendance-{today_str}.csv"

def init_attendance_file():
    global scanned_today
    try:
        today_file = get_today_attendance_file()
        today = datetime.datetime.now().date()
        
        if os.path.exists(today_file):
            df = pd.read_csv(today_file)
            print(f"✓ Loaded today's attendance file: {today_file}")
            
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date']).dt.date
                today_records = df[df['Date'] == today]
                scanned_today = set(today_records['Barcode'].astype(str))
                print(f"  {len(scanned_today)} students already scanned today")
            else:
                scanned_today = set()
        else:
            df = pd.DataFrame(columns=['Student Name', 'Barcode', 'Date', 'Time'])
            df.to_csv(today_file, index=False)
            scanned_today = set()
            print(f"✓ Created today's attendance file: {today_file}")
    except Exception as e:
        print(f"❌ Error initializing attendance file: {e}")
        scanned_today = set()

def find_student(barcode):
    try:
        reader = pd.read_csv("students.csv", dtype=str)
        searched_barcode = str(barcode).strip()
        matched_rows = reader[reader['Barcode'].str.strip() == searched_barcode]
        if not matched_rows.empty:
            return matched_rows.iloc[0]['Student Name']
    except Exception as e:
        print(f"Error reading students.csv: {e}")
    return None

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            return render_template("login.html", error="❌ Wrong Password!")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("login"))

@app.route("/admin")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    return redirect(url_for("admin_dashboard_day", date=today_str))

@app.route("/admin/day")
def admin_dashboard_day():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    # Get date from query param (?date=YYYY-MM-DD), default to today
    date_str = request.args.get('date')
    if not date_str:
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    # Load attendance for selected date (works for ANY date)
    filename = f"attendance-{date_str}.csv"
    if os.path.exists(filename):
        df = pd.read_csv(filename)
        attendance_count = len(df)
    else:
        df = pd.DataFrame(columns=['Student Name', 'Barcode', 'Date', 'Time'])
        attendance_count = 0

    attendance_records = df.to_dict(orient='records')

    # Load students database for QR gen
    try:
        students_df = pd.read_csv("students.csv")
        total_students = len(students_df)
    except:
        students_df = pd.DataFrame(columns=['Student Name', 'Barcode'])
        total_students = 0

    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    return render_template("admin.html", 
                          records=attendance_records, 
                          students_df=students_df,
                          selected_date=date_str, 
                          current_date=current_date,
                          attendance_count=attendance_count,
                          total_students=total_students)

@app.route("/students")
def students_page():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))
    try:
        students_df = pd.read_csv("students.csv")
        return render_template("students.html", students_df=students_df)
    except Exception as e:
        print(f"Error loading students: {e}")
        return render_template("students.html", students_df=pd.DataFrame(columns=['Student Name', 'Barcode']))

@app.route("/download")
def download_csv():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))
    date_str = request.args.get('date', datetime.datetime.now().strftime("%Y-%m-%d"))
    filename = f"attendance-{date_str}.csv"
    if os.path.exists(filename):
        return send_file(filename, as_attachment=True)
    return "File not found.", 404

@app.route("/reset", methods=["POST"])
def reset_attendance():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))
    global scanned_today
    today_file = get_today_attendance_file()
    if os.path.exists(today_file):
        os.remove(today_file)
        scanned_today.clear()
    return redirect(url_for("admin_dashboard"))

@app.route("/scan", methods=["POST"])
def scan():
    global scanned_today

    data = request.get_json()
    barcode = data.get("barcode")
    print(f"Received barcode: {barcode}")

    student_name = find_student(barcode)
    if not student_name:
        return jsonify({"success": False, "message": "Student not found."})

    searched_barcode = str(barcode).strip()
    today_file = get_today_attendance_file()
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    # FIXED: Always check CSV file for duplicates (works even after restart)
    if os.path.exists(today_file):
        df = pd.read_csv(today_file)
        existing_barcodes = df['Barcode'].astype(str).str.strip().values
        if searched_barcode in existing_barcodes:
            return jsonify({"success": False, "message": f"{student_name} already marked today!"})

    new_record = {
        "Student Name": student_name,
        "Barcode": searched_barcode,
        "Date": date_str,
        "Time": time_str
    }
    
    try:
        if os.path.exists(today_file):
            df = pd.read_csv(today_file)
            new_row_df = pd.DataFrame([new_record])
            df = pd.concat([df, new_row_df], ignore_index=True)
        else:
            df = pd.DataFrame([new_record])
        
        df.to_csv(today_file, index=False)
        scanned_today.add(searched_barcode)
        print(f"✓ Attendance marked for {student_name} ({searched_barcode}) in {today_file}")
        
    except Exception as e:
        print(f"Error writing attendance: {e}")
        return jsonify({"success": False, "message": "Error saving attendance."})

    return jsonify({
        "success": True,
        "message": f"Attendance marked for {student_name} ({searched_barcode})",
        "studentName": student_name,
        "barcode": searched_barcode
    })

@app.route('/save_attendance_photo', methods=['POST'])
def save_attendance_photo():
    data = request.get_json()
    student_name = data.get('studentName')
    barcode = data.get('barcode')
    photo_data_url = data.get('photoData')

    if not(photo_data_url and student_name and barcode):
        return jsonify({"success": False, "message": "Incomplete data"})

    try:
        header, encoded = photo_data_url.split(",", 1)
        photo_bytes = base64.b64decode(encoded)

        now = datetime.datetime.now()
        directory = "photos"
        os.makedirs(directory, exist_ok=True)
        filename = f"{directory}/{barcode}_{now.strftime('%Y%m%d_%H%M%S')}.png"
        with open(filename, "wb") as f:
            f.write(photo_bytes)

        print(f"✓ Saved photo for {student_name} at {filename}")
        return jsonify({"success": True, "message": "Photo saved successfully."})
    except Exception as e:
        print(f"Error saving photo: {e}")
        return jsonify({"success": False, "message": "Error saving photo."})

@app.route('/generate_qr/<barcode>')
def generate_qr(barcode):
    if not session.get('admin_logged_in'):
        return 'Unauthorized', 401
    
    try:
        reader = pd.read_csv("students.csv", dtype=str)
        searched_barcode = str(barcode).strip()
        matched_rows = reader[reader['Barcode'].str.strip() == searched_barcode]
        if matched_rows.empty:
            return 'Student not found', 404
        student_name = matched_rows.iloc[0]['Student Name']
    except Exception as e:
        return 'Student data error', 500
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(barcode)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img_bytes = BytesIO()
    img.save(img_bytes, 'PNG')
    img_bytes.seek(0)

    filename = f"{barcode}_{student_name.replace(' ', '_')}_QR.png"
    return send_file(img_bytes, mimetype='image/png', as_attachment=True, download_name=filename)

if __name__ == "__main__":
    init_attendance_file()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
    
