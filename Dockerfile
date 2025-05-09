FROM python:3.9-slim

WORKDIR /app

COPY autoscaler_api.py .
COPY replica_predictor_model.pkl .
COPY replica_scaler.pkl .

RUN pip install flask numpy joblib scikit-learn

EXPOSE 5000
CMD ["python", "autoscaler_api.py"]
