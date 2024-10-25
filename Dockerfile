# Use an official Python runtime as a parent image
FROM python:3.8.2
 

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
# You need to have a requirements.txt file with streamlit and other dependencies
RUN pip install --upgrade pip

RUN pip install -r requirements.txt

# Expose the port that Streamlit runs on
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "app.py"]
