import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, Response,send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
from datetime import datetime, timedelta
from threading import Thread
import time
import requests
import subprocess
import seaborn as sns
import io
import atexit
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
# env for Database Authentication and Access
load_dotenv()

app = Flask(__name__, template_folder='template')   
detection_process = None
app.secret_key = os.getenv('SECRET_KEY') 
loophole_process = None
# Function to start the Loophole tunnel
def start_loophole():
    loophole_path = r"C:/Users/harsh/loophole.exe"
    # Updated command to start Loophole with the correct syntax
    loophole_command = [loophole_path, "http", "5000", "--hostname", "gruhrashak"]
    loophole_process = subprocess.Popen(loophole_command)
    print("Loophole tunnel started.")

# Function to stop the Loophole tunnel
def stop_loophole():
    if loophole_process:
        loophole_process.terminate()  # Terminate the Loophole process
        loophole_process.wait()  # Wait for the process to terminate
        print("Loophole tunnel stopped.")

# Register the stop function to be called on exit
atexit.register(stop_loophole)


def get_db_connection():
    """Establish a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"OperationalError: {e}")
        return None

#functions for automatic deletion after exceeding size limit 
def get_database_size():
    """Get the total size of the PostgreSQL database."""
    conn = get_db_connection()
    if conn is None:
        print("Failed to connect to the database")
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
            size = cur.fetchone()[0]
            return size
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()

def check_and_clean_database(max_size_mb=650):
    """Check the database size and clean if necessary."""
    size = get_database_size()
    if size is None:
        return
    
    # Convert size to MB for   automated deletion process
    size_mb = int(size.split()[0].replace('kB', '').replace('MB', '').replace('GB', ''))
    
    if size_mb >= max_size_mb:
        conn = get_db_connection()
        if conn is None:
            print("Failed to connect to the database for cleanup")
            return
        
        try:
            with conn.cursor() as cur:
                #  Delete records older than a specific date
                cutoff_date = datetime.now() - timedelta(days=30)
                cur.execute("DELETE FROM temperature_data WHERE timestamp < %s", (cutoff_date,))
                cur.execute("DELETE FROM humidity_data WHERE timestamp < %s", (cutoff_date,))
                cur.execute("DELETE FROM mq6_data WHERE timestamp < %s", (cutoff_date,))
                conn.commit()
        except psycopg2.Error as e:
            print(f"Database error during cleanup: {e}")
        finally:
            conn.close()
# Dictionary to store the initial update time for each ESP32 s

def update_last_update_time(device):
    """Update the last update time for a specific ESP32 device."""
    if device in last_update_times:
        last_update_times[device] = datetime.now()


# List of ESP32 device IDs
esp32_ids = ['esp32_1', 'esp32_2']  # Replace with your actual ESP32 IDs

# Dictionary to store the last update times of each ESP32 device
last_update_times = {esp32_id: None for esp32_id in esp32_ids}

def monitor_esp32_status():
    while True:
        with app.app_context():
            current_time = datetime.now()
            for esp32_id in esp32_ids:
                last_update_time = last_update_times.get(esp32_id)
                if last_update_time and (current_time - last_update_time).seconds > 5:
                    # Mark as offline if no update within the last 5 seconds
                    last_update_times[esp32_id] = None
        time.sleep(5)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/aht21')
def aht21():
    return render_template('aht21.html')

@app.route('/mq6')
def mq6():
    return render_template('mq6.html')

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

@app.route('/temperature_humidity_data', methods=['POST'])
def receive_temp_humidity_data():
    data = request.json
    print(f"Received temperature and humidity data: {data}")
    timestamp = datetime.now()
    update_last_update_time('esp32_1')

    conn = get_db_connection()
    if conn is None:
        return "Failed to connect to the database", 500

    try:
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO temperature_data (timestamp, temperature) VALUES (%s, %s)',
                (timestamp, data['temperature'])
            )
            cur.execute(
                'INSERT INTO humidity_data (timestamp, humidity) VALUES (%s, %s)',
                (timestamp, data['humidity'])
            )
            conn.commit()
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return "Failed to insert data", 500
    finally:
        conn.close()

    return "Temperature and humidity data received successfully"

@app.route('/mq6_data', methods=['POST'])
def receive_mq6_data():
    data = request.json
    print(f"Received MQ6 data: {data}")
    timestamp = datetime.now()
    update_last_update_time('esp32_2')

    conn = get_db_connection()
    if conn is None:
        return "Failed to connect to the database", 500

    try:
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO mq6_data (timestamp, mq6_reading) VALUES (%s, %s)',
                (timestamp, data['mq6_reading'])
            )
            conn.commit()
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return "Failed to insert data", 500
    finally:
        conn.close()

    return "MQ6 data received successfully"

@app.route('/aht21_temperature_data', methods=['GET'])
def get_aht21_temperature_data():
    conn = get_db_connection()
    if conn is None:
        return "Failed to connect to the database", 500

    try:
        with conn.cursor() as cur:
            cur.execute('SELECT timestamp, temperature FROM temperature_data ORDER BY timestamp DESC')
            temperature_data = cur.fetchall()
            #print(f"Fetched AHT21 temperature data: {temperature_data}")

        return jsonify(temperature_data)
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return "Failed to retrieve data", 500
    finally:
        conn.close()

@app.route('/aht21_humidity_data', methods=['GET'])
def get_aht21_humidity_data():
    conn = get_db_connection()
    if conn is None:
        return "Failed to connect to the database", 500

    try:
        with conn.cursor() as cur:
            cur.execute('SELECT timestamp, humidity FROM humidity_data ORDER BY timestamp DESC')
            humidity_data = cur.fetchall()
            #print(f"Fetched AHT21 humidity data: {humidity_data}")

        return jsonify(humidity_data)
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return "Failed to retrieve data", 500
    finally:
        conn.close()

@app.route('/mq6_data', methods=['GET'])
def get_mq6_data():
    conn = get_db_connection()
    if conn is None:
        return "Failed to connect to the database", 500

    try:
        with conn.cursor() as cur:
            cur.execute('SELECT timestamp, mq6_reading FROM mq6_data ORDER BY timestamp DESC')
            mq6_data = cur.fetchall()
            #print(f"Fetched MQ6 data: {mq6_data}")

        return jsonify(mq6_data)
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return "Failed to retrieve data", 500
    finally:
        conn.close()

@app.route('/esp32_status')
def esp32_status():
    current_time = datetime.now()
    statuses = {}
    for esp32_id in esp32_ids:
        last_update_time = last_update_times.get(esp32_id)
        if last_update_time and (current_time - last_update_time).seconds <= 5:
            statuses[esp32_id] = 'online'
        else:
            statuses[esp32_id] = 'offline'
    return jsonify(statuses)


@app.route('/plot_mq6')
def plot_mq6():
    conn = get_db_connection()
    if conn is None:
        return "Failed to connect to the database", 500

    try:
        with conn.cursor() as cur:
            cur.execute('SELECT timestamp, mq6_reading FROM mq6_data ORDER BY timestamp')
            data = cur.fetchall()

        timestamps_mq6 = [row[0] for row in data]
        mq6_readings = [row[1] for row in data]

        sns.set(style="whitegrid")
        plt.figure(figsize=(10, 6))
        sns.lineplot(x=timestamps_mq6, y=mq6_readings, marker='o', color='red')
        plt.title('MQ6 Sensor Data')
        plt.xlabel('Timestamp')
        plt.ylabel('MQ6 Reading')
        plt.xticks(rotation=45)
        plt.tight_layout()

        img_bytesio = io.BytesIO()
        plt.savefig(img_bytesio, format='png')
        img_bytesio.seek(0)
        plt.close()

        return send_file(img_bytesio, mimetype='image/png')
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return "Failed to retrieve data", 500
    finally:
        conn.close()

@app.route('/plot_aht21')
def plot_aht21():
    conn = get_db_connection()
    if conn is None:
        return "Failed to connect to the database", 500

    try:
        with conn.cursor() as cur:
            cur.execute('SELECT timestamp, temperature FROM temperature_data ORDER BY timestamp')
            temperature_data = cur.fetchall()

            cur.execute('SELECT timestamp, humidity FROM humidity_data ORDER BY timestamp')
            humidity_data = cur.fetchall()

        timestamps_temperature = [row[0] for row in temperature_data]
        temperatures = [row[1] for row in temperature_data]

        timestamps_humidity = [row[0] for row in humidity_data]
        humidities = [row[1] for row in humidity_data]

        sns.set(style="whitegrid")
        plt.figure(figsize=(10, 12))

        plt.subplot(2, 1, 1)
        sns.lineplot(x=timestamps_temperature, y=temperatures, marker='o', color='blue')
        plt.title('Temperature Data')
        plt.xlabel('Timestamp')
        plt.ylabel('Temperature (°C)')
        plt.xticks(rotation=45)

        plt.subplot(2, 1, 2)
        sns.lineplot(x=timestamps_humidity, y=humidities, marker='o', color='green')
        plt.title('Humidity Data')
        plt.xlabel('Timestamp')
        plt.ylabel('Humidity (%)')
        plt.xticks(rotation=45)

        plt.tight_layout()

        img_bytesio = io.BytesIO()
        plt.savefig(img_bytesio, format='png')
        img_bytesio.seek(0)
        plt.close()

        return send_file(img_bytesio, mimetype='image/png')
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return "Failed to retrieve data", 500
    finally:
        conn.close()

@app.route('/overall')
def overall():
    conn = get_db_connection()
    if conn is None:
        return "Failed to connect to the database", 500

    try:
        with conn.cursor() as cur:
            cur.execute('SELECT timestamp, mq6_reading FROM mq6_data ORDER BY timestamp')
            mq6_data = cur.fetchall()

            cur.execute('SELECT timestamp, temperature FROM temperature_data ORDER BY timestamp')
            temperature_data = cur.fetchall()

            cur.execute('SELECT timestamp, humidity FROM humidity_data ORDER BY timestamp')
            humidity_data = cur.fetchall()

        timestamps_mq6 = [row[0] for row in mq6_data]
        mq6_readings = [row[1] for row in mq6_data]

        timestamps_temperature = [row[0] for row in temperature_data]
        temperatures = [row[1] for row in temperature_data]

        timestamps_humidity = [row[0] for row in humidity_data]
        humidities = [row[1] for row in humidity_data]

        sns.set(style="whitegrid")
        plt.figure(figsize=(18, 18))

        plt.subplot(3, 1, 1)
        sns.lineplot(x=timestamps_mq6, y=mq6_readings, marker='o', color='red')
        plt.title('MQ6 Sensor Data')
        plt.xlabel('Timestamp')
        plt.ylabel('MQ6 Reading')
        plt.xticks(rotation=45)

        plt.subplot(3, 1, 2)
        sns.lineplot(x=timestamps_temperature, y=temperatures, marker='o', color='blue')
        plt.title('Temperature Data')
        plt.xlabel('Timestamp')
        plt.ylabel('Temperature (°C)')
        plt.xticks(rotation=45)

        plt.subplot(3, 1, 3)
        sns.lineplot(x=timestamps_humidity, y=humidities, marker='o', color='green')
        plt.title('Humidity Data')
        plt.xlabel('Timestamp')
        plt.ylabel('Humidity (%)')
        plt.xticks(rotation=45)

        plt.tight_layout()

        img_bytesio = io.BytesIO()
        plt.savefig(img_bytesio, format='png')
        img_bytesio.seek(0)
        plt.close()

        return send_file(img_bytesio, mimetype='image/png')
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return "Failed to retrieve data", 500
    finally:
        conn.close()

# LoginManager From FLask For Login and Logout Pages
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

#  authentication dictionary for storing login credentials
users = {
    'admin': {'password': 'password'},
    'harshal': {'password': 'harshal24'},
    'akshay': {'password': 'akshay24'},
    'harshalM': {'password': 'simonriley'},
    'Tanmay': {'password': 'Tankishere'}
}

class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(user_id):
    return User(user_id) if user_id in users else None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in users and users[username]['password'] == password:
            login_user(User(username))
            return redirect(url_for('object_detection'))
        else:
            return "Invalid credentials", 403
    return render_template('login.html')

@app.route('/object_detection')
@login_required
def object_detection():
    return render_template('object_detection.html')


@app.route('/start_detection', methods=['POST'])
@login_required
def start_detection():
    global detection_process
    if detection_process is None:
        detection_process = subprocess.Popen(["python", "object_detection/detection.py"])
        return jsonify({"status": "Detection started"}), 200
    else:
        return jsonify({"status": "Detection already running"}), 400

@app.route('/stop_detection', methods=['POST'])
@login_required
def stop_detection():
    global detection_process
    if detection_process:
        detection_process.terminate()
        detection_process.wait()
        detection_process = None
        return jsonify({"status": "Detection stopped"}), 200
    else:
        return jsonify({"status": "No detection process running"}), 400

# Route to handle user logout
@app.route('/logout')
def logout():
    global detection_process
    if detection_process:
        detection_process.terminate()
        detection_process.wait()
        detection_process = None
    session.pop('user_id', None)
    return redirect(url_for('login'))





if __name__ == '__main__':
    # Start the Loophole tunnel when the application starts
    start_loophole()
    # Start the background thread for monitoring ESP32 status
    esp32_monitor_thread = Thread(target=monitor_esp32_status, daemon=True)
    esp32_monitor_thread.start()
    # Start the background thread for checking and cleaning the database
    db_cleanup_thread = Thread(target=check_and_clean_database, daemon=True)
    db_cleanup_thread.start()
    app.run(host='0.0.0.0', port=5000)
