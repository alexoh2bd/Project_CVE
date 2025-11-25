import json
import os
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
import requests
import streamlit as st


EXPECTED_VECTOR_LENGTH = 91
PREPROCESSOR_PATH = os.getenv("PREPROCESSOR_PATH", "data/traintest/preprocessor.joblib")
FEATURE_META_PATH = os.getenv("FEATURE_META_PATH", "data/traintest/feature_metadata.joblib")
DEFAULT_API_URL = os.getenv(
    "API_URL",
    "https://cve-api-image-499266163270.us-east1.run.app/predict",
)


def build_sample_payload(batch_size: int = 2) -> Dict[str, List[List[float]]]:
    """Return a sample payload with the right shape for quick testing."""
    vector = [0.0] * EXPECTED_VECTOR_LENGTH
    return {"features": [vector for _ in range(batch_size)]}


def validate_payload(raw_text: str) -> Dict[str, Any]:
    """Parse and validate that the payload matches the API contract."""
    data = json.loads(raw_text)
    if not isinstance(data, dict):
        raise ValueError("Payload must be a JSON object with a 'features' key.")

    features = data.get("features")
    if not isinstance(features, list) or not features:
        raise ValueError("The 'features' field must be a non-empty list of vectors.")

    clean_vectors: List[List[float]] = []
    for index, vector in enumerate(features):
        if not isinstance(vector, list):
            raise ValueError(f"Vector at index {index} is not a list.")
        if len(vector) != EXPECTED_VECTOR_LENGTH:
            raise ValueError(
                f"Vector at index {index} has length {len(vector)}, "
                f"expected {EXPECTED_VECTOR_LENGTH}."
            )
        try:
            clean_vectors.append([float(x) for x in vector])
        except Exception:
            raise ValueError(f"Vector at index {index} contains non-numeric values.")

    return {"features": clean_vectors}


