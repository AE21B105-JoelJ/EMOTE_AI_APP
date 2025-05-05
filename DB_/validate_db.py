# Validate DB script -- runs after the db container is healthy and checks whether the tables are created #

# Importing the necessary libraries needed 
import psycopg2
import os
import sys
import logging
import time


# Setting up the log file
log_file = "/var/log/db.log"
logging.basicConfig(
    level = logging.DEBUG,
    format = "%(asctime)s - %(levelname)s - %(message)s",
    handlers = [
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

logger.info("DB Container has started !!! Now in validation script")

try:
    # Getting the Environment variables
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'postgres')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', 5432))
    logging.info("Setting up the environment variables successful")

except Exception as e:
    logging.error("Environment variables setup unsuccessful !!")
    sys.exit(1)
    
# Setting up some configurations for the db connection
MAX_RETRIES = 30
SLEEP_TIME = 2
attempts = 0
conn = None

while attempts < MAX_RETRIES:
    try:
        logging.info("Connecting to the database")
        # Trying connection to the database
        conn = psycopg2.connect(
            dbname = POSTGRES_DB,
            user = POSTGRES_USER,
            password = POSTGRES_PASSWORD,
            host = POSTGRES_HOST,
            port = POSTGRES_PORT
        )
        # If successful break out of the loop
        break

    except psycopg2.OperationalError as e:
        logging.error(f" Failed to connect to the database, error : {e}")
        time.sleep(SLEEP_TIME)
        attempts += 1

# If still failed connection to the database
if conn is None:
    logging.critical("Failed to connect to the database !!!")
    sys.exit(1)

# cursor definition
cursor = conn.cursor()

# Checking if the tables exist
cursor.execute("""SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'sd_en_train');""")
table_1_exists = cursor.fetchone()[0]


cursor.execute("""SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'sd_en_test');""")
table_2_exists = cursor.fetchone()[0]

cursor.execute("""SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'sd_sp_train');""")
table_3_exists = cursor.fetchone()[0]

cursor.execute("""SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'sd_sp_test');""")
table_4_exists = cursor.fetchone()[0]

cursor.execute("""SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'sd_feed');""")
table_5_exists = cursor.fetchone()[0]

cursor.execute("""SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'feedback');""")
table_6_exists = cursor.fetchone()[0]

# Check for the existence of the table else create one
if not table_1_exists:
    logging.info("Table 1 (SD_en_train) does not exist! Creating...")
    cursor.execute("""CREATE TABLE IF NOT EXISTS SD_en_train (
            id SERIAL PRIMARY KEY,
            text_message TEXT  NOT NULL,
            label TEXT  NOT NULL
            );""")
    conn.commit()

if not table_2_exists:
    logging.info("Table 2 (SD_en_test) does not exist! Creating...")
    cursor.execute("""CREATE TABLE IF NOT EXISTS SD_en_test (
            id SERIAL PRIMARY KEY,
            text_message TEXT  NOT NULL,
            label TEXT  NOT NULL
            );""")
    conn.commit()

if not table_3_exists:
    logging.info("Table 3 (SD_sp_train) does not exist! Creating...")
    cursor.execute("""CREATE TABLE IF NOT EXISTS SD_sp_train (
            id SERIAL PRIMARY KEY,
            text_message TEXT  NOT NULL,
            label TEXT  NOT NULL
            );""")
    conn.commit()

if not table_4_exists:
    logging.info("Table 4 (SD_sp_test) does not exist! Creating...")
    cursor.execute("""CREATE TABLE IF NOT EXISTS SD_sp_test (
            id SERIAL PRIMARY KEY,
            text_message TEXT  NOT NULL,
            label TEXT  NOT NULL
            );""")
    conn.commit()

if not table_5_exists:
    logging.info("Table 5 (SD_feed) does not exist! Creating...")
    cursor.execute("""CREATE TABLE IF NOT EXISTS SD_feed (
            id SERIAL PRIMARY KEY,
            text_message TEXT  NOT NULL,
            label TEXT  NOT NULL
            );""")
    conn.commit()

if not table_6_exists:
    logging.info("Table 6 (Feedback) does not exist! Creating...")
    cursor.execute("""CREATE TABLE IF NOT EXISTS Feedback (
            id SERIAL PRIMARY KEY,
            rating REAL NOT NULL,
            text_message TEXT  NOT NULL
            );""")
    conn.commit()

logging.info("All the database tables are validated !!!")

# Closing the connection
cursor.close()
conn.close()