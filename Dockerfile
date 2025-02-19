# Use the official Python 3.12 slim image.
FROM python:3.12-slim

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Set the working directory inside the container.
WORKDIR /app

# Copy the requirements file and install dependencies.
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container.
COPY . .

# Expose port 8501 (the default port for Streamlit).
EXPOSE 8501

# Command to run the Streamlit app.
CMD ["streamlit", "run", "app.py", "--server.enableCORS", "false"]
