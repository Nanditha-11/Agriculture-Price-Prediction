# Use the official Python slim image
FROM python:3.14-slim

# Set working directory inside the container
WORKDIR /app

# Copy only the requirements first (helps caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the source code
COPY . .

# Expose the port Render expects (default 10000)
EXPOSE 10000

# The command Render will run to start the app
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:10000"]
