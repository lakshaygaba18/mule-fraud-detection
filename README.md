# 🛡️ MuleShield

### AI-Powered Mule Fraud Detection & Transaction Network Intelligence

> **Detect suspicious accounts. Trace the network. Explain the risk. Monitor when fraud behavior changes.**

MuleShield is an end-to-end fraud intelligence platform designed to identify suspicious mule accounts by combining **GraphSAGE-based graph learning, transaction-network analysis, behavioral explainability, risk propagation, adversarial robustness testing, and model-drift monitoring** into an investigator-oriented dashboard.

The goal is not simply to predict whether an account is fraudulent, but to provide investigators with the **context behind the prediction** and the surrounding transaction network.

---

## 🚀 Quick Links

| Component | Details |
|---|---|
| 🌐 Frontend | Flutter Web investigation dashboard |
| 🤖 ML Service | `https://mule-fraud-ml.onrender.com` |
| ☕ Backend | Spring Boot REST API |
| 💻 Source Code | `https://github.com/lakshaygaba18/mule-fraud-detection` |

### ML Service Health

The production ML service exposes:

```text
https://mule-fraud-ml.onrender.com
```

Example response:

```json
{
  "service": "Fraud Detection ML Service",
  "status": "running",
  "mode": "production"
}
```

---

# 🎯 Problem Statement

Traditional fraud detection systems often evaluate transactions or accounts independently.

Mule accounts, however, frequently operate as part of a **transaction network**.

```text
Account A
    │
    ▼
Mule Account
    │
    ├──────────► Account C
    │
    └──────────► Account D
```

A suspicious account may therefore be difficult to identify using only individual transaction features.

For example, an account that:

- receives money from many accounts,
- quickly forwards the money,
- has a high pass-through ratio,
- participates in multiple transaction paths,
- or acts as a bridge between suspicious accounts

may be more meaningful when viewed as part of a network.

MuleShield combines **account-level behavioral features with graph-based learning and network intelligence** to provide a broader view of suspicious financial activity.

---

# 💡 Core Idea

A traditional system may answer:

> **"Is this account suspicious?"**

MuleShield attempts to answer:

> **"Why is this account suspicious, who is it connected to, how is money moving through the network, and has the underlying behavior changed?"**

The platform therefore combines:

```text
Fraud Detection
      +
Network Intelligence
      +
Explainability
      +
Risk Propagation
      +
Adversarial Testing
      +
Drift Monitoring
      +
Audit Logging
```

---

# ✨ Key Features

- 🧠 Graph Neural Network fraud detection using **GraphSAGE**
- 🔗 Transaction-network visualization
- 🚨 Account-level risk scoring
- 🕵️ Mule / structured / outbound account identification
- 🔍 Explainable behavioral risk reasons
- 📈 Feature and model-drift monitoring using **PSI**
- 🧪 Adversarial fraud simulation and robustness testing
- 🔄 Network-based risk propagation
- 📋 Investigator-oriented fraud dashboard
- 📝 Drift-event audit logging
- ⚙️ REST APIs for fraud scoring and investigation data
- ☁️ Cloud deployment architecture
- 📱 Flutter Web responsive frontend
- 🐳 Dockerized Spring Boot backend deployment

---

# 🏗️ System Architecture

```text
                    ┌──────────────────────────┐
                    │       Flutter Web        │
                    │   Investigation Dashboard│
                    └────────────┬─────────────┘
                                 │
                                 │ REST API
                                 ▼
                    ┌──────────────────────────┐
                    │       Spring Boot        │
                    │     Application API      │
                    └────────────┬─────────────┘
                                 │
                                 │ REST
                                 ▼
                    ┌──────────────────────────┐
                    │         FastAPI          │
                    │       ML Service         │
                    └────────────┬─────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
       ┌─────────────┐    ┌─────────────┐    ┌──────────────┐
       │  GraphSAGE  │    │    Drift    │    │Explainability│
       │     GNN     │    │  Monitoring │    │   Signals    │
       └──────┬──────┘    └─────────────┘    └──────────────┘
              │
              ▼
       ┌──────────────────────┐
       │ Transaction Network  │
       │   Account Features   │
       └──────────────────────┘
```

