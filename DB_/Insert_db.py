# Inserter Script -- Inserts the data into the database #

# Importing the libraries needed
import pandas as pd
import logging
import os
import sys
import psycopg2
from sklearn.model_selection import train_test_split
from datasets import load_dataset
from psycopg2.extras import execute_values


## Setting up the logging ##
log_file = "/var/log/db.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),  
        logging.StreamHandler()         
    ]
)
logger = logging.getLogger(__name__)

logger.info("Data Insertion into db script has started !!!")

try:
    # Getting the Environment variables
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'postgres')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', 5432))
    DATASET_1_NAME = os.getenv("DATASET_1_NAME", "vibhorag101/suicide_prediction_dataset_phr")
    DATASET_2_NAME = os.getenv("DATASET_2_NAME", "PrevenIA/spanish-suicide-intent")
    logging.info("Setting up the environment variables successful")

except Exception as e:
    logging.error("Environment variables setup unsuccessful !!")
    sys.exit(1)
    

# Loading the data from the huggingface
def load_pandas_dataset(dataset_name : str, feature_name : str, target_name : str, split = True ):
    """
    Loads the dataset named from hugging face and converts to pandas dataframe
    dataset_name : str (name of the database)
    feature_name : str (feature name to extract)
    target_name : str (target name to extract)
    split : if the split is present already
    """

    logging.info("Getting the data from Huggingface")
    try:
        ds = load_dataset(dataset_name)
        logging.info("Loading the dataset from Huggingface is successful !!")
    except Exception as E:
        logging.critical(f"The dataset loading from hugging face failed. error : {E}")
        sys.exit(1)

    # If the split is already present
    if split:
        train_pd = ds["train"].to_pandas()
        test_pd = ds["test"].to_pandas()
    
    else:
        pd_total = ds.to_pandas()
        # Startified split
        train_pd, test_pd = train_test_split(pd_total, test_size=0.2, stratify=pd_total[target_name])

    logging.info("The split dataframe is done and returned from function...")
    return train_pd, test_pd

def make_pd_database_pushable(train_pd, test_pd, feature_name : str, target_name : str, type_chk = "str"):
    """
    Makes the pandas dataframe easily pushable into the database
    train_pd : pd.DataFrame of the train data
    test_pd : pd.DataFrame of the test data
    feature_name : str (feature name to extract)
    target_name : str (target name to extract)
    """

    logging.info("Making the dataframe database pushable")
    train_data = train_pd[[feature_name, target_name]].copy()
    test_data = test_pd[[feature_name, target_name]].copy()
    
    # Converting to categorical of desired form
    if type_chk == "str":
        logging.info("The data has the expected format of labels")

    else:
        logging.info("Converting the labels to required format")
        try:
            train_data[target_name] = train_data[target_name].map({1: 'suicide', 0: 'non-suicide'})
            test_data[target_name] = test_data[target_name].map({1: 'suicide', 0: 'non-suicide'})
            logging.info("Converted labels to the desired format")

        except Exception as e:
            logging.error(f"Could not convert labels to required format.. error : {e}")
            sys.exit(1)

    logging.info("Returning the training and testing dataframes")
    # Renaming the columns so that they match database
    train_data.rename(columns={feature_name: 'text_message', target_name: 'label'}, inplace=True)
    test_data.rename(columns={feature_name: 'text_message', target_name: 'label'}, inplace=True)

    return train_data, test_data

def connect_to_db(use_env = True):
    """
    Connect to the database and return the connection
    """

    logging.info("Connecting to the database from the inserter db")
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

def insert_into_database(table_name : str, DataFrame):
    """
    Function to connect to the database and push the dataframe to database
    table_name : str (Table name to push the data)
    DataFrame : pd.DataFrame (DataFrame to push into DB)
    conn : Connection to the DB
    """
    
    # Connecting to the database
    conn = connect_to_db()
    cursor  = conn.cursor()
    logging.info(f"Pushing data into the table {table_name}")

    # Starting to enter database
    cols = ",".join(DataFrame.columns)
    batch_size = 1000

    # Dropping null values in dataframe
    DataFrame = DataFrame.dropna()
    for start in range(0, len(DataFrame), batch_size):
        chunk = DataFrame.iloc[start:start + batch_size]
        values = [tuple(x) for x in chunk.to_numpy()]

        try:
            execute_values(
                cursor,
                f"INSERT INTO {table_name} ({cols}) VALUES %s",
                values
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            logging.error(f"Failed to insert chunk starting at row {start}: {e}")

    cursor.close()
    conn.close()

    logging.info(f"Pushing data into the table : {table_name}")
    return

# Main orchestration of the script
if __name__ == "__main__":
    # Pushing english dataset into the database
    logging.info("Starting the process for (en) Dataset")
    train_pd, test_pd = load_pandas_dataset(dataset_name=DATASET_1_NAME, feature_name="text", target_name="label", split=True)
    train_data, test_data = make_pd_database_pushable(train_pd=train_pd, test_pd=test_pd, feature_name="text", target_name="label", type_chk="str")
    insert_into_database(table_name="sd_en_train", DataFrame=train_data)
    insert_into_database(table_name="sd_en_test", DataFrame=test_data)

    # Pushing spanishdataset into the database
    logging.info("Starting the process for (sp) Dataset")
    train_pd, test_pd = load_pandas_dataset(dataset_name=DATASET_2_NAME, feature_name="Text", target_name="Label", split=True)
    train_data, test_data = make_pd_database_pushable(train_pd=train_pd, test_pd=test_pd, feature_name="Text", target_name="Label", type_chk="int")
    insert_into_database(table_name="sd_sp_train", DataFrame=train_data)
    insert_into_database(table_name="sd_sp_test", DataFrame=test_data)

    logging.info("Succesfull insertions of all tables in the database !!!")