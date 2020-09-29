# Set base image
FROM python:3.8.2

# Set work directory
WORKDIR /app

# Copy the current directory contents into the container at /app 
ADD . /app

# Install dependencies
RUN pip install -r requirements.txt

# command to run on container start
CMD ["python3", "./main.py"]