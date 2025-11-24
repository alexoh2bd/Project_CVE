from pathlib import Path
import os
import joblib
import scipy.sparse
import pandas as pd
import typer

from google.cloud import bigquery
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from config import TRAIN_TEST_DIR, LOGGER

# Had partial assistance with ChatGPT-5: https://chatgpt.com/share/6923f960-dc78-800c-8acc-11ae8e1589d8
app = typer.Typer()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"


# ML cleaning & splitting
def clean_ml(df: pd.DataFrame):
    """
    Convert timestamps, prepare features, build preprocessor,
    return processed train/test matrices + the preprocessor.
    """

    #  datetime aging 
    for col in ["published_date", "last_modified_date"]:
        if col in df:
            df[col] = pd.to_datetime(df[col], utc=True)
            now = pd.Timestamp.now(tz="UTC")
            df[col + "_age_days"] = (now - df[col]).dt.days

    # y targets 
    y = df["exploited"].astype(int)

    # numeric 
    numeric_cols = [
        "base_score", "exploitability_score", "impact_score",
        "published_date_age_days", "last_modified_date_age_days"
    ]
    numeric_cols = [c for c in numeric_cols if c in df]

    #  categoricals 
    cat_cols = [
        "attack_vector", "attack_complexity", "privileges_required",
        "user_interaction", "scope", "confidentiality_impact",
        "integrity_impact", "availability_impact", "cwe_id",
        "base_severity"
    ]
    cat_cols = [c for c in cat_cols if c in df]

    X = df[numeric_cols + cat_cols]

    #  preprocessing 
    numeric_transformer = Pipeline(
        steps=[("imputer", SimpleImputer(strategy="median"))]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore"))
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_cols),
            ("cat", categorical_transformer, cat_cols),
        ]
    )

    # Fit-transform
    X_proc = preprocessor.fit_transform(X)

    # y sparse
    y_sparse = scipy.sparse.csr_matrix(y.values.reshape(-1, 1))

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_proc,
        y_sparse,
        test_size=0.2,
        stratify=y_sparse.toarray(),
        random_state=42,
    )

    return X_train, X_test, y_train, y_test, preprocessor, numeric_cols, cat_cols

# utils to save data and processors
def save_sparse_matrix(path: Path, matrix):
    scipy.sparse.save_npz(str(path), matrix)


def save_splits(output_dir: Path, X_train, X_test, y_train, y_test):
    output_dir.mkdir(parents=True, exist_ok=True)

    save_sparse_matrix(output_dir / "X_train.npz", X_train)
    save_sparse_matrix(output_dir / "X_test.npz", X_test)
    save_sparse_matrix(output_dir / "y_train.npz", y_train)
    save_sparse_matrix(output_dir / "y_test.npz", y_test)


def save_metadata(output_dir: Path, preprocessor, numeric_cols, cat_cols):
    joblib.dump(preprocessor, output_dir / "preprocessor.joblib")
    joblib.dump(
        {"numeric_cols": numeric_cols, "cat_cols": cat_cols},
        output_dir / "feature_metadata.joblib",
    )


# MAIN
@app.command()
def main(output_path: Path = TRAIN_TEST_DIR):
    client = bigquery.Client()

    query = """
        SELECT *
        FROM `ml-pipeline-lab-478617.cve.ML_features`
    """
    LOGGER.info(f"Querying...\n{query}")

    df = client.query_and_wait(query).to_dataframe()
    LOGGER.info(f"Query Complete! Rows={len(df)}")

    (
        X_train, X_test, y_train, y_test,
        preprocessor, numeric_cols, cat_cols
    ) = clean_ml(df)

    LOGGER.info("Saving train/test splits...")
    save_splits(output_path, X_train, X_test, y_train, y_test)

    LOGGER.info("Saving metadata + preprocessor...")
    save_metadata(output_path, preprocessor, numeric_cols, cat_cols)

    LOGGER.info("Saving Complete!")


if __name__ == "__main__":
    app()
