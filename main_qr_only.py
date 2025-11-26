import cv2
import pandas as pd
from datetime import datetime
import os
import sys
import time
import os
print(os.getcwd())

print("📷 QR Code Attendance Scanner with Photo Capture")

class AttendanceScanner:
    def __init__(self, students_csv='students.csv', attendance_file_prefix='attendance'):
        self.students_csv = students_csv
        
        # Generate filename with today's date (e.g. attendance-2025-11-08.csv)
        today_str = datetime.now().strftime("%Y-%m-%d")
        self.attendance_file = f"{attendance_file_prefix}-{today_str}.csv"
        
        self.students_dict = {}
        self.scanned_today = set()
        self.qr_detector = cv2.QRCodeDetector()
        self.photos_dir = 'student_photos'
        
        # Create photos directory
        if not os.path.exists(self.photos_dir):
            os.makedirs(self.photos_dir)
            print(f"✓ Created directory: {self.photos_dir}/")
        
        self.load_students()
        self.init_attendance_file()
    
    def load_students(self):
        try:
            if not os.path.exists(self.students_csv):
                print(f"❌ {self.students_csv} not found!")
                sys.exit(1)
            
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
    
    def init_attendance_file(self):
        """Create or load today's attendance file."""
        try:
            if os.path.exists(self.attendance_file):
                df = pd.read_csv(self.attendance_file)
                print(f"✓ Loaded existing {self.attendance_file}")
                
                today = datetime.now().date()
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date']).dt.date
                    today_records = df[df['Date'] == today]
                    self.scanned_today = set(today_records['Barcode'].astype(str))
                    print(f"  {len(self.scanned_today)} students already scanned today")
            else:
                df = pd.DataFrame(columns=['Student Name', 'Barcode', 'Date', 'Time', 'Photo'])
                df.to_csv(self.attendance_file, index=False)
                print(f"✓ Created {self.attendance_file}")
        except Exception as e:
            print(f"❌ Error with attendance file: {e}")
            sys.exit(1)
    
    def capture_photo_with_countdown(self, cap, student_name, barcode):
        countdown_start = time.time()
        countdown_duration = 3
        captured_frame = None
        
        while time.time() - countdown_start < countdown_duration:
            ret, frame = cap.read()
            if not ret:
                break
            
            elapsed = time.time() - countdown_start
            remaining = countdown_duration - elapsed
            countdown_num = int(remaining) + 1
            
            overlay = frame.copy()
            height, width = frame.shape[:2]
            cv2.rectangle(overlay, (0, 0), (width, height), (0, 0, 0), -1)
            frame = cv2.addWeighted(overlay, 0.3, frame, 0.7, 0)
            
            font = cv2.FONT_HERSHEY_SIMPLEX
            msg1 = "PLEASE STAND BACK"
            msg2 = "Taking your picture..."
            (text_width1, text_height1), _ = cv2.getTextSize(msg1, font, 1.2, 3)
            (text_width2, text_height2), _ = cv2.getTextSize(msg2, font, 0.8, 2)
            x1 = (width - text_width1) // 2
            y1 = height // 2 - 100
            x2 = (width - text_width2) // 2
            y2 = height // 2 - 40
            
            cv2.putText(frame, msg1, (x1, y1), font, 1.2, (0, 255, 255), 3)
            cv2.putText(frame, msg2, (x2, y2), font, 0.8, (255, 255, 255), 2)
            
            if countdown_num > 0:
                center_x = width // 2
                center_y = height // 2 + 50
                radius = 80
                cv2.circle(frame, (center_x, center_y), radius, (0, 255, 255), 5)
                countdown_text = str(countdown_num)
                (text_width, text_height), _ = cv2.getTextSize(countdown_text, font, 4, 8)
                text_x = center_x - text_width // 2
                text_y = center_y + text_height // 2
                cv2.putText(frame, countdown_text, (text_x, text_y), font, 4, (0, 255, 255), 8)
            
            name_msg = f"Student: {student_name}"
            cv2.putText(frame, name_msg, (20, 40), font, 0.8, (0, 255, 0), 2)
            
            cv2.imshow('QR Code Attendance Scanner', frame)
            cv2.waitKey(100)
        
        ret, captured_frame = cap.read()
        if ret:
            overlay = captured_frame.copy()
            height, width = captured_frame.shape[:2]
            cv2.rectangle(overlay, (0, 0), (width, height), (0, 255, 0), -1)
            captured_frame_display = cv2.addWeighted(overlay, 0.2, captured_frame, 0.8, 0)
            msg = "PICTURE CAPTURED!"
            font = cv2.FONT_HERSHEY_SIMPLEX
            (text_width, text_height), _ = cv2.getTextSize(msg, font, 1.5, 4)
            x = (width - text_width) // 2
            y = height // 2
            cv2.putText(captured_frame_display, msg, (x, y), font, 1.5, (0, 255, 0), 4)
            cv2.putText(captured_frame_display, student_name, (x, y + 60), font, 1.0, (255, 255, 255), 3)
            cv2.imshow('QR Code Attendance Scanner', captured_frame_display)
            cv2.waitKey(1000)
            return True, captured_frame
        return False, None
    
    def save_photo(self, frame, student_name, barcode):
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_name = student_name.replace(' ', '_')
            filename = f"{self.photos_dir}/{barcode}_{safe_name}_{timestamp}.jpg"
            cv2.imwrite(filename, frame)
            return filename
        except Exception as e:
            print(f"⚠ Error saving photo: {e}")
            return None
    
    def save_attendance(self, barcode, student_name, photo_path):
        try:
            if barcode in self.scanned_today:
                return False, "Already scanned today"
            
            now = datetime.now()
            new_record = pd.DataFrame([{
                'Student Name': student_name,
                'Barcode': barcode,
                'Date': now.strftime('%Y-%m-%d'),
                'Time': now.strftime('%H:%M:%S'),
                'Photo': photo_path if photo_path else 'N/A'
            }])
            
            if os.path.exists(self.attendance_file):
                existing_df = pd.read_csv(self.attendance_file)
                updated_df = pd.concat([existing_df, new_record], ignore_index=True)
            else:
                updated_df = new_record
            
            updated_df.to_csv(self.attendance_file, index=False)
            self.scanned_today.add(barcode)
            
            return True, "Attendance recorded with photo"
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
        print("\n" + "="*70)
        print("📷 QR CODE ATTENDANCE SCANNER WITH PHOTO CAPTURE")
        print("="*70)
        print("Instructions:")
        print("  • Show QR code to camera")
        print("  • Stand back when countdown starts (3 seconds)")
        print("  • Photo captured automatically")
        print("  • Press 'q' to quit | 'r' to reset today's list")
        print("="*70 + "\n")
        
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Cannot access webcam!")
            return
        
        print(f"✓ Webcam opened - Saving to {self.attendance_file}")
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        last_message = ""
        message_color = (255, 255, 255)
        processing = False
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if not processing:
                qr_codes = self.decode_qr_opencv(frame)
                for qr_info in qr_codes:
                    qr_data = qr_info['data']
                    (x, y, w, h) = qr_info['rect']
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    
                    if qr_data in self.students_dict:
                        student_name = self.students_dict[qr_data]
                        if qr_data in self.scanned_today:
                            last_message = f"⚠ {student_name} - Already scanned today"
                            message_color = (0, 165, 255)
                            text_y = y - 10 if y - 10 > 10 else y + h + 20
                            cv2.putText(frame, "ALREADY SCANNED", (x, text_y),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
                        else:
                            processing = True
                            print(f"\n✓ QR CODE DETECTED: {student_name}")
                            photo_captured, captured_frame = self.capture_photo_with_countdown(cap, student_name, qr_data)
                            if photo_captured:
                                photo_path = self.save_photo(captured_frame, student_name, qr_data)
                                success, message = self.save_attendance(qr_data, student_name, photo_path)
                                if success:
                                    last_message = f"✓ {student_name} - {message}"
                                    message_color = (0, 255, 0)
                                    print(f"✓ Attendance: {student_name} ({qr_data})")
                                    print(f"✓ Photo: {photo_path}")
                                else:
                                    last_message = f"⚠ {student_name} - {message}"
                                    message_color = (0, 165, 255)
                            else:
                                last_message = "⚠ Photo capture failed"
                                message_color = (0, 0, 255)
                            processing = False
                    else:
                        last_message = f"❌ Unknown: {qr_data}"
                        message_color = (0, 0, 255)
                        cv2.putText(frame, "UNKNOWN", (x, y - 10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            cv2.putText(frame, "Press 'q' to quit | 'r' to reset", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f"Scanned today: {len(self.scanned_today)}", (10, 60),
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
                last_message = "✓ Today's list reset"
                message_color = (0, 255, 0)
                print("🔄 Reset")
        
        cap.release()
        cv2.destroyAllWindows()
        print(f"\n✓ Total scanned: {len(self.scanned_today)}")
        print(f"✓ Data saved to: {self.attendance_file}")
        print(f"✓ Photos: {self.photos_dir}/")

def main():
    print("\n🔧 Initializing Scanner...")
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
        print("❌ Install: pip install pandas")
        sys.exit(1)
    scanner = AttendanceScanner()
    scanner.run()

if __name__ == "__main__":
    main()