---

# 🧩 System Components

## 1. Flutter Web Frontend

The frontend provides the investigator-facing interface.

It includes:

- Fraud intelligence dashboard
- Risk-score visualization
- Account-level investigation
- Behavioral explanations
- Transaction network visualization
- Network filters
- Drift monitoring alerts
- Audit-log information

The frontend communicates with the backend through REST APIs.

---

## 2. Spring Boot Backend

The Spring Boot application acts as the application/API layer between the frontend and the ML service.

Responsibilities include:

- Exposing REST endpoints
- Calling the ML service
- Returning fraud predictions
- Returning drift reports
- Returning transaction-network data
- Returning audit-log information
- Recording relevant drift events

The backend is independently deployable and uses Docker for production deployment.

---

## 3. FastAPI ML Service

The FastAPI service provides the machine-learning functionality.

Responsibilities include:

- Fraud prediction
- GraphSAGE inference
- Account feature processing
- Explainability
- Network data generation
- Drift analysis
- Model monitoring
- Risk-related ML outputs

The ML service is independently deployed so that the machine-learning layer can be scaled and maintained separately from the application backend.

---

# 🧠 Machine Learning Pipeline

The ML pipeline transforms transaction-level data into **account-level behavioral features**.

Important features include:

```text
in_degree
out_degree
unique_senders
unique_receivers
pass_through_ratio
velocity_hours
in_span_hours
is_passthrough
```

These features capture behavioral characteristics associated with suspicious money movement.

### Feature intuition

| Feature | What it captures |
|---|---|
| `in_degree` | Number of incoming transaction relationships |
| `out_degree` | Number of outgoing transaction relationships |
| `unique_senders` | Number of distinct sending accounts |
| `unique_receivers` | Number of distinct receiving accounts |
| `pass_through_ratio` | How much received money is subsequently passed onward |
| `velocity_hours` | Timing/velocity characteristics of transactions |
| `in_span_hours` | Time span of incoming activity |
| `is_passthrough` | Whether an account exhibits pass-through behavior |

These features are then used as node attributes within the transaction graph.

---

# 🔗 Graph Neural Network

The transaction dataset is represented as a graph.

```text
Nodes     → Accounts
Edges     → Transactions
Features  → Account behavioral statistics
```

MuleShield uses **GraphSAGE** to learn representations from both:

1. The account's own behavioral features
2. The structure and features of its neighboring accounts

Simplified architecture:

```text
Account Features
       │
       ▼
 GraphSAGE Layer
       │
       ▼
      ReLU
       │
       ▼
 GraphSAGE Layer
       │
       ▼
 Fraud Probability
       │
       ▼
  Risk Score
```

This allows the model to use both **local account behavior and transaction-network structure**.

---

# 🚨 Risk Classification

Model outputs are converted into account-level risk scores.

The dashboard groups accounts into three categories:

```text
Risk Score >= 70
        ↓
      HIGH

40 <= Risk Score < 70
        ↓
    UNCERTAIN

Risk Score < 40
        ↓
      LOW
```

These categories help investigators prioritize accounts for further analysis.

---

# 🔍 Explainability

MuleShield does not expose only a numerical prediction.

It also provides behavioral explanations associated with suspicious activity.

Examples include:

- Receiving funds from multiple senders
- Forwarding funds shortly after receiving them
- High pass-through activity
- High percentage of received funds being forwarded
- Multiple transactions occurring within a short time window
- Sudden incoming activity without corresponding outbound history

Example:

```text
Risk Score: 87.4

Why flagged:

• received money from multiple senders
• forwarded funds shortly after receiving them
• passed through a high percentage of received funds
```

This makes the system more useful for investigation than a raw probability alone.

---

# 🕸️ Transaction Network Intelligence

The network view connects accounts through their transaction relationships.

Investigators can explore:

```text
Account
   │
   ├── Incoming transactions
   │
   ├── Outgoing transactions
   │
   ├── Connected accounts
   │
   └── Risk relationships
```

The dashboard supports filtering by:

