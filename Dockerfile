FROM python:3.10-slim

# Install system packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .


# Then install remaining packages
RUN pip install -r requirements.txt

COPY . .



# Run the app (change to your actual app entry point if needed)
CMD ["python", "main.py"]
