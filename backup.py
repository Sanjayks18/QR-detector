import cv2
import pandas as pd
from datetime import datetime
import os
import sys

# EXPLICITLY DISABLE PYZBAR - Use OpenCV QR detector only
USE_PYZBAR = False
print("📷 Using OpenCV QR Code Detector (No pyzbar/ZBar required)")
print("   Note: Only QR codes will be detected")

class AttendanceScanner:
    def __init__(self, students_csv='students.csv', attendance_file='attendance.xlsx'):
        self.students_csv = students_csv
        self.attendance_file = attendance_file
        self.students_dict = {}
        self.scanned_today = set()
        self.qr_detector = cv2.QRCodeDetector()
        
        self.load_students()
        self.init_attendance_file()
    
    def load_students(self):
        try:
            if not os.path.exists(self.students_csv):
                print(f"Creating sample {self.students_csv}...")
                self.create_sample_csv()
            
            df = pd.read_csv(self.students_csv)
            
            if 'Barcode' not in df.columns or 'Name' not in df.columns:
                raise ValueError("CSV must contain 'Barcode' and 'Name' columns")
            
            for _, row in df.iterrows():
                barcode = str(row['Barcode']).strip()
                name = str(row['Name']).strip()
                self.students_dict[barcode] = name
            
            print(f"✓ Loaded {len(self.students_dict)} students")
        except Exception as e:
            print(f"❌ Error loading students: {e}")
            sys.exit(1)
    
    def create_sample_csv(self):
        sample_data = {
            'Barcode': ['STU001', 'STU002', 'STU003', '123456789', '987654321'],
            'Name': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Williams', 'Charlie Brown']
        }
        df = pd.DataFrame(sample_data)
        df.to_csv(self.students_csv, index=False)
        print(f"✓ Created {self.students_csv}")
    
    def init_attendance_file(self):
        try:
            if os.path.exists(self.attendance_file):
                df = pd.read_excel(self.attendance_file)
                print(f"✓ Loaded existing {self.attendance_file}")
                
                today = datetime.now().date()
                today_records = df[pd.to_datetime(df['Date']).dt.date == today]
                self.scanned_today = set(today_records['Barcode'].astype(str))
                print(f"  {len(self.scanned_today)} students already scanned today")
            else:
                df = pd.DataFrame(columns=['Student Name', 'Barcode', 'Date', 'Time'])
                df.to_excel(self.attendance_file, index=False)
                print(f"✓ Created {self.attendance_file}")
        except Exception as e:
            print(f"❌ Error with attendance file: {e}")
            sys.exit(1)
    
    def save_attendance(self, barcode, student_name):
        try:
            if barcode in self.scanned_today:
                return False, "Already scanned today"
            
            now = datetime.now()
            new_record = pd.DataFrame([{
                'Student Name': student_name,
                'Barcode': barcode,
                'Date': now.strftime('%Y-%m-%d'),
                'Time': now.strftime('%H:%M:%S')
            }])
            
            if os.path.exists(self.attendance_file):
                existing_df = pd.read_excel(self.attendance_file)
                updated_df = pd.concat([existing_df, new_record], ignore_index=True)
            else:
                updated_df = new_record
            
            updated_df.to_excel(self.attendance_file, index=False)
            self.scanned_today.add(barcode)
            
            return True, "Attendance recorded"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def decode_qr_opencv(self, frame):
        results = []
        data, bbox, _ = self.qr_detector.detectAndDecode(frame)
        
        if data and bbox is not None:
            bbox = bbox.astype(int)
            x_min = int(bbox[:, 0].min())
            y_min = int(bbox[:, 1].min())
            x_max = int(bbox[:, 0].max())
            y_max = int(bbox[:, 1].max())
            
            results.append({
                'data': data,
                'type': 'QRCODE',
                'rect': (x_min, y_min, x_max - x_min, y_max - y_min)
            })
        
        return results
    
    def run(self):
        print("\n" + "="*60)
        print("📷 QR CODE ATTENDANCE SCANNER")
        print("="*60)
        print("Instructions:")
        print("  • Show QR code to the camera")
        print("  • Press 'q' to quit")
        print("  • Press 'r' to reset today's list")
        print("="*60 + "\n")
        
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Cannot access webcam!")
            print("Try: Settings → Privacy → Camera → Enable")
            return
        
        print("✓ Webcam opened")
        print("Scanning for QR codes...\n")
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        last_message = ""
        message_color = (255, 255, 255)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            qr_codes = self.decode_qr_opencv(frame)
            
            for qr_info in qr_codes:
                qr_data = qr_info['data']
                (x, y, w, h) = qr_info['rect']
                
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                if qr_data in self.students_dict:
                    student_name = self.students_dict[qr_data]
                    
                    text_y = y - 10 if y - 10 > 10 else y + h + 20
                    cv2.putText(frame, student_name, (x, text_y),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
                    success, message = self.save_attendance(qr_data, student_name)
                    
                    if success:
                        last_message = f"✓ {student_name} - {message}"
                        message_color = (0, 255, 0)
                        print(f"✓ Recorded: {student_name} ({qr_data})")
                    else:
                        last_message = f"⚠ {student_name} - {message}"
                        message_color = (0, 165, 255)
                else:
                    last_message = f"❌ Unknown: {qr_data}"
                    message_color = (0, 0, 255)
                    cv2.putText(frame, "UNKNOWN", (x, y - 10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            cv2.putText(frame, "Press 'q' to quit | 'r' to reset", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            cv2.putText(frame, f"Scanned: {len(self.scanned_today)}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            if last_message:
                cv2.putText(frame, last_message, (10, frame.shape[0] - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, message_color, 2)
            
            cv2.imshow('QR Code Attendance Scanner', frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                print("\n👋 Closing...")
                break
            elif key == ord('r'):
                self.scanned_today.clear()
                last_message = "✓ Reset complete"
                message_color = (0, 255, 0)
                print("🔄 Reset today's list")
        
        cap.release()
        cv2.destroyAllWindows()
        print(f"✓ Total scanned: {len(self.scanned_today)}")
        print(f"✓ Saved to: {self.attendance_file}")

def main():
    print("\n🔧 Initializing QR Code Scanner...")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)
    
    try:
        import cv2
        print(f"✓ OpenCV {cv2.__version__}")
    except ImportError:
        print("❌ Install: pip install opencv-python")
        sys.exit(1)
    
    try:
        import pandas
        print(f"✓ Pandas {pandas.__version__}")
    except ImportError:
        print("❌ Install: pip install pandas openpyxl")
        sys.exit(1)
    
    scanner = AttendanceScanner()
    scanner.run()

if __name__ == "__main__":
    main()
