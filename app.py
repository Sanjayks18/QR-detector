from flask import Flask, render_template, request, jsonify
import pandas as pd
import datetime
import os
import base64

app = Flask(__name__)

scanned_today = set()

def get_today_attendance_file():
    """Generate filename for today's attendance file"""
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    return f"attendance-{today_str}.csv"

def init_attendance_file():
    """Initialize today's attendance file and load scanned barcodes"""
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
            # Create today's attendance file if it doesn't exist
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

    # Check if already scanned today using today's specific file
    if searched_barcode in scanned_today:
        return jsonify({"success": False, "message": f"{student_name} already marked today!"})

    new_record = {
        "Student Name": student_name,
        "Barcode": searched_barcode,
        "Date": date_str,
        "Time": time_str
    }
    
    try:
        # Always work with today's specific attendance file
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

if __name__ == "__main__":
    init_attendance_file()
    app.run(debug=True)
