# Use an official Python runtime as a parent image
FROM python:3.8

# Set work directory
WORKDIR /code

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .
# Expose the port the app runs on
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