```text
ALL
HIGH RISK
MULE
STRUCTURED
OUTBOUND
```

The network view provides:

- Account relationships
- Transaction direction
- Transaction amounts
- Account risk levels
- Suspicious clusters
- Connected-account context
- Selected-account investigation context

This allows investigators to move from:

```text
"Which account is suspicious?"
```

to:

```text
"Which network of accounts is involved?"
```

---

# 🔄 Risk Propagation

Fraudulent behavior can extend through transaction networks.

MuleShield includes network-based risk propagation logic that considers relationships between suspicious accounts and connected accounts.

Conceptually:

```text
High-Risk Account
       │
       ▼
Connected Account
       │
       ▼
Network Context
       │
       ▼
Additional Risk Signal
```

Risk propagation provides an additional layer of network intelligence beyond the original GraphSAGE prediction.

It is intended to help surface suspicious relationships that may not be obvious from an isolated account-level score.

---

# 📈 Model Drift Monitoring

Fraud patterns can change over time.

A model that performs well on historical behavior may encounter a different distribution of transaction activity later.

MuleShield therefore includes **model and feature drift monitoring**.

The platform uses the **Population Stability Index (PSI)** to compare baseline and incoming distributions.

Example monitoring output:

```text
Overall status: MAJOR_SHIFT

Risk-score PSI: 0.045

Most-drifted feature:
is_passthrough
PSI: 0.583
```

A significant feature shift can indicate that new transaction behavior has entered the system.

The system also monitors explanation-pattern divergence using **Jensen-Shannon divergence (JS divergence)**.

---

# 🧪 Adversarial Robustness Testing

Fraudsters may intentionally modify their behavior to appear less suspicious.

MuleShield therefore includes adversarial transaction simulation to evaluate whether the detection pipeline remains robust against evasion-oriented behavior.

Workflow:

```text
Normal Data
     │
     ▼
Adversarial Simulation
     │
     ▼
Feature Generation
     │
     ▼
Model Scoring
     │
     ▼
Robustness Evaluation
```

This provides an additional evaluation layer beyond standard model testing.

The objective is to test the system under deliberately altered fraud-like behavior rather than evaluating only clean historical patterns.

---

# 📝 Audit & Monitoring

MuleShield combines:

```text
Fraud Detection
       +
Drift Detection
       +
Audit Logging
```

When significant drift is detected, the backend can record the event.

This creates an audit trail that can help investigators or engineers determine:

- When a drift event occurred
- What type of drift was observed
- Which features were affected
- Whether further investigation is required
- Whether model retraining should be considered

---

# 🔄 End-to-End Investigation Flow

A typical investigation can follow this workflow:

```text
                ┌─────────────────┐
                │  Fraud Report   │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Identify Risky  │
                │    Accounts     │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Review Reasons  │
                │   for Risk      │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Open Network    │
                │    View         │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Trace Connected  │
                │    Accounts     │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Review Network  │
                │ Risk Propagation│
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Check Model/Data│
                │     Drift       │
                └─────────────────┘
```

---

# 🛠️ Technology Stack

## Frontend

- Flutter
- Dart
- Material UI
- GraphView
- REST API integration

## Backend

- Java
- Spring Boot
- Spring Web
- Maven
- REST APIs

## Machine Learning

- Python
- FastAPI
- PyTorch
- PyTorch Geometric
- GraphSAGE
- Pandas
- NumPy
- Scikit-learn
- SciPy

## Deployment

- GitHub
- Render
- Docker
- Flutter Web

---

# 📡 API Endpoints

## Fraud Report

```http
GET /api/fraud-report
```

Returns account-level fraud predictions and behavioral explanations.

---

## Drift Report

```http
GET /api/drift-report
```

Returns:

- Overall drift status
- Risk-score PSI
- Feature PSI
- Explanation divergence
- Drift alerts
- Summary information

Example:

