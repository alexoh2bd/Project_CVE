# Tests written by Gemini 3 Pro on November 23, 2025
import requests
import time
import sys

# FIX: Use localhost for the client connection
# BASE_URL = "http://localhost:8080"
BASE_URL ="https://cve-api-image-499266163270.us-east1.run.app"
EXPECTED_VECTOR_LENGTH = 91 

def test_api_health():
    """Test that the API is reachable with retries"""
    print(f"Attempting to connect to {BASE_URL}...")
    for i in range(5):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                print(f"✓ API is reachable at {BASE_URL}")
                return
        except requests.exceptions.ConnectionError:
            print(f"  Attempt {i+1}/5: Waiting for API...")
            time.sleep(1)
    raise requests.exceptions.ConnectionError(f"Could not connect to {BASE_URL} after 5 attempts.")

def test_predict_valid_vector():
    """Test that a single correct vector returns 200 OK and correct structure"""
    # Wrap single vector in a list for batch format
    single_vector = [0.0] * EXPECTED_VECTOR_LENGTH
    payload = {"features": [single_vector]}
    
    response = requests.post(f"{BASE_URL}/predict", json=payload)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    json_data = response.json()
    
    # NEW: Check for 'batch_results' key instead of direct keys
    assert "batch_results" in json_data, "Response missing 'batch_results' key"
    results = json_data["batch_results"]
    assert len(results) == 1, "Expected exactly 1 result"
    
    # Check the first result
    first_pred = results[0]
    assert "predicted_class" in first_pred, "Result missing 'predicted_class'"
    assert "probability" in first_pred, "Result missing 'probability'"
    print("✓ test_predict_valid_vector passed")

def test_multiple():
    """Test that a batch of 3 vectors returns 3 results"""
    # Create a batch of 3 vectors
    payload = {"features": [[0.0] * EXPECTED_VECTOR_LENGTH for _ in range(3)]}
    
    response = requests.post(f"{BASE_URL}/predict", json=payload)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    json_data = response.json()
    
    assert "batch_results" in json_data
    results = json_data["batch_results"]
    
    # Verify we got 3 results back
    assert len(results) == 3, f"Expected 3 results, got {len(results)}"
    print("✓ test_multiple passed")

def test_predict_invalid_shape_short():
    """Test that a vector inside the batch that is too short is rejected"""
    # We send a batch containing ONE vector that is too short
    # Note the double brackets [[...]] to satisfy List[List] type
    short_vector = [0.0] * (EXPECTED_VECTOR_LENGTH - 1)
    payload = {"features": [short_vector]}
    
    response = requests.post(f"{BASE_URL}/predict", json=payload)
    
    assert response.status_code == 422, f"Expected 422, got {response.status_code}"
    # The error message from your validator should mention the index and length
    assert "Vector at index 0" in response.text, "Error message should specify index"
    print("✓ test_predict_invalid_shape_short passed")

def test_predict_invalid_type():
    """Test that strings instead of floats are rejected"""
    # Batch with string values
    payload = {"features": [["not a number"] * EXPECTED_VECTOR_LENGTH]}
    
    response = requests.post(f"{BASE_URL}/predict", json=payload)
    assert response.status_code == 422, f"Expected 422, got {response.status_code}"
    print("✓ test_predict_invalid_type passed")

if __name__ == "__main__":
    print(f"\n--- Testing API at {BASE_URL} ---")
    
    try:
        test_api_health()
        test_predict_valid_vector()
        test_multiple()
        test_predict_invalid_shape_short()
        test_predict_invalid_type()
        print("\n✅ All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Tip: Make sure you ran 'docker run -p 8080:8080 cve_api_image1'")
        sys.exit(1)