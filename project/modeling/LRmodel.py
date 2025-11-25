from pathlib import Path
import os
import pickle
import sys

import scipy.sparse
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import cross_val_score
import wandb

sys.path.append(os.path.join(os.getcwd(), "project", "pdpipeline"))
from config import TRAIN_TEST_DIR, MODELS_DIR, LOGGER, API_MODELS_DIR  # noqa: E402
from project.config_loader import get_config  # noqa: E402


# Had partial assistance refining original script from ChatGPT-5: https://chatgpt.com/share/6924698d-3924-800c-afa0-ac254bf0f571

CONFIG = get_config()
TRAINING_CFG = CONFIG.get("training", {})


def _resolve_model_path(value: str) -> Path:
    default_path = Path(MODELS_DIR) / "logistic_regression_model.pkl"
    if not value:
        return default_path
    candidate = Path(value)
    if not candidate.is_absolute():
        return default_path.parent / candidate
    return candidate


wandb.init(
    project=TRAINING_CFG.get("experiment_name", "CVE-logreg-pipeline"),
    name=TRAINING_CFG.get("run_name", "baseline-logreg"),
    config={
        "model": "LogisticRegression",
        "solver": "lbfgs",
        "max_iter": 100,
        "cv_folds": 3,
    },
)

# Load sparse splits
X_train = scipy.sparse.load_npz(f"{TRAIN_TEST_DIR}/X_train.npz")
X_test = scipy.sparse.load_npz(f"{TRAIN_TEST_DIR}/X_test.npz")
y_train = scipy.sparse.load_npz(f"{TRAIN_TEST_DIR}/y_train.npz").toarray()
y_test = scipy.sparse.load_npz(f"{TRAIN_TEST_DIR}/y_test.npz").toarray()

# Train & log
model = LogisticRegression()
cv_scores = cross_val_score(model, X_train, y_train, cv=3, scoring="roc_auc")
model.fit(X_train, y_train)
wandb.log({"cv_mean": cv_scores.mean(), "cv_std": cv_scores.std()})

preds = model.predict(X_test)
acc = accuracy_score(y_test, preds)
prec = precision_score(y_test, preds)
recall = recall_score(y_test, preds)
roc_auc = roc_auc_score(y_test, preds)
wandb.log(
    {
        "accuracy": acc,
        "precision": prec,
        "recall_score": recall,
        "ROC_AUC": roc_auc,
    }
)

# Save the trained model to disk
model_file = _resolve_model_path(TRAINING_CFG.get("model_path", ""))
api_file = Path(API_MODELS_DIR) / model_file.name
with open(model_file, "wb") as file:
    pickle.dump(model, file)
with open(api_file, "wb") as file:
    pickle.dump(model, file)
LOGGER.info(f"Saved model to {api_file} and {model_file}")

# Log artifacts to WandB
artifact = wandb.Artifact(
    name=TRAINING_CFG.get("artifact_name", "logreg-model"),
    type="model",
    description="Trained Logistic Regression model for CVE classification",
)
artifact.add_file(str(model_file))
artifact.add_file(str(api_file))
wandb.log_artifact(artifact)

wandb.finish()
