from flask import Flask, jsonify, request, Response, send_file
from ultralytics import YOLO
import numpy as np
import cv2
import os,io
import time
import imageio
from collections import deque
from threading import Thread
from datetime import datetime, timedelta
from pymongo import MongoClient
import numpy as np
import matplotlib
from datetime import datetime


matplotlib.use('Agg')  # Set the backend to Agg to avoid GUI issues
import matplotlib.pyplot as plt
app = Flask(__name__)

# MongoDB Configuration (Replace with your own)

MONGO_URI = "mongodb://mongodb:27017"  
client = MongoClient(MONGO_URI)
db = client["GasLeakage"]
collection = db["events"]


# YOLO Model loading
model = YOLO("./best.pt")

# Global variables for stats and tracking
tracked_cylinders = deque(maxlen=15)
stats_data = {
    "leakage": 0,
    "human_activity": 0,
    "latest_leakage_time": None,
    "latest_human_activity_time": None
}

# Define color mapping for different classes
COLOR_MAP = {
    "bumpy area": (0, 0, 255),
    "cylinder": (0, 165, 255),
    "leakage": (60, 230, 60),
    "human activity": (255, 0, 0),
    "plug": (255, 0, 255)
}

# Store events in MongoDB
def store_event_in_mongodb(event_type, start_frame, start_time, end_frame, end_time):
    event = {
        "event_type": event_type,
        "start_frame": start_frame,
        "start_time": start_time,
        "end_frame": end_frame,
        "end_time": end_time,
        "timestamp": datetime.utcnow()
    }

# Event tracking globals
leakage_active = False
human_activity_active = False
leakage_start_time = None
last_leakage_time = None
human_activity_start_time = None
last_human_activity_time = None
time_threshold = timedelta(seconds=20)
leakage_events = []
human_activity_events = []
total_leakage_count = 0
total_human_activity_count = 0

