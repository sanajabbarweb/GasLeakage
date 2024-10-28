import streamlit as st
import requests
import cv2
import numpy as np
from datetime import datetime, timedelta
import time


st.set_page_config(layout="wide", page_title="Leakage Monitoring Dashboard")

# Custom styling
st.markdown("""
    <style>
    body {
        background-color: #000000;
        color: white;
    }
    .stApp {
        background-color: #000000;
    }
    h1,p {
        color: white;
        font-family: 'Arial', sans-serif;
    }
    h3, h2 {
        color: white;
        font-family: 'Arial', sans-serif;
    }
    .block-container {
        padding: 1rem;
    }
    .css-12oz5g7 {
        background-color: #1c1c1c !important;
        padding: 1.5rem !important;
        border-radius: 15px !important;
    }
    .css-1lcbmhc {
        color: #ffffff !important;
        font-size: 20px;
        font-weight: bold;
        font-family: 'Arial', sans-serif;
    }
    .css-1d391kg {
        color: #ffffff !important;
        font-size: 14px;
        font-family: 'Arial', sans-serif;
    }
    .stDateInput input {
        background-color: #333333 !important;
        color: #ffffff !important;
        border: 1px solid #555555 !important;
        border-radius: 8px !important;
        padding: 0.7rem !important;
        font-size: 14px;
    }
    .stButton > button {
        color: white !important;
        background-color: #333333 !important;
        border-radius: 8px !important;
        padding: 0.7rem 1rem !important;
        font-size: 14px;
        border: 1px solid #555555 !important;
    }
    .stButton > button:hover {
        background-color: #555555 !important;
    }
    .stImage > img {
        max-width: 550px;
        margin: auto;
        display: block;
        border-radius: 10px;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.4);
    }
    </style>
    """, unsafe_allow_html=True)

# Title and video section
st.title("Leakage Monitoring System")

# Main layout structure: one row with two columns
left_col, right_col = st.columns([1, 3])

# Placeholder for live stats
with left_col:
    st.subheader("Live Video Feed")
    leakage_count_placeholder = st.empty()
    human_activity_count_placeholder = st.empty()
    latest_leakage_time_placeholder = st.empty()
    latest_human_activity_time_placeholder = st.empty()

# Video placeholder
video_placeholder = right_col.empty()

# Function to display live video in Streamlit
def display_live_video():
    try:
        video_url = "http://gasdet-flask_service-1:5000/video_feed"
        video_bytes = requests.get(video_url, stream=True)
        bytes_data = bytes()

        # Continuously read and display frames from the video stream
        for chunk in video_bytes.iter_content(chunk_size=1024):
            bytes_data += chunk
            a = bytes_data.find(b'\xff\xd8')  # JPEG start
            b = bytes_data.find(b'\xff\xd9')  # JPEG end

            if a != -1 and b != -1:
                jpg = bytes_data[a:b + 2]
                bytes_data = bytes_data[b + 2:]

                # Decode the image
                img = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                # Resize the video frame
                img_rgb_resized = cv2.resize(img_rgb, (800, 300))
                
                # Update the placeholder with the current frame
                video_placeholder.image(img_rgb_resized, use_column_width=False)

    except Exception as e:
        st.error(f"Error fetching live video: {e}")

# Function to fetch and update stats
def fetch_stats():
    try:
        #response = requests.get("http://localhost:5000/get_stats")  # Ensure the correct URL
        response = requests.get("http://flask_service:5000/get_stats")
        if response.status_code == 200:
            stats = response.json()
            st.write(f"Stats Fetched: {stats}")  # Log for debugging purposes
            return stats
        else:
            st.error(f"Failed to fetch stats: {response.status_code} {response.reason}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching live stats: {e}")
        return None

# Function to update the live stats on Streamlit
def update_stats():
    stats = fetch_stats()
    
    if stats:
        leakage_count = stats.get("leakage", 0)
        human_activity_count = stats.get("human_activity", 0)
        latest_leakage_time = stats.get("latest_leakage_time", "N/A")
        latest_human_activity_time = stats.get("latest_human_activity_time", "N/A")

        # Update the placeholders with the latest data
        leakage_count_placeholder.markdown(f"**Total Leakages:** {leakage_count}")
        human_activity_count_placeholder.markdown(f"**Total Human Activities:** {human_activity_count}")
        latest_leakage_time_placeholder.markdown(f"**Last Leakage Time:** {latest_leakage_time}")
        latest_human_activity_time_placeholder.markdown(f"**Last Human Activity Time:** {latest_human_activity_time}")
    else:
        st.write("Waiting for data...")

# Sidebar for date input and overall stats plotting
start_date = st.sidebar.date_input("Start Date", value=(datetime.now() - timedelta(days=7)).date())
end_date = st.sidebar.date_input("End Date", value=datetime.now().date())

# Main content for chart reporting
col1, col2 = st.columns(2)

# Fetch and plot leakage and human activity events
if st.sidebar.button("Generate Reports"):
    with col1:
        response = requests.get(f"http://flask_service:5000/leakage_events?start_date={start_date}&end_date={end_date}")
        if response.status_code == 200:
            st.image(response.content, caption="Leakage Events Bar Chart", use_column_width=True)
        else:
            st.write("No leakage events found.")

    with col2:
        response = requests.get(f"http://flask_service:5000/human_activity_events?start_date={start_date}&end_date={end_date}")
        if response.status_code == 200:
            st.image(response.content, caption="Human Activity Events Bar Chart", use_column_width=True)
        else:
            st.write("No human activity events found.")

# Refresh video and stats every 5 seconds without blocking the UI
def run_dashboard():
    display_live_video()  # Update live video
    update_stats()  # Update live stats
    time.sleep(5)  # Wait for 5 seconds before updating again
    
    # Trigger app rerun
    st.rerun()  

# Call the dashboard function

run_dashboard()

