from sklearn.linear_model import LogisticRegression
import pickle
import sys
import os
import scipy.sparse
sys.path.append(os.path.join(os.getcwd(), "project","pdpipeline"))
from config import TRAIN_TEST_DIR, MODELS_DIR, LOGGER
# import pandas as pd
from sklearn.metrics import accuracy_score, precision_score




X_train = scipy.sparse.load_npz(f"{TRAIN_TEST_DIR}/X_train.npz")
X_test = scipy.sparse.load_npz(f"{TRAIN_TEST_DIR}/X_test.npz")

y_train = scipy.sparse.load_npz(f"{TRAIN_TEST_DIR}/y_train.npz")
y_test = scipy.sparse.load_npz(f"{TRAIN_TEST_DIR}/y_test.npz")

model = LogisticRegression()
model.fit(X_train, y_train.toarray())
preds = model.predict(X_test)
acc = accuracy_score(preds,y_test.toarray())
prec = precision_score(preds,y_test.toarray())
LOGGER.info(f"Fit a Logistic Regression model to training data with {acc*100}%  accuracy and {prec*100}% precision.")
# Define the filename for the pickled model
filename = f'{MODELS_DIR}/logistic_regression_model.pkl'

# Save the trained model to a file using pickle.dump()
with open(filename, 'wb') as file:
    pickle.dump(model, file)

LOGGER.info(f"Saved model to {filename}")