def call_predict(api_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    response = requests.post(api_url, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


@st.cache_resource(show_spinner=False)
def load_encoder() -> Tuple[Any, Dict[str, Any], Dict[str, List[str]]]:
    """Load the trained preprocessor + metadata and derive categorical options."""
    try:
        preprocessor = joblib.load(PREPROCESSOR_PATH)
        meta = joblib.load(FEATURE_META_PATH)
    except Exception:
        return None, None, {}

    cat_options: Dict[str, List[str]] = {}
    features = meta.get("onehot_features", [])
    for col in meta.get("cat_cols", []):
        prefix = f"cat__{col}_"
        col_vals = [f[len(prefix):] for f in features if f.startswith(prefix)]
        cat_options[col] = sorted(col_vals)
    return preprocessor, meta, cat_options


def build_vector_from_form(
    preprocessor: Any,
    numeric_inputs: Dict[str, float],
    cat_inputs: Dict[str, str],
) -> List[float]:
    """Build a single 91-length vector using the fitted preprocessor."""
    row = {}
    row.update(numeric_inputs)
    row.update(cat_inputs)
    df = pd.DataFrame([row])
    arr = preprocessor.transform(df)
    if hasattr(arr, "toarray"):
        arr = arr.toarray()
    vec = np.asarray(arr)[0].tolist()
    if len(vec) != EXPECTED_VECTOR_LENGTH:
        raise ValueError(f"Encoded vector length {len(vec)} != {EXPECTED_VECTOR_LENGTH}")
    return vec


def render_results(results: List[Dict[str, Any]], risk_threshold: float):
    table = []
    for idx, r in enumerate(results):
        pred_class = r.get("predicted_class")
        prob = r.get("probability")
        label = "Likely Exploited" if pred_class == 1 else "Not Exploited"
        risk = "High" if (pred_class == 1 and prob is not None and prob >= risk_threshold) else "Low"
        if prob is None:
            score_label = None
        elif pred_class == 1:
            score_label = f"Confidence (Exploited): {prob * 100:.1f}%"
        else:
            score_label = f"Confidence (Not Exploited): {prob * 100:.1f}%"
        table.append(
            {
                "#": idx + 1,
                "label": label,
                "probability": score_label,
                "risk_flag": risk,
            }
        )

    st.dataframe(table, use_container_width=True, hide_index=True)

    for idx, r in enumerate(results):
        prob = r.get("probability")
        pred_class = r.get("predicted_class")
        if prob is None:
            continue
        color = "red" if (pred_class == 1 and prob >= risk_threshold) else "green"
        score_text = (
            f"Confidence (Exploited): {prob*100:.1f}%"
            if pred_class == 1
            else f"Confidence (Not Exploited): {prob*100:.1f}%"
        )
        st.markdown(
            f"<div style='padding:8px;margin:4px 0;border:1px solid #333;border-radius:6px;"
            f"background:#111;'>Item {idx+1}: "
            f"<span style='color:{color};font-weight:600;'>{score_text}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )


st.set_page_config(page_title="CVEye - Exploit Risk", page_icon="🛡️", layout="wide")

# Simple dark theme overrides
st.markdown(
    """
    <style>
    body, .main { background: #000; color: #f5f5f5; }
    .stApp { background: #000; color: #f5f5f5; }
    .stTextInput>div>div>input, textarea, .stTextArea textarea {
        background: #111 !important; color: #f5f5f5 !important; border: 1px solid #333;
    }
    .stButton>button {
        background: linear-gradient(90deg, #1f1f1f, #111);
        color: #f5f5f5;
        border: 1px solid #444;
        border-radius: 8px;
        padding: 0.6rem 1.1rem;
        font-weight: 600;
    }
    .stButton>button:hover { border: 1px solid #888; }
    .stSlider, .stSelectbox label { color: #f5f5f5; }
    .stDataFrame { color: #f5f5f5; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("CVEye Exploit Risk")
st.caption(
    "Exploit likelihood hinges on how a vulnerability scores on access, complexity, impact, and history. "
    "We take your CVSS-style inputs (scores + categories), expand them into the 91 encoded features the model was trained on, "
    "and return the predicted exploitation risk. Set realistic inputs for a CVE, submit, and read the predicted class and probability."
)

# Defaults from env; threshold adjustable inline
api_url = DEFAULT_API_URL
risk_threshold = st.slider(
    "High-risk threshold (probability)",
    min_value=0.1,
    max_value=0.9,
    value=0.6,
    step=0.05,
)

st.markdown(
    "Enter scores and choose categories; we encode them into the 91-length vector the model expects. "
    "Run a prediction to see the class (Not Exploited / Likely Exploited) and probability."
)

if "payload_text" not in st.session_state:
    st.session_state.payload_text = json.dumps(build_sample_payload(), indent=2)

preprocessor, meta, cat_options = load_encoder()

st.subheader("Form builder (single sample)")
if not preprocessor:
    st.info("Preprocessor metadata not found. Form builder disabled. Keep using raw JSON below.")
else:
    num_cols = meta.get("numeric_cols", [])
    cat_cols = meta.get("cat_cols", [])

    # Default numeric values
    defaults = {
        "base_score": 5.0,
        "exploitability_score": 5.0,
        "impact_score": 5.0,
        "published_date_age_days": 365.0,
        "last_modified_date_age_days": 180.0,
    }

    c1, c2 = st.columns(2)
    with c1:
        base_score = st.slider("Base score (0-10)", 0.0, 10.0, defaults["base_score"], 0.1)
        exploitability_score = st.slider("Exploitability score (0-10)", 0.0, 10.0, defaults["exploitability_score"], 0.1)
        impact_score = st.slider("Impact score (0-10)", 0.0, 10.0, defaults["impact_score"], 0.1)
    with c2:
        published_age = st.slider("Published age (days)", 0.0, 5000.0, defaults["published_date_age_days"], 1.0)
        modified_age = st.slider("Last modified age (days)", 0.0, 5000.0, defaults["last_modified_date_age_days"], 1.0)

    # Categorical selectors (selectbox per column)
    cat_inputs = {}
    for col in cat_cols:
        options = cat_options.get(col, [])
        if not options:
            continue
        # Display friendly label
        label = col.replace("_", " ").title()
        default_idx = 0
        cat_inputs[col] = st.selectbox(label, options, index=default_idx, key=f"cat_{col}")

    form_batch = st.number_input("Duplicate this sample into batch size", min_value=1, max_value=10, value=1, step=1)

    if st.button("Build from form and send", type="primary"):
        numeric_inputs = {
            "base_score": base_score,
            "exploitability_score": exploitability_score,
            "impact_score": impact_score,
            "published_date_age_days": published_age,
            "last_modified_date_age_days": modified_age,
        }
        try:
            vector = build_vector_from_form(preprocessor, numeric_inputs, cat_inputs)
            payload = {"features": [vector for _ in range(int(form_batch))]}

            with st.spinner("Calling API..."):
                response = call_predict(api_url, payload)
                results = response.get("batch_results", [])
                if not isinstance(results, list):
                    raise ValueError("Response missing 'batch_results' list.")

                st.success(f"Received {len(results)} predictions.")
                render_results(results, risk_threshold)
                with st.expander("Raw response"):
                    st.json(response)
                with st.expander("Payload sent"):
                    st.json(payload)
        except Exception as exc:
            st.error(f"Form build or API call failed: {exc}")

st.subheader("Prediction request (raw JSON)")
st.text_area(
    "Payload (JSON)",
    key="payload_text",
    height=260,
    help="Must include 'features': [[...], [...]] with 91 floats per vector. Use 'Generate sample payload' for a valid shape.",
)

col1, col2 = st.columns(2)
with col1:
    batch_size = st.number_input("Sample batch size", min_value=1, max_value=5, value=2, step=1)
with col2:
    if st.button("Generate sample payload"):
        st.session_state.payload_text = json.dumps(build_sample_payload(int(batch_size)), indent=2)

if st.button("Send to /predict", type="primary"):
    if not api_url:
        st.error("Please set the predict endpoint URL.")
    else:
        try:
            payload = validate_payload(st.session_state.payload_text)
        except Exception as exc:
            st.error(f"Invalid payload: {exc}")
        else:
            with st.spinner("Calling API..."):
                try:
                    response = call_predict(api_url, payload)
                    results = response.get("batch_results", [])
                    if not isinstance(results, list):
                        raise ValueError("Response missing 'batch_results' list.")

                    st.success(f"Received {len(results)} predictions.")

                    table = []
                    for idx, r in enumerate(results):
                        pred_class = r.get("predicted_class")
                        prob = r.get("probability")
                        label = "Likely Exploited" if pred_class == 1 else "Not Exploited"
                        risk = "High" if (pred_class == 1 and prob is not None and prob >= risk_threshold) else "Low"
                        score_pct = f"{prob * 100:.1f}%" if prob is not None else None
                        table.append(
                            {
                                "#": idx + 1,
                                "label": label,
                                "probability_pct": score_pct,
                                "risk_flag": risk,
                            }
                        )

                    st.dataframe(table, use_container_width=True, hide_index=True)

                    # Simple "vulnerability score" badge per item
                    for idx, r in enumerate(results):
                        prob = r.get("probability")
                        pred_class = r.get("predicted_class")
                        if prob is None:
                            continue
                        color = "red" if (pred_class == 1 and prob >= risk_threshold) else "green"
                        st.markdown(
                            f"<div style='padding:8px;margin:4px 0;border:1px solid #333;border-radius:6px;"
                            f"background:#111;'>Item {idx+1}: "
                            f"<span style='color:{color};font-weight:600;'>Vulnerability Score: {prob*100:.1f}%</span>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )

                    with st.expander("Raw response"):
                        st.json(response)
                    with st.expander("What are the 91 features?"):
                        st.markdown(
                            "- Start features: CVSS scores/ages (numeric) + categorical factors like attack vector, complexity, privileges, user interaction, scope, confidentiality/integrity/availability impact, CWE ID, base severity.\n"
                            "- The 91-length vector is those columns after one-hot encoding (each category becomes multiple binary columns), plus the numeric fields.\n"
                            "- The API expects the already-encoded 91-length vectors; the UI here relays them to the model."
                        )
                except Exception as exc:
                    st.error(f"API call failed: {exc}")
