import cv2
import datetime
import pytesseract
import mysql.connector

# Initialize MySQL connection
mysql_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="B@lu2003*",
    database="vehicle_data"
)
cursor = mysql_connection.cursor()
# Initialize other variables and constants
plateCascade = cv2.CascadeClassifier("Dataset.xml")
minArea = 500

# Function to store entry information in the database
def store_entry_info(plate_number, entry_time):
    cursor.execute("INSERT INTO vehicle_records (plate_number, entry_time) VALUES (%s, %s)", (plate_number, entry_time))
    mysql_connection.commit()

# Function to update exit time and status in the database
def update_exit_time(plate_number, exit_time):
    cursor.execute("UPDATE vehicle_records SET exit_time = %s, status = 'Out' WHERE plate_number = %s AND exit_time IS NULL", (exit_time, plate_number))
    mysql_connection.commit()

# Function to extract license plate number from the image using OCR
def extract_plate_number(img):
    # Use pytesseract to perform OCR on the preprocessed image
    plate_number = pytesseract.image_to_string(img, lang='eng',
                                               config='--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    return plate_number.strip()  # Strip any leading/trailing whitespace

# Function to detect and recognize license plates
def detect_and_recognize_plates(img):
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    numberPlates = plateCascade.detectMultiScale(imgGray, 1.1, 4)
    detected_plate_numbers = []
    for (x, y, w, h) in numberPlates:
        area = w * h
        if area > minArea:
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
            imgRoi = img[y:y + h, x:x + w]

            # Extract plate number using OCR
            plate_number = extract_plate_number(imgRoi)
            if plate_number is not None and len(plate_number) > 3:
                detected_plate_numbers.append(plate_number)
    return detected_plate_numbers

# Main function for ANPR
def main(video_file_path, cursor):

    cap = cv2.VideoCapture(video_file_path)
    previous_plate_number = None
    frame_count = 0
    while True:
        success, img = cap.read()
        frame_count += 1
        if frame_count == 60:  # Capture a frame after every 10 seconds (assuming 30 fps)
            detected_plate_numbers = detect_and_recognize_plates(img)
            for plate_number in detected_plate_numbers:
                print(plate_number)
                if plate_number != previous_plate_number:
                    entry_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute('SELECT * FROM vehicle_records WHERE plate_number = %s AND exit_time IS NULL', (plate_number,))
                    entry_exists = cursor.fetchone()
                    if entry_exists:
                        update_exit_time(plate_number, entry_time)
                        print(f"Exit time recorded for vehicle with plate number {plate_number}")
                    else:
                        store_entry_info(plate_number, entry_time)
                        print(f"Entry recorded for vehicle with plate number {plate_number}")
                    previous_plate_number = plate_number
            frame_count = 0
        if img is not None:
            cv2.imshow("Output Screen", img)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            elif cv2.waitKey(1) & 0xFF == 27:  # Press Esc key to exit
                break
        else:
            print("Nothing to do")
            break
    cursor.close()
    mysql_connection.close()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # This part will be called when you run anpr.py directly
    # You can test your ANPR functionality here
    # main('path_to_your_video_file')
    pass  # Placeholder to avoid running ANPR functionality when importing this script
