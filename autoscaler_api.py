from flask import Flask, request, jsonify
import joblib
import numpy as np

# Load model and scaler
model = joblib.load("replica_predictor_model.pkl")
scaler = joblib.load("replica_scaler.pkl")

# Feature order as trained
features_order = [
    "Requests/sec", "Size/request", "Concurrent requests",
    "10th percentile", "50th percentile", "75th percentile",
    "90th percentile", "99th percentile", "error_rate"
]

app = Flask(__name__)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        x = np.array([[data[f] for f in features_order]])
        x_scaled = scaler.transform(x)
        y_pred = model.predict(x_scaled)
        replicas = int(max(1, round(y_pred[0])))  # Ensure >= 1
        return jsonify({"replicas": replicas})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