```json
{
  "overall_status": "major_shift",
  "score_psi": 0.04504380869345427,
  "feature_psi": {
    "in_degree": 0.05194713329452505,
    "out_degree": 0.06552895270702973,
    "unique_senders": 0.04489214081788862,
    "unique_receivers": 0.08457825725441973,
    "pass_through_ratio": 0.041574160574492786,
    "velocity_hours": 0.05921611504823506,
    "in_span_hours": 0.04637897959173011,
    "is_passthrough": 0.5830799852834774
  },
  "explanation_js_divergence": 0.0057590339522558456
}
```

A high PSI value on an individual feature can trigger a drift alert.

---

## Transaction Network

```http
GET /api/network
```

Returns network information including:

- Network nodes
- Account IDs
- Risk scores
- Risk levels
- Account types
- Transaction edges
- Transaction amounts

---

## Audit Log

```http
GET /api/audit-log
```

Returns recorded drift-related audit events.

---

# 📁 Project Structure

```text
mule-fraud-detection/
│
├── backend/
│   ├── src/
│   │   └── main/
│   │       ├── java/
│   │       │   └── com/
│   │       │       └── fraudplatform/
│   │       │           └── backend/
│   │       └── resources/
│   ├── pom.xml
│   ├── mvnw
│   └── Dockerfile
│
├── frontend/
│   ├── lib/
│   │   ├── models/
│   │   ├── screens/
│   │   ├── services/
│   │   └── widgets/
│   ├── pubspec.yaml
│   └── test/
│
├── fastapi_app.py
├── drift_monitor.py
├── risk_propagation.py
├── explain.py
│
├── train_baseline.py
├── train_gnn.py
├── retrain_gnn_v2.py
│
├── build_features.py
├── build_drift_features.py
├── build_adversarial_features.py
├── add_topology_feature.py
│
├── simulate_data.py
├── simulate_drift_batch.py
├── simulate_adversarial_batch.py
│
├── run_drift_check.py
├── run_adversarial_drift_check.py
│
├── score_current_batch.py
├── score_adversarial_batch.py
├── score_adversarial_with_v2.py
│
├── combine_training_data.py
├── requirements.txt
├── Procfile
├── .gitignore
└── README.md
```

Generated datasets and model artifacts are intentionally excluded from version control where appropriate through `.gitignore`.

---

# ⚙️ Local Setup

## Prerequisites

Install:

- Python 3.x
- Java 17+
- Maven
- Flutter SDK
- Git

---

# 🤖 Run the ML Service

Create and activate a virtual environment:

### Windows

```cmd
python -m venv venv
venv\Scripts\activate
```

Install dependencies:

```cmd
pip install -r requirements.txt
```

Run the FastAPI service:

```cmd
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000
```

The ML service will be available at:

```text
http://localhost:8000
```

---

# ☕ Run the Spring Boot Backend

Navigate to the backend:

```cmd
cd backend
```

Build the application:

```cmd
mvnw clean package -DskipTests
```

Run the generated JAR:

```cmd
java -jar target/backend-0.0.1-SNAPSHOT.jar
```

The backend runs on:

```text
http://localhost:8080
```

---

# 📱 Run the Flutter Frontend

Navigate to the frontend:

```cmd
cd frontend
```

Install Flutter dependencies:

```cmd
flutter pub get
```

Run locally:

```cmd
flutter run -d chrome
```

---

# 🔌 API Configuration

The Flutter frontend supports configurable API endpoints using:

```text
API_BASE_URL
```

Example:

```cmd
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8080
```

For a deployed backend:

```cmd
flutter run -d chrome --dart-define=API_BASE_URL=https://your-backend-url
```

This keeps deployment-specific URLs outside the application source code.

---

# 🐳 Docker Deployment

The Spring Boot backend includes a Dockerfile based on Eclipse Temurin Java 17.

```dockerfile
FROM eclipse-temurin:17-jdk
WORKDIR /app
COPY . .
RUN chmod +x mvnw
RUN ./mvnw clean package -DskipTests
EXPOSE 8080
CMD ["java", "-jar", "target/backend-0.0.1-SNAPSHOT.jar"]
```

The application listens on port `8080`.

---

# ☁️ Deployment Architecture

The project is designed as independently deployable services:

```text
                    Internet
                       │
                       ▼
              ┌─────────────────┐
              │  Flutter Web UI  │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Spring Boot API │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ FastAPI ML API  │
              └─────────────────┘
```

