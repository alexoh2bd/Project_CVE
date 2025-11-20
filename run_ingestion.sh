#!/bin/bash

echo "Running Ingestion Pipeline"
python3 project/pdpipeline/ingest.py

echo "Merging Ingested Files"
python3 project/pdpipeline/process.py

echo "Uploading main feature dataset to GCP BigQuery database"
# python3 project/pdpipeline/bigqueryscript.py

