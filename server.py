from flask import Flask, request, jsonify, send_from_directory, render_template
from datetime import datetime, timedelta
import csv
import os



app = Flask(__name__)

latest_position = {}
history = []
criticals = []

# Log files
FULL_LOG = "gps_log.csv"
FILTERED_LOG = "gps_log_filtered.csv"
last_filtered_log_time = None  # Used to compare time spacing

# Ensure headers exist
for log_path in [FULL_LOG, FILTERED_LOG]:
    if not os.path.exists(log_path):
        with open(log_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "lat", "lng", "speed", "alert"])

@app.route('/gps', methods=['GET'])
def gps_data():
    global latest_position, last_filtered_log_time

    lat = float(request.args.get("lat"))
    lng = float(request.args.get("lng"))
    speed = float(request.args.get("speed"))
    date = request.args.get("date")
    time = request.args.get("time")


    timestamp_str = f"{date}T{time}"
    timestamp = datetime.strptime(timestamp_str, "%d-%m-%YT%H:%M:%S")

    latest_position = {
        "lat": lat,
        "lng": lng,
        "speed": speed,
        "timestamp": timestamp_str
    }

    print(f"📍  GPS => Lat: {lat}, Lng: {lng}, Speed: {speed:.2f} km/h, Time: {timestamp_str}")
    history.append(latest_position)

    # 1️⃣ Log everything to the full log
    with open(FULL_LOG, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp_str, lat, lng, speed, "🚨 " if speed > 6 else ""])

    # 2️⃣ Conditional logging to filtered log
    should_log = False
    if speed > 3:
        should_log = True
    elif last_filtered_log_time is None or (timestamp - last_filtered_log_time).total_seconds() >= 1800:
        should_log = True

    if should_log:
        criticals.append(latest_position)
        with open(FILTERED_LOG, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp_str, lat, lng, speed, "🚨 " if speed > 6 else ""])
        last_filtered_log_time = timestamp

    return "✅  Logged data\n"

@app.route('/latest')
def latest():
    return jsonify(latest_position if latest_position else {"message": "No data yet"})

@app.route('/history')
def get_history():
    return jsonify(history)

@app.route('/')
def serve_map():
    return send_from_directory('.', 'index.html')

@app.route('/download/<filename>')
def download_log(filename):
    if filename in [FULL_LOG, FILTERED_LOG]:
        return send_from_directory('.', filename, as_attachment=True)
    return "❌  File not found", 404


@app.route('/log')
def log_page():
    return render_template('log.html', entries=history)

@app.route('/critical')
def critical_page():
    return render_template('critical.html', entries=criticals)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

