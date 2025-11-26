from flask import Flask, render_template, request, jsonify
import pandas as pd
import datetime
import os

app = Flask(__name__)

attendance_file = "attendance.csv"
scanned_today = set()

def init_attendance_file():
    global scanned_today
    try:
        today = datetime.datetime.now().date()
        if os.path.exists(attendance_file):
            df = pd.read_csv(attendance_file)
            print(f"✓ Loaded existing {attendance_file}")

            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date']).dt.date
                today_records = df[df['Date'] == today]
                scanned_today = set(today_records['Barcode'].astype(str))
                print(f"  {len(scanned_today)} students already scanned today")
            else:
                scanned_today = set()
        else:
            df = pd.DataFrame(columns=['Student Name', 'Barcode', 'Date', 'Time'])
            df.to_csv(attendance_file, index=False)
            scanned_today = set()
            print(f"✓ Created new {attendance_file}")
    except Exception as e:
        print(f"❌ Error with attendance file: {e}")
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
    today = datetime.datetime.now().date()
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    if searched_barcode in scanned_today:
        return jsonify({"success": False, "message": f"{student_name} already marked today!"})

    new_record = {
        "Student Name": student_name,
        "Barcode": searched_barcode,
        "Date": date_str,
        "Time": time_str
    }
    try:
        if os.path.exists(attendance_file):
            df = pd.read_csv(attendance_file)
            new_row_df = pd.DataFrame([new_record])
            df = pd.concat([df, new_row_df], ignore_index=True)
        else:
            df = pd.DataFrame([new_record])
        df.to_csv(attendance_file, index=False)
        scanned_today.add(searched_barcode)
        print(f"Attendance marked for {student_name} ({searched_barcode})")
    except Exception as e:
        print(f"Error writing attendance: {e}")
        return jsonify({"success": False, "message": "Error saving attendance."})

    return jsonify({"success": True, "message": f"Attendance marked for {student_name} ({searched_barcode})"})

if __name__ == "__main__":
    init_attendance_file()
    app.run(debug=True)
