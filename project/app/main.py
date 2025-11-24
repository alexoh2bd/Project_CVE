from fastapi import FastAPI, HTTPException
from .schemas import VectorInput, PredictionOutput, BatchPredictionOutput
import numpy as np
import pickle
from .config.config import logger, SETTINGS
import os
# had partial assistance from Gemini 3 Pro: https://gemini.google.com/app/9bd9bd0bef74a364


app = FastAPI(title=SETTINGS.PROJECT_NAME)

@app.get("/health")
def health_check():
    return {"status": "ok", "env": SETTINGS.ENVIRONMENT}

@app.post("/predict", response_model=BatchPredictionOutput)
def predict(payload: VectorInput):
    try:
        # Convert list of lists to 2D Numpy Array
        X = np.array(payload.features)
        
        logger.info(f"BATCH VECTOR RECEIVED. Shape: {X.shape}")

        model_path = "./models/logistic_regression_model.pkl"
        
        # Check if model exists
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}")

        # Load model (Note: For production, load this once at startup, not every request)
        with open(model_path, 'rb') as file:
            model = pickle.load(file)
    
        # Make Batch Predictions
        predictions = model.predict(X) 
        pred_probs_all = model.predict_proba(X) 

        results_list = []

        # Iterate through the batch results
        for i, pred_class in enumerate(predictions):
            # Get the probability specific to the predicted class
            prob = pred_probs_all[i][pred_class]
            
            results_list.append(
                PredictionOutput(
                    predicted_class=int(pred_class),
                    probability=float(prob)
                )
            )

        # logger.info(f"Batch predictions generated: {len(results_list)} items")

    except Exception as e:
        logger.error(f"Prediction Error: {e}")
        raise HTTPException(status_code=400, detail=f"Error processing array: {str(e)}")
        
    return BatchPredictionOutput(batch_results=results_list)