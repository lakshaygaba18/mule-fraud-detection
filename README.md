\# 🕵️ Mule Fraud Detection \& Network Intelligence Platform



An end-to-end fraud detection platform designed to identify suspicious mule accounts by combining \*\*machine learning, transaction-network analysis, risk propagation, explainability, adversarial testing, and model-drift monitoring\*\*.



The platform provides an investigator-oriented dashboard where suspicious accounts, transaction relationships, risk scores, behavioral explanations, and data drift can be explored in one place.



\---



\## 🚀 Project Overview



The platform consists of three major components:



\- \*\*Flutter Web Frontend\*\* — investigator dashboard and transaction-network visualization

\- \*\*Spring Boot Backend\*\* — application/API layer

\- \*\*FastAPI ML Service\*\* — fraud scoring, GraphSAGE inference, explanations, and drift monitoring



The architecture separates the application layer from the machine-learning service, allowing the ML service to operate independently.



\---



\## 🎯 Problem Statement



Traditional fraud detection systems often evaluate transactions or accounts independently.



Mule accounts, however, frequently operate as part of a \*\*transaction network\*\*.



```text

Account A

&#x20;   │

&#x20;   ▼

Mule Account

&#x20;   │

&#x20;   ├──────────► Account C

&#x20;   │

&#x20;   └──────────► Account D



A suspicious account may therefore be difficult to identify using only individual transaction features.



This project combines account-level behavioral features with graph-based learning to identify suspicious patterns and provide investigators with network-level context.



✨ Key Features

🧠 Graph Neural Network fraud detection using GraphSAGE

🔗 Transaction-network visualization

🚨 Account-level risk scoring

🕵️ Mule / structured / outbound account identification

🔍 Explainable behavioral risk reasons

📈 Feature and risk-score drift monitoring using PSI

🧪 Adversarial fraud simulation and robustness testing

🔄 Network-based risk propagation

📋 Investigator-oriented fraud dashboard

📝 Drift-event audit logging

⚙️ REST APIs for fraud scoring and investigation data

☁️ Cloud deployment architecture

📱 Flutter Web responsive frontend

🏗️ System Architecture

&#x20;                   ┌──────────────────────┐

&#x20;                   │     Flutter Web      │

&#x20;                   │  Investigation UI    │

&#x20;                   └──────────┬───────────┘

&#x20;                              │

&#x20;                              │ REST API

&#x20;                              ▼

&#x20;                   ┌──────────────────────┐

&#x20;                   │    Spring Boot       │

&#x20;                   │    Application API   │

&#x20;                   └──────────┬───────────┘

&#x20;                              │

&#x20;                              │ REST

&#x20;                              ▼

&#x20;                   ┌──────────────────────┐

&#x20;                   │      FastAPI         │

&#x20;                   │     ML Service       │

&#x20;                   └──────────┬───────────┘

&#x20;                              │

&#x20;            ┌─────────────────┼─────────────────┐

&#x20;            │                 │                 │

&#x20;            ▼                 ▼                 ▼

&#x20;     ┌────────────┐    ┌────────────┐    ┌────────────┐

&#x20;     │ GraphSAGE  │    │   Drift    │    │Explainable │

&#x20;     │    GNN     │    │ Monitoring │    │  Signals   │

&#x20;     └─────┬──────┘    └────────────┘    └────────────┘

&#x20;           │

&#x20;           ▼

&#x20;  ┌─────────────────────┐

&#x20;  │ Transaction Network │

&#x20;  │  Account Features   │

&#x20;  └─────────────────────┘

🧠 Machine Learning Pipeline



The ML pipeline transforms transaction-level information into account-level behavioral features.



Important features include:



in\_degree

out\_degree

unique\_senders

unique\_receivers

pass\_through\_ratio

velocity\_hours

in\_span\_hours

is\_passthrough



These features capture behavioral characteristics associated with suspicious money movement.



🔗 Graph Neural Network



The transaction dataset is represented as a graph:



Nodes       → Accounts

Edges       → Transactions

Features    → Account behavioral statistics



The project uses GraphSAGE to learn representations from:



An account's own behavioral features

The structure of its surrounding transaction network



Simplified architecture:



Account Features

&#x20;     │

&#x20;     ▼

&#x20;GraphSAGE Layer

&#x20;     │

&#x20;     ▼

&#x20;   ReLU

&#x20;     │

&#x20;     ▼

&#x20;GraphSAGE Layer

&#x20;     │

&#x20;     ▼

&#x20;Fraud Probability



The resulting probability is converted into an account-level risk score.



🚨 Risk Classification



Accounts are classified using their model-generated risk score.



Risk Score >= 70

&#x20;       ↓

&#x20;     HIGH



40 <= Risk Score < 70

&#x20;       ↓

&#x20;   UNCERTAIN



Risk Score < 40

&#x20;       ↓

&#x20;     LOW



These categories help investigators prioritize suspicious accounts.



🔍 Explainability



The system provides behavioral explanations alongside numerical risk scores.



Examples include:



Receiving funds from multiple senders

Forwarding funds shortly after receiving them

Passing through a high percentage of received funds

Receiving multiple payments within a short time window

Sudden incoming activity with no outbound history



Example:



Risk Score: 87.4



Why flagged:



• received money from multiple senders

• forwarded funds shortly after receiving them

• passed through a high percentage of received funds



This makes the output more useful for investigation than a raw ML probability alone.



🕸️ Transaction Network Intelligence



The network view connects suspicious accounts with their transaction neighbors.



The dashboard supports filtering by:



ALL

HIGH RISK

MULE

STRUCTURED

OUTBOUND



The graph provides:



Account relationships

Transaction direction

Transaction amounts

Risk levels

Suspicious account clusters

Connected-account context



This allows investigators to move from:



"Which account is suspicious?"



to:



"Which network of accounts is involved?"

🔄 Risk Propagation



Fraudulent behavior can propagate through transaction networks.



The project includes network-based risk propagation logic that considers relationships between suspicious accounts and connected accounts.



This provides an additional layer of network intelligence beyond the original model prediction.



📈 Model Drift Monitoring



The platform compares baseline behavior with the current data batch.



Population Stability Index (PSI) is used to monitor changes in feature distributions.



Example monitoring output:



Overall status: MAJOR\_SHIFT



Risk-score PSI: 0.045



Most-drifted feature:

is\_passthrough

PSI: 0.583



A significant shift in a feature can indicate that transaction behavior has changed.



The system exposes drift information through a dedicated monitoring API and displays relevant alerts in the dashboard.



The drift monitoring layer can help identify situations where further investigation or model retraining may be required.



🧪 Adversarial Robustness Testing



The project includes adversarial transaction simulation to evaluate model robustness against fraud patterns designed to appear less suspicious.



Workflow:



Normal Data

&#x20;   │

&#x20;   ▼

Adversarial Simulation

&#x20;   │

&#x20;   ▼

Feature Generation

&#x20;   │

&#x20;   ▼

Model Scoring

&#x20;   │

&#x20;   ▼

Robustness Evaluation



This provides an additional evaluation layer beyond standard model testing.



📝 Audit \& Monitoring



The platform combines:



Fraud Detection

&#x20;      +

Drift Detection

&#x20;      +

Audit Logging



When significant drift is detected, the backend records the event so investigators can identify situations where further analysis or model retraining may be required.



🛠️ Technology Stack

Frontend

Flutter

Dart

Material UI

GraphView

REST API integration

Backend

Java

Spring Boot

Maven

REST APIs

Machine Learning

Python

FastAPI

PyTorch

PyTorch Geometric

GraphSAGE

Pandas

NumPy

Scikit-learn

SciPy

Deployment

GitHub

Render

Docker

Flutter Web

📡 API Endpoints

Fraud Report

GET /api/fraud-report



Returns account-level fraud predictions and behavioral explanations.



Drift Report

GET /api/drift-report



Returns:



Overall drift status

Risk-score PSI

Feature PSI

Explanation divergence

Drift alerts

Summary

Transaction Network

GET /api/network



Returns:



Network nodes

Account risk levels

Risk scores

Transaction edges

Transaction amounts

Audit Log

GET /api/audit-log



Returns recorded drift-related audit events.



📁 Project Structure

mule-fraud-detection/

│

├── backend/

│   ├── src/

│   │   └── main/

│   │       ├── java/

│   │       └── resources/

│   ├── pom.xml

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

├── fastapi\_app.py

├── drift\_monitor.py

├── risk\_propagation.py

│

├── combine\_training\_data.py

├── retrain\_gnn\_v2.py

├── score\_adversarial\_with\_v2.py

│

├── requirements.txt

├── Procfile

└── README.md

☁️ Deployment



The application is designed around independently deployable services:



Flutter Web

&#x20;    │

&#x20;    ▼

Spring Boot Backend

&#x20;    │

&#x20;    ▼

FastAPI ML Service



The ML service is deployed separately from the Spring Boot application.



The frontend communicates with the configured backend API through an environment-specific API base URL.



This separation allows the frontend, backend, and ML inference service to be deployed and scaled independently.



🔐 Configuration



The frontend API endpoint is configurable using:



API\_BASE\_URL



The backend ML service endpoint is configured using:



ML\_SERVICE\_URL



This keeps deployment-specific URLs outside the application logic.



🎓 Project Goals



This project demonstrates the practical integration of:



Machine Learning

Graph Neural Networks

Fraud Detection

Network Analysis

Explainable AI

Adversarial Testing

Data Drift Monitoring

REST API Architecture

Spring Boot

FastAPI

Flutter

Cloud Deployment



Rather than treating fraud detection as only a classification problem, the platform approaches it as an investigation and network-intelligence problem.



⚠️ Disclaimer



This project is intended for educational, research, and portfolio demonstration purposes.



The transaction data and fraud patterns used in the project are simulated or project-generated and should not be treated as real financial intelligence.



👨‍💻 Author



Lakshay Gaba



BTech Student | Machine Learning | Backend Development | Flutter



⭐ If you find this project interesting



Feel free to explore the repository, review the architecture, and experiment with the fraud-detection and network-analysis components.

