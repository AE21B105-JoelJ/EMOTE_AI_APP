#!/bin/bash
set -e

POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"

docker-entrypoint.sh postgres &

until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
    echo "Waiting for initiation !!!"
    sleep 5
done

/db_/venv/bin/python3 /db_/validate_db.py 

echo "Checking if data is already present"

DATA_EXISTS=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT EXISTS (SELECT 1 FROM sd_en_train LIMIT 1);")

if [ "$DATA_EXISTS" = "t" ]; then
    echo "Data already exists in sd_en_train. Skipping insertion."
else
    echo "No data found. Inserting now..."
    /db_/venv/bin/python3 /db_/Insert_db.py
fi

wait