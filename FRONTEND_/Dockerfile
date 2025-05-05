FROM python:3.12-slim

USER root

# Installing python and pip
RUN apt-get update && apt-get install -y python3-venv

# Setting up the work directory
WORKDIR /frontend_

# Creating a virtual environment
RUN  python3 -m venv /frontend_/venv

# Copying files to docker container/image
COPY frontend_app.py /frontend_/frontend_app.py
COPY requirements.txt /frontend_/requirements.txt
COPY contact.html /frontend_/contact.html
COPY diagnostic.html /frontend_/diagnostic.html
COPY feedback.html /frontend_/feedback.html
COPY index.html /frontend_/index.html
COPY logs.html /frontend_/logs.html
COPY visualizations.html /frontend_/visualizations.html
COPY script.js /frontend_/script.js
COPY styles.css /frontend_/styles.css

# Installing the python dependencies
RUN /frontend_/venv/bin/pip install --no-cache-dir -r requirements.txt

# Exposing the default frontend port
EXPOSE 8000

CMD ["/frontend_/venv/bin/python3", "frontend_app.py"]