video_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # Format as needed
def process_video(video):
    global leakage_active, human_activity_active
    global leakage_start_time, last_leakage_time
    global human_activity_start_time, last_human_activity_time
    global total_leakage_count, total_human_activity_count

    #cap = cv2.VideoCapture(video)
    cap = cv2.VideoCapture(video, cv2.CAP_V4L2)
    if not cap.isOpened():
        print("Error: Unable to open video source.")
        return

    # Video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
   

    # Direct-to-disk video storage
    
    writer = imageio.get_writer(video_name+".mp4", fps=fps, codec="libx264")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        current_time = datetime.now()  # Capture the current time
        results = model.predict(frame, conf=0.5)

        leakage_detected = False
        human_activity_detected = False

        # Annotate frame with detected objects
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = result.names[class_id].lower()
                x1, y1, x2, y2 = int(box.xyxy[0][0]), int(box.xyxy[0][1]), int(box.xyxy[0][2]), int(box.xyxy[0][3])

                color = COLOR_MAP.get(class_name, (255, 255, 255))
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 15)
                cv2.putText(frame, class_name.capitalize(), (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 3, color, 10)

                # Leakage detection logic
                if class_name == "leakage":
                    leakage_detected = True
                    last_leakage_time = current_time
                    if not leakage_active:
                        leakage_active = True
                        leakage_start_time = current_time

                # Human activity detection logic
                if class_name == "human activity":
                    human_activity_detected = True
                    last_human_activity_time = current_time
                    if not human_activity_active:
                        human_activity_active = True
                        human_activity_start_time = current_time

        # Check if leakage detection has ended
        if not leakage_detected and leakage_active:
            time_without_leakage = current_time - last_leakage_time
            if time_without_leakage >= time_threshold:
                leakage_end_time = current_time
                leakage_events.append((leakage_start_time, leakage_end_time))
                store_event_in_mongodb("leakage", leakage_start_time, leakage_end_time)
                total_leakage_count += 1
                stats_data["leakage"] = total_leakage_count
                stats_data["latest_leakage_time"] = leakage_end_time
                leakage_active = False

        if not human_activity_detected and human_activity_active:
            time_without_human_activity = current_time - last_human_activity_time
            if time_without_human_activity >= time_threshold:
                human_activity_end_time = current_time
                human_activity_events.append((human_activity_start_time, human_activity_end_time))
                store_event_in_mongodb("human activity", human_activity_start_time, human_activity_end_time)
                total_human_activity_count += 1
                stats_data["human_activity"] = total_human_activity_count
                stats_data["latest_human_activity_time"] = human_activity_end_time
                human_activity_active = False

        # Convert frame to RGB for imageio writer
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        writer.append_data(frame_rgb)  # Write frame to output_video.mp4 in real-time

        # Stream frame to Flask/Streamlit
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        time.sleep(0.03)

    # Release resources
    cap.release()
    writer.close()

    # Return path to the saved video file if needed
    return str(video_name+".mp4")

# MongoDB event storage (without frame numbers)
def store_event_in_mongodb(event_type, start_time, end_time):
    event = {
        "event_type": event_type,
        "start_time": start_time,  # Time the event started
        "end_time": end_time,  # Time the event ended
        "timestamp": datetime.now()  # When the event was logged
    }

    try:
        collection.insert_one(event)
        print(f"Stored {event_type} event in MongoDB: {start_time} to {end_time}")
    except Exception as e:
        print(f"Error inserting {event_type} event into MongoDB: {e}")


#stream_url = 0
#@app.route('/video_feed')
#def video_feed():
#    return Response(process_video(stream_url), mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route('/video_feed')
def video_feed():
    # Retry until the file exists and can be opened
    while not os.path.exists('/app/video_feed.mjpeg'):
        print("Waiting for video feed to be available...")
        time.sleep(1)  # Wait 1 second before retrying

    # Open the file and stream once it's available
    return Response(open('/app/video_feed.mjpeg', 'rb'), mimetype='multipart/x-mixed-replace; boundary=frame')
# Flask API route to get real-time stats

@app.route('/get_stats', methods=['GET'])
def get_stats():
    # Convert datetime objects to string if they are not None
    latest_leakage_time_str = stats_data["latest_leakage_time"].strftime('%Y-%m-%d %H:%M:%S') if stats_data["latest_leakage_time"] else None
    latest_human_activity_time_str = stats_data["latest_human_activity_time"].strftime('%Y-%m-%d %H:%M:%S') if stats_data["latest_human_activity_time"] else None
    
    return jsonify({
        "leakage": stats_data["leakage"],  # Example placeholder, ensure actual logic
        "human_activity": stats_data["human_activity"],
        "latest_leakage_time": latest_leakage_time_str,
        "latest_human_activity_time": latest_human_activity_time_str
    })

# Event count retrieval function from MongoDB
def get_event_counts_per_day(event_type, start_date, end_date):
    pipeline = [
        {"$match": {"event_type": event_type, "timestamp": {"$gte": start_date, "$lte": end_date}}},
        {"$group": {"_id": {"year": {"$year": "$timestamp"}, "month": {"$month": "$timestamp"}, "day": {"$dayOfMonth": "$timestamp"}}, "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    results = list(collection.aggregate(pipeline))
    event_counts = {f"{result['_id']['year']}-{result['_id']['month']:02d}-{result['_id']['day']:02d}": result['count'] for result in results}
    return event_counts

# Plot event counts as an image

def plot_event_counts(event_counts, event_type):
    dates = list(event_counts.keys())
    counts = list(event_counts.values())

    # Set the figure size and background color
    fig, ax = plt.subplots(figsize=(10, 4), facecolor='white')  # White background for the figure
    
    # Plot the bars with a light color for better contrast on white background
    ax.bar(dates, counts, color='lightblue', edgecolor='black')
    
    # Set title and labels with increased font sizes and black color
    ax.set_title(f"{event_type.capitalize()} Events Per Day", color='black', fontsize=16)
    ax.set_xlabel("Date", color='black', fontsize=12)
    ax.set_ylabel("Count", color='black', fontsize=12)
    
    # Customize tick colors and font sizes
    ax.tick_params(axis='x', colors='black', labelsize=10)
    ax.tick_params(axis='y', colors='black', labelsize=10)
    
    # Add light gray gridlines for better readability
    #ax.grid(True, which='both', axis='y', linestyle='--', linewidth=0.7, color='lightgray')
    
    # Rotate x-tick labels for better readability
    plt.xticks(rotation=20, ha='right')

    # Save plot to an image buffer
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', facecolor='white')  # Ensure the saved image has a white background
    img.seek(0)
    plt.close(fig)  # Close the figure to free up memory
    
    return img


@app.route('/leakage_events', methods=['GET'])
def leakage_events_api():
    start_date = request.args.get('start_date', default=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', default= (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))
    
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1, seconds=-1)

    

    # Fetch the leakage events
    leakage_counts = get_event_counts_per_day("leakage", start_date, end_date)

    if leakage_counts:
        # Plot and return the image
        img = plot_event_counts(leakage_counts, "leakage")
        return send_file(img, mimetype='image/png')
    else:
        return jsonify({"message": "No leakage events found."}), 404


# Fetch and plot human activity events
@app.route('/human_activity_events', methods=['GET'])
def human_activity_events_api():
    start_date = request.args.get('start_date', default=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', default=datetime.now().strftime('%Y-%m-%d'))

    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1, seconds=-1)

    human_activity_counts = get_event_counts_per_day("human activity", start_date, end_date)

    if human_activity_counts:
        img = plot_event_counts(human_activity_counts, "human activity")
        return send_file(img, mimetype='image/png')
    else:
        return jsonify({"message": "No human activity events found."}), 404
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