The ML service is deployed independently from the Spring Boot application.

This separation allows:

- Independent service deployment
- Clear API boundaries
- Easier ML iteration
- Independent scaling
- Cleaner frontend/backend architecture

---

# 🔐 Configuration

Deployment-specific configuration is handled using environment variables where appropriate.

Example:

```text
ML_SERVICE_URL=https://mule-fraud-ml.onrender.com
```

The frontend similarly supports:

```text
API_BASE_URL
```

This avoids hard-coding environment-specific service locations into application logic.

---

# 🧪 Model Evaluation & Robustness

The project includes multiple layers of evaluation:

```text
                 Model Evaluation
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   Normal Data   Adversarial Data   Drift Data
        │              │              │
        ▼              ▼              ▼
    Prediction     Robustness       Distribution
     Testing        Testing           Analysis
```

This is intended to provide a broader assessment of the fraud-detection pipeline than a single accuracy metric.

---

# 📊 Example Drift Finding

One observed monitoring scenario produced:

```text
Overall status: MAJOR_SHIFT

Risk-score PSI: 0.045

is_passthrough PSI: 0.583

Explanation JS divergence: 0.006
```

The key signal was the substantial distribution shift in:

```text
is_passthrough
```

while the overall risk-score distribution remained comparatively stable.

This illustrates why monitoring individual input features can reveal changes that may not immediately appear in the final model-score distribution.

---

# 🎯 Why This Project Matters

Mule fraud is fundamentally a **network problem**.

A single suspicious transaction may not provide enough evidence.

However:

```text
Multiple Senders
       │
       ▼
  Mule Account
       │
       ├──────────► Receiver A
       │
       ├──────────► Receiver B
       │
       └──────────► Receiver C
```

can reveal a much stronger behavioral pattern.

MuleShield therefore combines:

```text
Account Behavior
       +
Graph Structure
       +
Transaction Relationships
       +
Explainability
       +
Risk Propagation
       +
Continuous Monitoring
```

to create an investigation-oriented fraud intelligence system.

---

# 🚀 Future Improvements

Potential future extensions include:

- Real-time transaction-stream processing
- Larger production-scale transaction graphs
- Real-time GraphSAGE inference
- Automated model retraining pipelines
- Stronger adversarial evaluation
- Investigator feedback loops
- Case-management workflows
- Historical investigation replay
- Advanced graph analytics
- Model performance monitoring
- Human-in-the-loop fraud review
- Production database integration

---

# 🏆 Project Summary

MuleShield is designed as more than a machine-learning classifier.

It combines:

```text
                 ┌─────────────────────┐
                 │   Fraud Detection   │
                 └──────────┬──────────┘
                            │
                 ┌──────────▼──────────┐
                 │ Network Intelligence│
                 └──────────┬──────────┘
                            │
                 ┌──────────▼──────────┐
                 │   Explainability    │
                 └──────────┬──────────┘
                            │
                 ┌──────────▼──────────┐
                 │  Risk Propagation   │
                 └──────────┬──────────┘
                            │
                 ┌──────────▼──────────┐
                 │ Adversarial Testing │
                 └──────────┬──────────┘
                            │
                 ┌──────────▼──────────┐
                 │  Drift Monitoring   │
                 └──────────┬──────────┘
                            │
                 ┌──────────▼──────────┐
                 │ Investigator UI     │
                 └─────────────────────┘
```

The central idea is simple:

> **Don't just detect the suspicious account. Understand the network, explain the behavior, and monitor how the fraud pattern evolves.**

---

# 📌 Disclaimer

This project is a technical demonstration and research-oriented fraud intelligence platform.

It is not intended to make autonomous real-world financial decisions without appropriate validation, governance, human review, regulatory controls, and production-grade security.

---

# 👨‍💻 Project

**MuleShield — AI-Powered Mule Fraud Detection & Network Intelligence Platform**

Built with:

**Flutter • Java • Spring Boot • Python • FastAPI • PyTorch • PyTorch Geometric • GraphSAGE • Docker • Render**