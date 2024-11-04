# Guide to Run the Dockerized GasLeakage Application

## Overview
This guide walks you through two methods for deploying the Dockerized GasLeakage Application:
1. **Pull Images from DockerHub**
2. **Build Images Locally**

### Prerequisites
Ensure Docker is installed on your system. If it isn't, download Docker from the [official Docker Get Started page](https://docs.docker.com/get-docker/) and follow the setup instructions.

---

## Method 1: Pull Images from DockerHub
This section covers the steps to install and run the GasLeakage application using pre-built images from DockerHub.

### Step 1: Install Docker
Before you begin, make sure Docker is installed on your system. If Docker isn’t already installed, download it from the [official Docker Get Started page](https://docs.docker.com/get-docker/) and follow the instructions.

### Step 2: Clone the Repository from the Master Branch
To access the GasLeakage application code, clone the master branch of the repository. Open a terminal (or Command Prompt) and enter the following command:

git clone -b master https://github.com/sanajabbarweb/GasLeakage.git

#### Step 3: Navigate to the Project Directory

cd GasLeakage

### Step 4: Download Images from DockerHub

docker pull sanajabbar88/gasdet-streamlit_service:latest

docker pull sanajabbar88/gasdet-flask_service:latest

### Step 5: Modify Camera Stream URL for Live Streaming
1. Open the flask_app.py file.
2. Locate line 213, where rtsp_url is defined.
3. Replace url with the IP URL of your live camera feed in rtsp_url to enable live streaming.

### Step 6: Build and Start the Application Using Docker Compose

sudo docker-compose up --build

The --build flag ensures that Docker Compose rebuilds the application images if there are any updates to the Dockerfile or configuration files.

### Step 7: Access the Application
Open your web browser and go to:

http://localhost:8501/


### Step 8: Stop the Streamlit App
To close the app, press **Ctrl+C**, and if need to stop Docker the use the following command:

docker-compose down

