## Backend script for the API calls ##

# Importing the necessary libraries required #
import logging
import os
import sys
import time
from fastapi import FastAPI, Body, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from threading import Thread
from prometheus_client import Summary, start_http_server, Counter, Gauge, Info
from prometheus_client import disable_created_metrics
import pickle
import uvicorn
import base64
import psycopg2
import Utils
import numpy as np
import onnxruntime as ort


# Creating useful prometheus metrics
# disabling the created metrics
disable_created_metrics()

# _sum will track the total bytes, _count will track the number of calls.
request_size = Summary('input_bytes_be', 'input data size (bytes)') 
# _sum tracks total time taken, _count tracks number of calls
api_usage = Summary('api_runtime_be', 'api run time monitoring')

# define the counter to track the usage based on client IP.
api_counter = Counter('api_call_counter_be', 'number of times that API is called', ['endpoint', 'client'])
api_gauge = Gauge('api_runtime_secs_be', 'runtime of the method in seconds', ['endpoint', 'client']) 

# adding build information to the info metric.
info = Info('my_build', 'Prometheus Instrumented AI App for Suicide Detection')
info.info({'version': '0.0.1', 'buildhost': '@Instinct', 'author': 'Joel J @ IITM', 'builddate': 'April 2025'})

# Creating onnx runtime session
session = ort.InferenceSession("/var/Data_/model_best.onnx")

