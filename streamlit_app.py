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
    /* (Same styling as before) */
    </style>
    """, unsafe_allow_html=True)

st.title("Leakage Monitoring System")

left_col, right_col = st.columns([1, 3])

with left_col:
    st.subheader("Live Video Feed")
    leakage_count_placeholder = st.empty()
    human_activity_count_placeholder = st.empty()
    latest_leakage_time_placeholder = st.empty()
    latest_human_activity_time_placeholder = st.empty()

video_placeholder = right_col.empty()

# Sidebar for date input and overall stats plotting
start_date = st.sidebar.date_input("Start Date", value=(datetime.now() - timedelta(days=7)).date())
end_date = st.sidebar.date_input("End Date", value=datetime.now().date())

# Fetch and plot leakage and human activity events
if st.sidebar.button("Generate Reports"):
    with st.columns(2)[0]:
        response = requests.get(f"http://flask_service:5000/leakage_events?start_date={start_date}&end_date={end_date}")
        if response.status_code == 200:
            st.image(response.content, caption="Leakage Events Bar Chart", use_column_width=True)
        else:
            st.write("No leakage events found.")

    with st.columns(2)[1]:
        response = requests.get(f"http://flask_service:5000/human_activity_events?start_date={start_date}&end_date={end_date}")
        if response.status_code == 200:
            st.image(response.content, caption="Human Activity Events Bar Chart", use_column_width=True)
        else:
            st.write("No human activity events found.")

def display_live_video():
    try:
        video_url = "http://flask_service:5000/video_feed"
        video_bytes = requests.get(video_url, stream=True)
        bytes_data = bytes()
        for chunk in video_bytes.iter_content(chunk_size=1024):
            bytes_data += chunk
            a = bytes_data.find(b'\xff\xd8')
            b = bytes_data.find(b'\xff\xd9')
            if a != -1 and b != -1:
                jpg = bytes_data[a:b + 2]
                bytes_data = bytes_data[b + 2:]
                img = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img_rgb_resized = cv2.resize(img_rgb, (800, 300))
                video_placeholder.image(img_rgb_resized, use_column_width=False)
    except Exception as e:
        st.error(f"Error fetching live video: {e}")

def fetch_and_display_stats():
    try:
        response = requests.get("http://flask_service:5000/get_stats")
        if response.status_code == 200:
            stats = response.json()
            leakage_count = stats.get("leakage", 0)
            human_activity_count = stats.get("human_activity", 0)
            latest_leakage_time = stats.get("latest_leakage_time", "N/A")
            latest_human_activity_time = stats.get("latest_human_activity_time", "N/A")
            leakage_count_placeholder.markdown(f"**Total Leakages:** {leakage_count}")
            human_activity_count_placeholder.markdown(f"**Total Human Activities:** {human_activity_count}")
            latest_leakage_time_placeholder.markdown(f"**Last Leakage Time:** {latest_leakage_time}")
            latest_human_activity_time_placeholder.markdown(f"**Last Human Activity Time:** {latest_human_activity_time}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching live stats: {e}")

# Main loop: Update video and stats independently
while True:
    fetch_and_display_stats()  # Update live stats
    time.sleep(5)  # Fetch stats every 5 seconds
    display_live_video()  # Display video continuously
