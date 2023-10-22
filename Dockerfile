
FROM python:3.9-slim

## Install FFmpeg
#RUN apt-get update && apt-get install -y ffmpeg

# Install required system packages and clean up to minimize image size
#RUN #apt-get update && apt-get install -y --no-install-recommends ffmpeg && apt-get clean && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y --no-install-recommends --fix-missing ffmpeg && apt-get clean && rm -rf /var/lib/apt/lists/*
# Set the working directory
WORKDIR /app

# Set the working directory
WORKDIR /app

# Copy your Python script and extension to the container
COPY app.py /app/app.py
COPY logger /app/logger
COPY service /app/service
COPY routes /app/routes
COPY extensions /app/extensions

# Copy requirements.txt and install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip3 install -r requirements.txt

## Set the URL environment variable
#ENV URL https://www.mako.co.il/news-military/6361323ddea5a810/Article-266c9903a293b81027.htm?partner=lobby

## Expose port 80
#EXPOSE 80

CMD ["python", "app.py"]
