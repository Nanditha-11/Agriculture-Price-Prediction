# Use the official Python slim image
FROM python:3.14-slim

# Set working directory inside the container
WORKDIR /app

# Copy the requirements file from the subfolder (handles spaces)
COPY "Agriculture Price Prediction"/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source from the subfolder (handles spaces)
COPY "Agriculture Price Prediction"/ .

# Expose the port Render expects (default 10000)
EXPOSE 10000

# Start the Flask app (app.py resides at the root of the copied files)
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:10000"]
