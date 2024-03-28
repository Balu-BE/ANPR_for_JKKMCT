from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import subprocess
import os
from datetime import datetime
import mysql.connector
from anpr import main as process_video  # Import the ANPR function

app = Flask(__name__, template_folder='templates')

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize MySQL connection
mysql_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="B@lu2003*",
    database="vehicle_data"
)
cursor = mysql_connection.cursor(dictionary=True)

def generate_unique_filename(filename):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_string = os.urandom(8).hex()  # Generate a random string
    secure_name = secure_filename(filename)  # Secure the filename
    unique_name = f"{timestamp}_{random_string}_{secure_name}"
    return unique_name
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/runcode', methods=['POST'])
def runcode():
    data = request.get_json()
    script_name = data['script']
    try:
        subprocess.run(['python', script_name], check=True)
        return jsonify({'message': f'Successfully executed {script_name}.'}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({'message': f'Error executing {script_name}: {e}'}), 500
    

    
@app.route('/videoupload')
def redirect_to_videoupload():
    return render_template('videoupload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part', 'success': False}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file', 'success': False}), 400
    if file:
        filename = generate_unique_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        uploaded_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        # Call the ANPR script with the uploaded file path
        process_video(uploaded_file_path, cursor)
        return jsonify({'file_path': uploaded_file_path, 'success': True}), 200
    else:
        return jsonify({'error': 'Error uploading file', 'success': False}), 500

# def process_video(video_file_path, cursor):
def process_video(video_file_path: str, cursor: mysql.connector.cursor.MySQLCursor) -> None:
    # Call your ANPR script or function here passing the video_file_path
    import anpr  # Assuming anpr.py is in the same directory
    anpr.main(video_file_path, cursor)  # Pass the cursor to the ANPR function
@app.route('/dashboard')
def render_dashboard():
    try:
        mysql_connection.ping(reconnect=True)  # Check and reconnect if necessary
        cursor.execute("SELECT * FROM vehicle_records order by id desc")
        records = cursor.fetchall()
        return render_template('dashboard.html', records=records)
    except Exception as e:
        print(e)  # Log the exception for debugging purposes
        error_message = str(e) if str(e) else "Unknown error occurred."
        return render_template('error.html', error_message=error_message), 500

        
@app.route('/some_route')
def some_route():
    try:
        # Some code that might raise an exception
        # If an exception occurs, handle it and render the error page
        raise Exception("An error occurred")  # Example exception
    except Exception as e:
        error_message = str(e)
        return render_template('error.html', error_message=error_message), 500  # Pass error_message and HTTP status code


if __name__ == '__main__':
    app.run(debug=True, port=2000)
