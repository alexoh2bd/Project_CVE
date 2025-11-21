from google.cloud import bigquery
import os
import csv, json
import gc 
# from tqdm.auto import tqdm
from config import MERGED_DATA_DIR, LOGGER
from tqdm.auto import tqdm


# OPTION A: Point to the JSON key file path explicitly
# Ideally, set this in your environment variables, but this works for testing.
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"

def send_to_bigQuery(data_rows):
    """
    Ingests a list of dictionaries into BigQuery.
    """
    # Initialize the client
    client = bigquery.Client()
    table_id = "ml-pipeline-lab-478617.cve.ML_features"
    batch_size = 1000
    total = len(data_rows)

    for start in tqdm(range(0, total, batch_size)):
        end = start + batch_size
        batch = data_rows[start:end]

        errors = client.insert_rows_json(table_id, batch)

        if errors:
            LOGGER.error(f"BigQuery yeeted this batch: {errors}")

    LOGGER.info(f"Uploaded {total} new rows to the BigQuery Table.")


# Example usage
if __name__ == "__main__":
    # Data must match the schema you defined in Phase 1
    # data = []
    csv_file_path = (f"{MERGED_DATA_DIR}/Main1.csv")
    LOGGER.info(f"Loading {csv_file_path}")
    with open(csv_file_path, mode='r', newline='', encoding='utf-8') as csvfile:
        # Use DictReader to read CSV rows as dictionaries
        data = list(csv.DictReader(csvfile))
            # for i, row in enumerate(csv_reader):
            #     data.append(row)
            # # row.pop("")
            # if i < 10:
            #     data.append(row)
            # else: 
            #     break
    
    send_to_bigQuery(data)
    del data
    gc.collect()
