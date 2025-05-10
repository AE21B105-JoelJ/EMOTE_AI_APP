# Emote AI - Suicide Detection AI App
This AI-powered tool analyzes text messages for signs of concerning mental health patterns. It's designed as a supportive resource, not a medical diagnostic tool.

## Details about the App
In the following sections of the Readme file the code organizations of the app is discussed. On how to use the app a user manual is attached with lower level design and high level design diagrams with the API endpoint definitions

GITHUB LINK : https://github.com/AE21B105-JoelJ/EMOTE_AI_APP.git

### Hosting the application
To host the services of the application, run the following command from the terminal (assuming docker engine is installed)

(following version command is for the linux)
```
docker compose up
```

below are the configured exposed port
- database : 5432 -> 5432
- backend : 18001 -> 18001 (remove this if you dont need to visualize the metrics)
- frontend : 8000 -> 8000 ; 18002 -> 18002 (remove this if you dont need to visualize the metrics)
- prometheus : 9090 -> 9090 (remove that if not needed)
- node exporter : 9100 -> 9100 (remove that if not needed)
- grafana : 3000 -> 3000

Change these ports which are exposed to localhost as per the available ports in your machine.

### DATABASE
Dockerfile
- Base image file used is the postgres.
- Python runtime and virtual environment is created and the requirements are installed.
- Init.sql creates the required table if not exists
- Validate_db script checks if the tables are existing and validates else creates one.
- Insert_db script inserts the required data to the database if not already done.

### BACKEND
Dockerfile
- Base image is the python:3.12-slim version
- Then the required files are copied in the working directory and the requirements are installed. And the backend is hosted and running.
- The Data_ volume is mounted to the backend to access the model files and the pickle files of the preprocessing and the data drift detection.
- From the docker compose file you can see the port 4000 is exposed to the docker networks alone and the 18001 port is exposed prometheus to scrap metrics. 
- Backend hosting is dependent of the database container.

Note : Except the frontend none of the exposed to localhost is used while running of the apps. The metrics are exposed to localhost only for visualization purposes. All the running is via docker networks only.

Backend_app.py
- Exposes metrics to the port "18001/metrics"
- Logs in the log volume mounted
- All functionalities of the backend. Connect to the database, Enter data into the database, Get the text and predict the sentiment and also detect drift. Get the logs files and pictures to be displayed in the webpage.
- Hosts the backend to 4000 port and FastAPI is used for hosting.

### FRONTEND
Dockerfile
- Base image is the python:3.12-slim version
- The required files of the frontend such as HTML files, CSS files, JS files along with the API are copied to the working directory.
- Port exposed to the localhost is 8000 which is the port where the frontend services are exported.
- From the docker-compose yaml file the port 18002 is exposed for prometheus metrics for the frontend apps. Without this expose also the prometheus be visualized because these ports are configured via promethues container which we will see later.
- The same Data_ folder is also mounted to the frontend to access any files if necessary.

Frontend_app.py
- Exposes metrics to the port "18002/metrics"
- Logs in the log volume mounted
- All functionalities of the frontend. Routing calls to backend, hosting the frontend using HTML, CSS and JavaScript.
- Hosts the frontend to 8000 port and FastAPI is used for hosting.

Other files
- The HTML, CSS and Javascript files are for the frontend application.

### PROMETHEUS
Prometheus.yml 
- The yaml file contains the container names and the port number for the promethus to scrape the metrics that are exported from the frontend, backend etc.

### NODE EXPORTER
- From the docker-compose yaml file that contains the port to expose the node metrics of the host computer

### GRAFANA
- From the docker-compose yaml file that contains the port to visualize the prometheus metrics configured in the grafana dashboard.