# create the AI application
app = FastAPI(title="AI Application for Suicide Detection (via text)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Setting up the logging 
log_file = "/var/log/backend.log"
logging.basicConfig(
    level = logging.DEBUG,
    format = "%(asctime)s - %(levelname)s - %(message)s",
    handlers = [
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

logger.info("The Backend is starting now !!!")

try:
    # Getting the Environment variables
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'postgres')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'postgres_db')
    POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', 5432))
    logging.info("Setting up the environment variables successful")

except Exception as e:
    logging.error("Environment variables setup unsuccessful !!")
    sys.exit(1)


# Pydantic model for inputs
class input_data(BaseModel):
    text : str

class input_feedback(BaseModel):
    rating : int
    comments : str

class input_diagnostic(BaseModel):
    text : str
    label : str

def load_preprocessor(filename):
    """
    Loads the preprocessing class with pickle binary
    """
    logger.info("Loading the preprocessor from the pickle file")
    with open(filename, 'rb') as f:
        loaded_preprocessor = pickle.load(f)
    return loaded_preprocessor

def load_detector(filename):
    """
    Loads the drift detector class with pickle binary
    """
    logger.info("Loading the detector from the pickle file")
    with open(filename, 'rb') as f:
        loaded_detector = pickle.load(f)
    return loaded_detector

# Global loading of model and processor
from Utils import TextPreprocessor, DriftDetector
processor = TextPreprocessor()
processor = load_preprocessor(filename="/var/Data_/preprocess_obj_numpy.pkl")
detector = load_detector(filename="/var/Data_/drift_uni_obj.pkl")

def connect_to_db(use_env = True):
    """
    Connect to the database and return the connection
    """

    logging.info("Connecting to the database from backend")
    if use_env:
        conn = None
        try:
            logging.info("Connecting to the database ...")
            conn = psycopg2.connect(dbname = POSTGRES_DB,
                                    user = POSTGRES_USER, 
                                    password = POSTGRES_PASSWORD,
                                    host = POSTGRES_HOST, 
                                    port = POSTGRES_PORT)
        except psycopg2.OperationalError as e:
            logging.error(f"Error in connecting to the database {e}")
            print(f"Error in connecting to the database {e}")
            sys.exit(1)

        if conn is None:
            logging.error("Error in connecting to the database")
            print("Error in connecting to the database")
            sys.exit(1)

        return conn

    else:
        logging.critical("The database configuration without environment variables is not configured")
        logging.debug("The database configuration without environment variables is not configured")
        sys.exit(1)

        return None
    
def insert_to_db_feedback(conn, json):
    cursor = conn.cursor()

    try: 
        cursor.execute(
            """ INSERT INTO feedback (rating, text_message)
            VALUES (%s, %s)
            """,
            (json.rating, json.comments)
        )

        logger.info("Insertion of the row is successful")
        if cursor.rowcount > 0:
            conn.commit()
            logger.info("Committed sucessfully !!!")
        else:
            conn.rollback()
            logger.warn("Commit to database unsucessful !!!")
    except Exception as e:
        logger.error(f"Error in inserting into the database {e}")
        conn.rollback()

    cursor.close()
    conn.close()
    return
    
def insert_to_db_feed(conn, json):
    cursor = conn.cursor()
    try: 
        cursor.execute(
            """ INSERT INTO sd_feed (text_message, label)
            VALUES (%s, %s)
            """,
            (json.text, json.label)
        )

        logger.info("Insertion of the row is successful")
        if cursor.rowcount > 0:
            conn.commit()
            logger.info("Committed sucessfully !!!")
        else:
            conn.rollback()
            logger.warn("Commit to database unsucessful !!!")
    except Exception as e:
        logger.error(f"Error in inserting into the database {e}")
        conn.rollback()

    cursor.close()
    conn.close()
    return


@app.post("/predict")
@api_usage.time()
def predict_using_model(input : input_data, request:Request):
    # Logging #
    logger.info(f"predict body : receiving {len(input.text)} bytes on input")
    # tracking te amount of data processed by API #
    request_size.observe(amount = len(input.text))
    # Increasing the counter of API per host
    api_counter.labels(endpoint = "/predict", client=request.client.host).inc()
    # Preprocessing the text
    logger.info("Processing the text input")
    text_in = input.text

    if detector.is_drifted(text_in):
        logger.info("drift detected for the input ...")
        return {"risk" : "drift_detected"}

    text_pr = processor.process(text_in)
    # Predicting using the model
    logger.info("Predicting from the processed text input")
    ort_input = {"input" : text_pr}
    ort_output = session.run(None, ort_input)

    prediction = ort_output[0].item()

    # Output 
    if prediction >= 0.5:
        output = "high"
    elif prediction >=0.3:
        output = "medium"
    else:
        output = "low"

    return {"risk" : output}

@app.post("/feedback")
@api_usage.time()
def feedback_loader(data : input_feedback, request:Request):
    # Logging #
    logger.info(f"feedback body : receiving {len(data.comments)} bytes on input")
    # Tracking the amount of data processed by the API #
    request_size.observe(amount = len(data.comments))
    # Increasing the API usage count per host
    api_counter.labels(endpoint = "/feedback", client=request.client.host).inc()

    # Enter into the database
    logger.info("pushing the data into the database")
    conn = connect_to_db()
    insert_to_db_feedback(conn, data)

    return None

@app.post("/diagnostic")
@api_usage.time()
def feed_loader(data : input_diagnostic, request:Request):
    # Logging #
    logger.info(f"feedback body : receiving {len(data.text)} bytes on input")
    logger.info(f"feedback body : receiving {len(data.label)} bytes on input")
    # Tracking the amount of data processed by the API #
    request_size.observe(amount = len(data.text))
    # Increasing the API usage count per host
    api_counter.labels(endpoint = "/diagnostic", client=request.client.host).inc()

    # Enter into the database
    logger.info("pushing the data into the database")
    conn = connect_to_db()
    insert_to_db_feed(conn, data)

    return None

@app.get("/visualizations/{plot_name}")
@api_usage.time()
def image_output(plot_name : str, request:Request):
    logger.info("Getting the image for visualization")
    # Increasing the API usage count per host
    api_counter.labels(endpoint = "/visualizations", client=request.client.host).inc()

    # Define the path where images are stored
    path = "/var/Data_/"

    # A dictionary to map plot names to their respective file names
    plot_files = {
        "CDD": "CDD.png",
        "WC": "WC.png",
        "WF": "WF.png",
        "PIPE": "PIPE.png"
    }
    
    # Check if the plot_name exists in the dictionary
    if plot_name not in plot_files:
        return JSONResponse(content={"error": "Plot not found"}, status_code=404)

    # Build the file path
    file_path = path + plot_files[plot_name]
    
    try:
        with open(file_path, "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode("utf-8")
        return JSONResponse(content={"image_base64": encoded_string})
    except FileNotFoundError:
        return JSONResponse(content={"error": f"File {file_path} not found"}, status_code=404)
    except Exception as e:
        logger.error(f"Error processing the image: {e}")
        return JSONResponse(content={"error": "An error occurred while processing the image"}, status_code=500)

@app.get("/logs/{container_name}")
@api_usage.time()
def logs_output(container_name : str, request:Request):
    logger.info("Getting the logs for visualization")
    # Increasing the API usage count per host
    api_counter.labels(endpoint = "/logs", client=request.client.host).inc()

    # Defining the path where log are stored
    path = f"/var/log/{container_name}.log"

    try:
        with open(path, 'r') as file:
            log_text = file.read()
        
        return {"log_text": log_text}
    except Exception as e:
        logger.error(f"Error reading log file: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to read log file"}
        )

if __name__ == "__main__":
    # Starting to expose the metrics at prometheus monitor
    logger.info("Starting the prometheus monitor at port 18001")
    start_http_server(18001)

    # Starting the fastAPI server
    uvicorn.run("__main__:app", host = "0.0.0.0", port=4000)