FROM postgres:latest

USER root

# Installing python and pip
RUN apt-get update && apt-get install -y python3 python3-venv python3-pip

# Setting up the work directory
WORKDIR /db_

# Creating a virtual environment
RUN  python3 -m venv /db_/venv

# Copying the files to the docker container/image
COPY validate_db.py /db_/validate_db.py
COPY Insert_db.py /db_/Insert_db.py
COPY requirements.txt /db_/requirements.txt
COPY init_db.sql /docker-entrypoint-initdb.d/init_db.sql
COPY entrypoint.sh /entrypoint.sh

# Installing the python dependencies
RUN /db_/venv/bin/pip install --no-cache-dir -r requirements.txt

# Ensure permissions to run entrypoint shell file
RUN chmod +x /entrypoint.sh

# Exposing the default postgres port
EXPOSE 5432 

# Setting the entrypoint of the shell
ENTRYPOINT ["/entrypoint.sh"]