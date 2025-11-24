#!/bin/bash

echo "Running Ingestion Pipeline"
python3 project/pdpipeline/ingest.py

echo "Merging Ingested Files"
python3 project/pdpipeline/process.py

echo "Uploading main feature dataset to GCP BigQuery database"
python3 project/pdpipeline/bigqueryscript.py

echo "Querying Training Data from BigQuery and Preprocessing" 
python3 project/pdpipeline/mlpipeline.py

echo "Fitting, Testing, and Saving Logistic Regression Model on CVE Train/Test data"
python3 project/modeling/LRmodel.py
