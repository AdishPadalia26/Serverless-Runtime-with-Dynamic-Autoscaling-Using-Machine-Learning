# 🚀 Serverless Runtime with Dynamic Autoscaling Using Machine Learning and Kubernetes

A Kubernetes-based serverless autoscaling platform that integrates **OpenFaaS**, **Horizontal Pod Autoscaler (HPA)**, **machine learning-based predictive scaling**, and real-time traffic simulation using `hey`. The system forecasts future traffic and scales functions proactively to reduce latency and cold starts.

---

## 📌 Project Overview

This project explores a hybrid autoscaling system combining:
- Reactive scaling (via Kubernetes HPA)
- Predictive ML-based scaling (Random Forest)
- OpenFaaS functions deployed on Kubernetes
- Real-time testing with `hey`
- Visualization with Prometheus + Grafana

---

## 🧰 Tools & Technologies

- **Kubernetes** + **Minikube**
- **OpenFaaS**
- **Helm**
- **Prometheus** & **Grafana**
- **Python** (Flask, Scikit-learn)
- **Docker**
- **Horizontal Pod Autoscaler (HPA)**
- **hey** (load testing)

---

## 🧱 Architecture

```
┌─────────────┐        ┌────────────┐        ┌─────────────┐
│   hey Tool  ├───────▶│  OpenFaaS  ├───────▶│ Kubernetes  │
└─────────────┘        └─────┬──────┘        └──────┬──────┘
                             ▼                       ▼
                 ┌────────────────────┐     ┌────────────────────┐
                 │   Prometheus       │     │   ML Predictor API │
                 └────────────────────┘     └────────────────────┘
```

---

## 📦 Repository Structure

```
├── flask-api/                  # Flask server for ML model
│   ├── autoscaler_model.pkl    # Trained Random Forest model
│   ├── scaler.pkl              # Corresponding StandardScaler
│   └── app.py                  # Flask API
├── Dockerfile                  # Container for Flask API
├── deployment.yaml             # K8s deployment for predictor API
├── gen.py                      # Script for generating traffic
├── autoscaler_log.csv          # Logs of predictions
└── README.md                   # This file
```

---

## 🧪 Phase-by-Phase Execution

---

### ✅ Phase 1: Setup & Infrastructure

```bash
# Install kubectl
curl -LO "<kubectl-url>"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
kubectl version --client

# Install Minikube
curl -LO "<minikube-url>"
sudo install minikube-linux-amd64 /usr/local/bin/minikube
minikube start
kubectl get nodes
kubectl get pods -A

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
helm version

# Deploy Prometheus and Grafana
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus prometheus-community/kube-prometheus-stack
minikube service grafana --url
```

---

### ✅ Phase 2: Reactive Autoscaling with OpenFaaS + HPA

```bash
# Install OpenFaaS CLI
curl -sSL https://cli.openfaas.com | sudo sh
faas-cli version

# Set up namespaces
kubectl apply -f https://raw.githubusercontent.com/openfaas/faas-netes/master/namespaces.yml

# Install OpenFaaS via Helm
helm repo add openfaas https://openfaas.github.io/faas-netes/
helm repo update
helm install openfaas openfaas/openfaas \
  --namespace openfaas \
  --set functionNamespace=openfaas-fn \
  --set generateBasicAuth=true \
  --set serviceType=NodePort

# Login
PASSWORD=$(kubectl get secret -n openfaas basic-auth -o jsonpath="{.data.basic-auth-password}" | base64 --decode)
faas-cli login --username admin --password $PASSWORD

# Create, build and deploy a function
faas-cli new hello-python --lang python3
faas-cli build -f hello-python.yml
faas-cli push -f hello-python.yml
faas-cli deploy -f hello-python.yml

# Enable HPA
kubectl autoscale deployment hello-python --cpu-percent=50 --min=1 --max=10 -n openfaas-fn
```

---

### ✅ Phase 3: Predictive ML Autoscaling

- Metrics collected via `hey` + script
- Features extracted: latency percentiles, error rate, etc.
- Feature engineering:  
  `((Status 500 / Status 200) + Status 500)`
- Model: `RandomForestRegressor`
- Accuracy: **93.1%**
- Exported model: `autoscaler_model.pkl`  
- Exported scaler: `scaler.pkl`

---

### ✅ Phase 4: ML Model Served via Flask + Docker

```bash
# Build Docker image
docker build -t ml-predictor .

# Tag and push
docker tag ml-predictor <dockerhub-username>/ml-predictor:latest
docker push <dockerhub-username>/ml-predictor:latest

# Deploy on Kubernetes
kubectl apply -f deployment.yaml
```

---

### ✅ Phase 5: Autoscaling Script Using hey + ML

```bash
# Run autoscaling loop
python3 autoscale_predict_independent.py
```

This:
- Simulates traffic using `hey`
- Parses output
- Sends features to `/predict`
- Gets predicted replicas
- Scales deployment using `kubectl`
- Logs prediction in `autoscaler_log.csv`

---

## 📈 Results

- 🚀 Reduced cold-start latency by ~15%
- 📉 Smoother CPU usage graphs
- 📊 Better anticipatory scaling vs HPA

---

## 🔮 Future Work

- Use LSTM/Transformer models for higher accuracy
- Migrate to GPU/TPU-backed environments
- Integrate Prometheus for live time-series inputs
- Model compression for edge deployment

---

## 📚 References

See [Report PDF](./Design%20of%20Internet%20Services_Project_Report.pdf) for more detailed analysis.
