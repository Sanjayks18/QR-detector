"""
Attendance Viewer - View attendance records with photos
"""

import pandas as pd
import cv2
import os
import sys

def view_attendance():
    """View attendance records with photos"""
    
    attendance_file = 'attendance.csv'
    
    if not os.path.exists(attendance_file):
        print(f"❌ {attendance_file} not found!")
        return
    
    # Read attendance data
    df = pd.read_csv(attendance_file)
    
    print("\n" + "="*80)
    print("  ATTENDANCE RECORDS")
    print("="*80)
    
    if len(df) == 0:
        print("No attendance records found.")
        return
    
    # Display summary
    print(f"\nTotal Records: {len(df)}")
    print(f"Unique Students: {df['Student Name'].nunique()}")
    
    # Group by date
    df['Date'] = pd.to_datetime(df['Date'])
    dates = df['Date'].dt.date.unique()
    
    print(f"Dates: {', '.join(str(d) for d in sorted(dates))}")
    
    # Display detailed records
    print("\n" + "-"*80)
    print(f"{'#':<4} {'Name':<20} {'Barcode':<15} {'Date':<12} {'Time':<10} {'Photo':<20}")
    print("-"*80)
    
    for idx, row in df.iterrows():
        photo_status = "✓ Yes" if (pd.notna(row['Photo']) and row['Photo'] != 'N/A') else "✗ No"
        print(f"{idx+1:<4} {row['Student Name']:<20} {row['Barcode']:<15} "
              f"{row['Date'].strftime('%Y-%m-%d'):<12} {row['Time']:<10} {photo_status:<20}")
    
    print("-"*80)
    
    # Ask if user wants to view photos
    print("\n" + "="*80)
    print("Photo Viewing Options:")
    print("  1. View all photos")
    print("  2. View specific student's photo")
    print("  3. Exit")
    print("="*80)
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == '1':
        view_all_photos(df)
    elif choice == '2':
        view_student_photo(df)
    elif choice == '3':
        print("👋 Goodbye!")
    else:
        print("Invalid choice!")

def view_all_photos(df):
    """View all photos in sequence"""
    photos_with_data = df[df['Photo'].notna() & (df['Photo'] != 'N/A')]
    
    if len(photos_with_data) == 0:
        print("No photos found in attendance records.")
        return
    
    print(f"\n📸 Viewing {len(photos_with_data)} photos...")
    print("Press any key to view next photo, 'q' to quit")
    
    for idx, row in photos_with_data.iterrows():
        photo_path = row['Photo']
        
        if os.path.exists(photo_path):
            img = cv2.imread(photo_path)
            
            # Add info overlay
            height, width = img.shape[:2]
            
            # Create info bar at top
            cv2.rectangle(img, (0, 0), (width, 80), (0, 0, 0), -1)
            
            # Add text
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(img, f"Name: {row['Student Name']}", (10, 25), 
                       font, 0.7, (255, 255, 255), 2)
            cv2.putText(img, f"Barcode: {row['Barcode']}", (10, 50), 
                       font, 0.6, (200, 200, 200), 1)
            cv2.putText(img, f"Date: {row['Date']}  Time: {row['Time']}", (10, 70), 
                       font, 0.5, (200, 200, 200), 1)
            
            cv2.imshow('Student Photo', img)
            key = cv2.waitKey(0)
            
            if key == ord('q'):
                break
        else:
            print(f"⚠ Photo not found: {photo_path}")
    
    cv2.destroyAllWindows()

def view_student_photo(df):
    """View photo of a specific student"""
    print("\nAvailable students:")
    students = df['Student Name'].unique()
    
    for idx, name in enumerate(students, 1):
        print(f"  {idx}. {name}")
    
    try:
        choice = int(input("\nEnter student number: ").strip())
        if 1 <= choice <= len(students):
            student_name = students[choice - 1]
            
            # Get student's records
            student_records = df[df['Student Name'] == student_name]
            
            print(f"\n{student_name}'s attendance records:")
            for idx, row in student_records.iterrows():
                print(f"  {row['Date']} - {row['Time']}")
            
            # Get the latest photo
            photos = student_records[student_records['Photo'].notna() & (student_records['Photo'] != 'N/A')]
            
            if len(photos) > 0:
                latest = photos.iloc[-1]
                photo_path = latest['Photo']
                
                if os.path.exists(photo_path):
                    img = cv2.imread(photo_path)
                    
                    # Add info
                    height, width = img.shape[:2]
                    cv2.rectangle(img, (0, 0), (width, 60), (0, 0, 0), -1)
                    
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    cv2.putText(img, f"{student_name} - {latest['Date']}", (10, 40), 
                               font, 0.8, (255, 255, 255), 2)
                    
                    cv2.imshow(f'{student_name} Photo', img)
                    print("\nPress any key to close...")
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()
                else:
                    print(f"⚠ Photo not found: {photo_path}")
            else:
                print(f"No photos found for {student_name}")
        else:
            print("Invalid choice!")
    except ValueError:
        print("Invalid input!")

def export_report():
    """Export attendance report to Excel with clickable photo links"""
    attendance_file = 'attendance.csv'
    
    if not os.path.exists(attendance_file):
        print(f"❌ {attendance_file} not found!")
        return
    
    try:
        df = pd.read_csv(attendance_file)
        
        # Convert photo paths to absolute paths
        df['Photo'] = df['Photo'].apply(lambda x: os.path.abspath(x) if pd.notna(x) and x != 'N/A' else 'N/A')
        
        output_file = 'attendance_report.xlsx'
        df.to_excel(output_file, index=False)
        
        print(f"\n✓ Report exported to: {output_file}")
        print("  You can open this in Excel to view all attendance data")
    except Exception as e:
        print(f"❌ Error exporting report: {e}")
        print("  Install openpyxl: pip install openpyxl")

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║          ATTENDANCE VIEWER WITH PHOTO GALLERY                ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    while True:
        print("\n" + "="*60)
        print("Main Menu:")
        print("  1. View attendance records")
        print("  2. Export to Excel")
        print("  3. Exit")
        print("="*60)
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            view_attendance()
        elif choice == '2':
            export_report()
        elif choice == '3':
            print("\n👋 Goodbye!")
            break
        else:
            print("Invalid choice! Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()