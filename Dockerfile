# Use a specific, slim Python base image for a smaller footprint
FROM python:3.12-slim

# Set environment variables for Python best practices in Docker
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
# This leverages Docker's build cache, so dependencies are only re-installed when requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user and group for security
# Running applications as a non-root user is a security best practice
RUN addgroup --system app && adduser --system --group app

# Copy the rest of the application code
COPY . .

# Change the ownership of the application directory to the non-root user
RUN chown -R app:app /app

# Switch to the non-root user
USER app

# Expose the port the app runs on
EXPOSE 5000

# Set the default command to run the application with Gunicorn
# --workers 3 is a sensible default; adjust based on your server's core count (e.g., (2 * cores) + 1)
CMD ["gunicorn", "whatsapp_webhook:app", "--bind", "0.0.0.0:5000", "--workers", "3"]
