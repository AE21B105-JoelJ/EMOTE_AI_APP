FROM python:3.12-slim

USER root

# Installing python and pip
RUN apt-get update && apt-get install -y python3-venv

# Setting up the work directory
WORKDIR /backend_

# Creating a virtual environment
RUN  python3 -m venv /backend_/venv

# Copying files to docker container/image
COPY backend_app.py /backend_/backend_app.py
COPY Utils.py /backend_/Utils.py
COPY requirements.txt /backend_/requirements.txt

# Installing the python dependencies
RUN /backend_/venv/bin/pip install --no-cache-dir -r requirements.txt

# Exposing the default backend port
EXPOSE 4000

CMD ["/backend_/venv/bin/python3", "backend_app.py"]