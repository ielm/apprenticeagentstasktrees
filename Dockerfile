# Use an official Python runtime as a parent image
# FROM python:3.5
FROM python:3.6

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5002

# Define environment variable
# ENV NAME World

# Run corenlp_server.py when the container launches
#CMD ["python3.6", "backend/main.py", "host=0.0.0.0", "port=5002"]
CMD ["python3.6", "-m", "backend.main", "host=0.0.0.0", "port=5002"]