from sklearn.linear_model import LogisticRegression
import pickle
import sys
import os
import scipy.sparse
sys.path.append(os.path.join(os.getcwd(), "project","pdpipeline"))
from config import TRAIN_TEST_DIR, MODELS_DIR, LOGGER, API_MODELS_DIR
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import cross_val_score
import wandb
# Had partial assistance refining original script from ChatGPT-5: https://chatgpt.com/share/6924698d-3924-800c-afa0-ac254bf0f571

wandb.init(
    project="CVE-logreg-pipeline",
    config={     # Keeps track of your hyperparameters
        "model": "LogisticRegression",
        "solver": "lbfgs",
        "max_iter": 100,
        "cv_folds": 3
    }
)   

X_train = scipy.sparse.load_npz(f"{TRAIN_TEST_DIR}/X_train.npz")
X_test = scipy.sparse.load_npz(f"{TRAIN_TEST_DIR}/X_test.npz")

y_train = scipy.sparse.load_npz(f"{TRAIN_TEST_DIR}/y_train.npz").toarray()
y_test = scipy.sparse.load_npz(f"{TRAIN_TEST_DIR}/y_test.npz").toarray()

model = LogisticRegression()
cv_scores = cross_val_score(model,X_train, y_train, cv=3, scoring='roc_auc')
model.fit(X_train, y_train)
wandb.log({"cv_mean": cv_scores.mean(), "cv_std": cv_scores.std()})

preds = model.predict(X_test)
acc = accuracy_score(y_test, preds)
prec = precision_score(y_test, preds)
recall = recall_score(y_test, preds)
roc_auc = roc_auc_score(y_test,preds)
wandb.log({
    "accuracy": acc,
    "precision": prec,
    'recall_score': recall,
    "ROC_AUC": roc_auc
})

# Define the destination dirs for the pickled model
model_file= f'{MODELS_DIR}/logistic_regression_model.pkl'
api_file = f'{API_MODELS_DIR}/logistic_regression_model.pkl'

# Save the trained model to a file using pickle.dump()
with open(model_file, 'wb') as file:
    pickle.dump(model, file)
with open(api_file, 'wb') as file:
    pickle.dump(model, file)
LOGGER.info(f"Saved model to {api_file} and {model_file}")



# LOG artifacts to WandB
artifact = wandb.Artifact(
    name="logreg-model",
    type="model",
    description="Trained Logistic Regression model for CVE classification",
)

artifact.add_file(model_file)
artifact.add_file(api_file)
wandb.log_artifact(artifact)

wandb.finish()