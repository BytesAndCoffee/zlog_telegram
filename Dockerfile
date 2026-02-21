# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
# If your application uses a port, uncomment the following line and replace 80 with your port
# EXPOSE 80

# Copy the .env file into the container at /app
COPY .env /app

# Run sqlpush.py when the container launches
CMD ["python", "sqlpush.py"]

