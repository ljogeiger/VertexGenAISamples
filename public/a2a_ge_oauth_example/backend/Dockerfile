
# Use an official Python runtime as a parent image
FROM python:3.13.3

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

# Make port 9998 available to the world outside this container
EXPOSE 9998

# Run the app
CMD ["python", "a2a_server_calendar_agent.py"]
